// Claude Code status line. Reads the session JSON on stdin, prints one line.
// Payload fields used here: cwd, workspace.*, model.*, effort.level, context_window.*, worktree.branch.
// (The payload also carries session_name, vim, pr, cost, rate_limits -- vim and pr are native.)
const { execFileSync } = require('child_process');

// Claude Code spawns us with a stdin pipe, and also spawns MCP servers via cmd.exe
// that inherit open handles. A grandchild holding the write end means we never see
// EOF once Claude exits, so waiting on 'end' alone leaks a wedged process per session.
// Render on whichever comes first -- EOF or the deadline -- and always exit explicitly.
const DEADLINE_MS = 2000;

const chunks = [];
let done = false;

// Nerd Font glyphs -- these require a Nerd Font (Cascadia Code NF is installed and set
// as the Windows Terminal face). Written as escapes so this file stays pure ASCII.
// Every glyph below was checked against the font's cmap. U+2387 (the old branch mark),
// U+2717 and U+2718 (ballot X) are NOT in Cascadia Code NF -- do not reach for them.
const ICON = {
  dir:      '\uF07C',    // fa folder-open
  repo:     '\uF401',    // octicon repo
  branch:   '\uE725',    // devicon git-branch
  clean:    '\u2713',    // check -- working tree clean
  dirty:    '\u25CF',    // filled circle -- uncommitted changes
  conflict: '\uF071',    // fa warning -- unmerged paths
  model:    '\u{F06A9}', // md robot
  effort:   '\uF0E7',    // fa bolt
  context:  '\uF437',    // octicon graph
  sep:      '\u2502',    // box-drawing vertical bar
};

const paint = (code, s) => `\x1b[${code}m${s}\x1b[0m`;

// Envative branches are `users/<user>/<work-item>-<description>`, which runs to ~60
// characters and wraps the status line. Drop the owner prefix -- it is always this
// user -- and cap what remains.
const BRANCH_MAX = 32;
const shortBranch = (b) => {
  const s = b.replace(/^users\/[^/]+\//, '');
  return s.length > BRANCH_MAX ? s.slice(0, BRANCH_MAX - 1) + '\u2026' : s;
};

// Context usage as a bare percentage. The colour carries the urgency, so the ten-cell
// bar this replaces was costing width without adding information.
const contextPct = (pct) => {
  const clamped = Math.max(0, Math.min(100, pct));
  const colour = clamped >= 80 ? '31' : clamped >= 60 ? '33' : '32';  // red / yellow / green
  return paint(colour, `${ICON.context} ${Math.round(clamped)}%`);
};

// `git status --porcelain=v1 --branch` returns the branch and the working-tree state
// together, so the status indicator costs no extra subprocess over the `rev-parse` it
// replaces. Porcelain v1 is a stable, documented format safe to parse.
const gitInfo = (cwd) => {
  try {
    const out = execFileSync('git', ['-C', cwd, 'status', '--porcelain=v1', '--branch'],
      { encoding: 'utf8', timeout: 1000, stdio: ['ignore', 'pipe', 'ignore'] });
    const lines = out.split('\n');

    // Header looks like "## main...origin/main [ahead 1]", "## main", or
    // "## HEAD (no branch)" when detached. Branch names may contain dots, so split
    // on the literal "..." upstream separator rather than on any dot.
    let branch = '';
    const head = lines[0] || '';
    if (head.startsWith('## ') && !head.startsWith('## HEAD (no branch)')) {
      branch = head.slice(3).split('...')[0]
        .replace(/^No commits yet on /, '')
        .replace(/\s+\[.*\]$/, '')
        .trim();
    }

    // One porcelain line is one file. Count lines, not index/worktree flags: a file
    // that is staged and then modified again reports "MM" and must still count once.
    let changed = 0, conflict = 0;
    for (const line of lines.slice(1)) {
      if (!line) continue;
      const x = line[0], y = line[1];
      // Unmerged: either side U, or the AA / DD both-added / both-deleted pairs.
      if (x === 'U' || y === 'U' || (x === 'A' && y === 'A') || (x === 'D' && y === 'D')) conflict++;
      else changed++;   // includes "??" untracked, which is also one line per file
    }
    return { branch, changed, conflict };
  } catch { return null; }
};

// One glyph, coloured: red on conflicts, yellow with a count when there is anything
// uncommitted, green when the tree is clean.
const gitBadge = (g) => {
  if (!g) return '';
  if (g.conflict) return paint('31', `${ICON.conflict} ${g.conflict}`);
  return g.changed ? paint('33', `${ICON.dirty} ${g.changed}`) : paint('32', ICON.clean);
};

const render = () => {
  let d = {};
  try { d = JSON.parse(chunks.join('')); } catch {}

  const cwd = d.workspace?.current_dir || d.cwd || process.cwd();

  const home = process.env.USERPROFILE || process.env.HOME || '';
  let dir = cwd;
  if (home && dir.toLowerCase().startsWith(home.toLowerCase())) dir = '~' + dir.slice(home.length);
  dir = dir.split('\\').join('/');

  // The payload carries repo identity (host/owner/name) but never the checked-out
  // branch outside --worktree sessions, so ask git directly.
  const git = gitInfo(cwd);
  const branch = d.worktree?.branch || git?.branch || '';

  // session_name is deliberately omitted -- the TUI already shows it by the input box.
  // vim.mode and pr.number are omitted too: Claude Code renders both natively (the
  // built-in "-- INSERT --" text and the footer PR badge, which pr.number mirrors).
  const parts = [paint('36', `${ICON.dir} ${dir}`)];                       // cyan cwd

  const repo = d.workspace?.repo;
  if (repo?.name) parts.push(paint('34', `${ICON.repo} ${repo.owner}/${repo.name}`));  // blue repo

  if (branch && branch !== 'HEAD') {
    const badge = gitBadge(git);                                                     // magenta branch
    parts.push(paint('35', `${ICON.branch} ${shortBranch(branch)}`) + (badge ? ` ${badge}` : ''));
  }

  // Reasoning effort rides with the model rather than taking its own segment: it is a
  // property of the model, and the line is already wide. Absent when the model has no
  // effort parameter; `xhigh` also covers Ultracode, which is not a distinct level.
  const model = d.model?.display_name;
  const effort = d.effort?.level;
  if (model || effort) {
    const head = model ? paint('33', `${ICON.model} ${model}`) : '';        // yellow model
    const gap = model && effort ? ' ' : '';
    const tail = effort ? paint('90', `${gap}${ICON.effort} ${effort}`) : ''; // dim effort
    parts.push(head + tail);
  }

  const pct = d.context_window?.used_percentage;
  if (typeof pct === 'number') parts.push(contextPct(pct));

  return parts.join(paint('90', ` ${ICON.sep} `));
};

const finish = () => {
  if (done) return;
  done = true;
  clearTimeout(watchdog);
  // Release the stdin handle so a still-open pipe can't hold the event loop open.
  try { process.stdin.pause(); process.stdin.destroy(); } catch {}
  process.stdout.write(render(), () => process.exit(0));
  // Backstop for a stdout pipe that never drains (same inheritance trap as stdin).
  setTimeout(() => process.exit(0), 250).unref();
};

const watchdog = setTimeout(finish, DEADLINE_MS);

process.stdin.on('data', (c) => chunks.push(c));
process.stdin.on('end', finish);
process.stdin.on('error', finish);
