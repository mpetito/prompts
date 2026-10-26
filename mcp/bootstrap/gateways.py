"""Run one shared Docker MCP gateway per profile at logon, so every client session connects to it instead of starting
gateways of its own.
  python3 mcp/bootstrap/gateways.py install [--what-if]
  python3 mcp/bootstrap/gateways.py uninstall [--what-if]
  python3 mcp/bootstrap/gateways.py run <profile>
install creates a random token, MCP_GATEWAY_AUTH_TOKEN, only when there is none, then has the user's service manager
run this script's run for each profile from logon:
- Windows: the token is a user environment variable; each profile gets a hidden per-user logon task, run under
  pythonw.
- Linux: the token is in mcp_common.token_file(), which a line added to ~/.profile exports to login shells; each
  profile is an instance of a systemd user unit.
Clients started before the token was stored must be restarted (on Linux, from a new login) to read it. uninstall stops
and removes the services, with their gateways, and the token. run waits for the Docker engine, then runs the
profile's gateway on its loopback port, again whenever it exits; its output goes to log_path(profile). A failed command stops install or uninstall
(exit 1).
"""
import os
import secrets
import shlex
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import mcp_common as mcp
from mcp_common import sc

TASK = "Docker MCP gateway {profile}"
UNIT = "docker-mcp-gateway@{profile}.service"
PORTS = {profile: port for _, profile, port in mcp.GATEWAYS}
RETRY_SECONDS = 10
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


def powershell(command, input=None):
    """Run command in Windows PowerShell, input on its stdin, so a secret is never on a command line. Fail names the
    command, never the input."""
    r = sc.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], input=input)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise sc.Fail(f"Command failed (exit {r.returncode}): powershell {command}")


def task_xml(profile):
    """The logon task for profile: hidden, for this user only, with no time limit or battery stop, and restarted
    every minute should the runner itself fail."""
    user = f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}"
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.exists():
        raise sc.Fail(f"{pythonw} is missing; the task needs it to run without a window.")
    arguments = f'"{Path(__file__).absolute()}" run {profile}'
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Shared Docker MCP gateway for the {escape(profile)} profile.</Description>
    </RegistrationInfo>
  <Triggers><LogonTrigger><UserId>{escape(user)}</UserId></LogonTrigger></Triggers>
  <Principals><Principal id="Author"><UserId>{escape(user)}</UserId><LogonType>InteractiveToken</LogonType>
    <RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <Hidden>true</Hidden>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure><Interval>PT1M</Interval><Count>255</Count></RestartOnFailure>
  </Settings>
  <Actions Context="Author"><Exec><Command>{escape(str(pythonw))}</Command>
    <Arguments>{escape(arguments)}</Arguments></Exec></Actions>
</Task>
"""


def install_tasks(args):
    what_if = args.what_if
    if not mcp.gateway_token() and sc.should(what_if, mcp.TOKEN_VARIABLE,
                                             "Store a new gateway token in the user environment"):
        powershell(f"[Environment]::SetEnvironmentVariable('{mcp.TOKEN_VARIABLE}', [Console]::In.ReadToEnd(), 'User')",
                   secrets.token_urlsafe(32))
    for _, profile, port in mcp.GATEWAYS:
        name = TASK.format(profile=profile)
        if sc.should(what_if, name, f"Register and start the logon task for the gateway on port {port}"):
            powershell(f"Register-ScheduledTask -TaskName '{name}' -Xml ([Console]::In.ReadToEnd()) -Force | Out-Null;"
                       f" Start-ScheduledTask -TaskName '{name}'", task_xml(profile))
    if not what_if:
        print("Gateways started. Restart clients opened before the token was set; check with"
              " 'python3 mcp/bootstrap/verify.py'.")


def uninstall_tasks(args):
    what_if = args.what_if
    for _, profile, _ in mcp.GATEWAYS:
        name = TASK.format(profile=profile)
        if sc.should(what_if, name, "Stop and remove the logon task and its gateway"):
            powershell(f"$task = Get-ScheduledTask -TaskName '{name}' -ErrorAction SilentlyContinue;"
                       " if ($task) { $task | Stop-ScheduledTask; $task | Unregister-ScheduledTask -Confirm:$false }")
    if sc.should(what_if, mcp.TOKEN_VARIABLE, "Remove the gateway token from the user environment"):
        powershell(f"[Environment]::SetEnvironmentVariable('{mcp.TOKEN_VARIABLE}', $null, 'User')")


def systemctl(*args):
    sc.run_checked(["systemctl", "--user", *args], show=False)


def unit_path():
    return os.path.join(sc.setup_paths().config_root, "systemd", "user", UNIT.format(profile=""))


def unit_text():
    """The systemd user template unit, whose instance (%i) is a profile: started with the user's service manager,
    restarted should the runner itself fail. Stopping it stops the gateway too: systemd stops the unit's whole control
    group."""
    # Quoted for a path with spaces; % doubled, since systemd reads it as a specifier.
    command = " ".join(f'"{part}"'.replace("%", "%%") for part in (sys.executable, Path(__file__).absolute()))
    return f"""[Unit]
Description=Shared Docker MCP gateway for the %i profile

[Service]
ExecStart={command} run %i
Restart=always
RestartSec={RETRY_SECONDS}

[Install]
WantedBy=default.target
"""


def profile_line():
    """The ~/.profile line that exports the token to login shells, and to the desktop sessions started from them."""
    path = shlex.quote(mcp.token_file())
    return f"if [ -f {path} ]; then . {path}; export {mcp.TOKEN_VARIABLE}; fi\n"


def install_units(args):
    what_if = args.what_if
    paths = sc.setup_paths()
    token_file, profile = mcp.token_file(), os.path.join(paths.user_root, ".profile")
    if not os.path.exists(token_file) and sc.should(what_if, token_file, "Store a new gateway token"):
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        # Created owner-only, so the token is never readable by others.
        with open(os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as f:
            f.write(f"{mcp.TOKEN_VARIABLE}={secrets.token_urlsafe(32)}\n")
    text = Path(profile).read_text(encoding="utf-8") if os.path.exists(profile) else ""
    if profile_line() not in text and sc.should(what_if, profile, "Export the gateway token to login shells"):
        with open(profile, "a", encoding="utf-8") as f:
            f.write(("\n" if text and not text.endswith("\n") else "") + profile_line())
    unit = unit_path()
    if sc.should(what_if, unit, "Write the gateways' systemd user unit"):
        os.makedirs(os.path.dirname(unit), exist_ok=True)
        Path(unit).write_text(unit_text(), encoding="utf-8")
        systemctl("daemon-reload")
    for _, profile_name, port in mcp.GATEWAYS:
        name = UNIT.format(profile=profile_name)
        if sc.should(what_if, name, f"Enable and start the gateway on port {port}"):
            systemctl("enable", "--now", name)
    if not what_if:
        print("Gateways started. Restart clients from a new login, which exports the token; check with"
              " 'python3 mcp/bootstrap/verify.py'.")


def uninstall_units(args):
    what_if = args.what_if
    paths = sc.setup_paths()
    unit = unit_path()
    if os.path.exists(unit):
        for _, profile_name, _ in mcp.GATEWAYS:
            name = UNIT.format(profile=profile_name)
            if sc.should(what_if, name, "Stop and disable the gateway"):
                systemctl("disable", "--now", name)
        if sc.should(what_if, unit, "Remove the gateways' systemd user unit"):
            os.remove(unit)
            systemctl("daemon-reload")
    profile = os.path.join(paths.user_root, ".profile")
    text = Path(profile).read_text(encoding="utf-8") if os.path.exists(profile) else ""
    if profile_line() in text and sc.should(what_if, profile, "Stop exporting the gateway token to login shells"):
        Path(profile).write_text(text.replace(profile_line(), ""), encoding="utf-8")
    token_file = mcp.token_file()
    if os.path.exists(token_file) and sc.should(what_if, token_file, "Remove the gateway token"):
        os.remove(token_file)


# The service manager that runs the gateways at logon, by os.name: its install and uninstall commands.
SERVICE_MANAGERS = {"nt": (install_tasks, uninstall_tasks), "posix": (install_units, uninstall_units)}


def die_with_this_process():
    """Put this process in a job that kills everything in it when its last handle closes, at this process's exit.
    The gateway, docker.exe and the docker-mcp.exe it starts, inherits the job, so stopping the task, which ends only
    the runner, stops the gateway too."""
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", ctypes.c_uint64 * 6),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    job = kernel32.CreateJobObjectW(None, None)
    info = Extended()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not job or not kernel32.SetInformationJobObject(wintypes.HANDLE(job), JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                                                       ctypes.byref(info), ctypes.sizeof(info)) or \
            not kernel32.AssignProcessToJobObject(wintypes.HANDLE(job), wintypes.HANDLE(kernel32.GetCurrentProcess())):
        raise ctypes.WinError(ctypes.get_last_error())
    # The handle stays open, deliberately, for the life of this process.


def log_path(profile):
    """The gateway's log, which only this user can read: Windows' temporary folder is the user's own, but elsewhere it
    is usually the shared /tmp, so the log goes beside the token."""
    folder = tempfile.gettempdir() if os.name == "nt" else os.path.dirname(mcp.token_file())
    return os.path.join(folder, f"mcp-gateway-{profile}.log")


def run(args):
    """Serve the profile's gateway until this process is stopped: wait for the Docker engine, run the gateway, and
    after it exits wait and start again. Fail when the token is unset; under the service manager, that shows only as
    its last run result or in its journal, since pythonw has no stderr."""
    # The stored value, which a process started before install does not have in its environment.
    token = mcp.gateway_token()
    if not token:
        raise sc.Fail(f"{mcp.TOKEN_VARIABLE} is unset. Run 'python3 mcp/bootstrap/gateways.py install'.")
    os.environ[mcp.TOKEN_VARIABLE] = token
    if os.name == "nt":
        die_with_this_process()
    log = log_path(args.profile)
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8", buffering=1) as log:
        while True:
            # A starting engine can hold docker info; the timeout turns that into one more wait.
            if not sc.run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=60).returncode:
                code = sc.run(mcp.gateway_command(args.profile, PORTS[args.profile]), output=log).returncode
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} gateway exited with code {code}", file=log)
            time.sleep(RETRY_SECONDS)


def main(argv):
    parser = sc.Parser(prog="gateways.py", description="Run the shared Docker MCP gateways at logon.")
    commands = parser.add_subparsers(required=True)
    for name, handler in zip(("install", "uninstall"), SERVICE_MANAGERS[os.name]):
        command = commands.add_parser(name)
        command.add_argument("--what-if", action="store_true")
        command.set_defaults(handler=handler)
    command = commands.add_parser("run")
    command.add_argument("profile", choices=PORTS)
    command.set_defaults(handler=run)
    args = parser.parse_args(argv)
    args.handler(args)
    return 0


if __name__ == "__main__":
    sc.entry(main)
