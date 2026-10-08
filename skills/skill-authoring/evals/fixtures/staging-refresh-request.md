# Request: an agent skill for refreshing the staging database

From: a platform teammate on the Larkspur team. Repo: `larkspur-platform` (monorepo).
Tools used on this repo: GitHub Copilot and Claude Code, both daily.

## What I want

Agents keep getting the staging refresh wrong, so I want a skill for it. People ask for it
as "refresh staging", "reset the staging DB" or "pull a fresh snapshot into staging".
A refresh takes staging down for the whole team, so only a person should start one; an
agent must never begin a refresh on its own initiative (say, while debugging a test).
I already created the folder `.claude/skills/StagingRefresh/` and was going to call the
skill "Staging DB Refresh". Rename it if that is wrong.

Skills in this repo live in `.github/skills/`, and `.claude/skills/` is a symlink to that
folder. Other skills that already exist there:

- `.github/skills/prod-restore/SKILL.md` restores PRODUCTION from a point-in-time
  backup. People mix the two up constantly, and an agent once started a prod restore when asked to
  refresh staging.
- `.github/skills/staging-smoke/SKILL.md` runs the post-deploy smoke checks against
  staging. The refresh must end by running those checks, so link to it from the new skill.

It's basically just running commands, so please set `model: haiku` on it to keep it cheap.

## The procedure (as we run it today)

1. Announce in #staging-ops that staging will be down for about 20 minutes.
2. Take the latest sanitised snapshot:
   `larkctl db snapshot list --env prod-sanitised --latest`
3. Put staging in maintenance mode: `larkctl app maintenance on --env staging`
4. Drop and restore. This OVERWRITES the staging database and cannot be undone:
   `pg_restore --clean --if-exists --no-owner -d "$STAGING_DB_URL" snapshot.dump`
5. Run migrations: `larkctl db migrate --env staging`
6. Maintenance off: `larkctl app maintenance off --env staging`
7. Run the staging smoke checks (the other skill above).

If step 4 fails halfway, restore the pre-refresh dump with the same `pg_restore` command
pointed at `pre-refresh.dump`, which step 4 must therefore take first with `pg_dump -Fc`.

## Announcement template (please include it in the skill verbatim)

The post we use in #staging-ops is Markdown and contains a code block:

    **Staging refresh starting** - owner: @<you>, ETA 20 min.
    Snapshot: <snapshot-id>. To follow along:
    ```bash
    larkctl app status --env staging --watch
    ```
    Staging will be read-only until the smoke checks pass.

## pg_restore flag reference (include all of it)

Agents keep guessing flags, so put the whole reference table in the skill. First rows:

| Flag              | Meaning                                  | Use on staging? |
| ----------------- | ---------------------------------------- | --------------- |
| `--clean`         | Drop objects before recreating them      | yes             |
| `--if-exists`     | Avoid errors when dropping missing items | yes             |
| `--no-owner`      | Skip ALTER OWNER statements              | yes             |
| `--no-privileges` | Skip GRANT/REVOKE                        | yes             |
| `--jobs=N`        | Parallel restore with N workers          | yes, N=4        |
| `--single-transaction` | All-or-nothing restore              | no (with jobs)  |
| `--data-only`     | Restore data, not schema                 | no              |
| `--schema=NAME`   | Restore one schema only                  | rarely          |

(The full table continues for roughly 200 more rows in the same shape, covering every
flag plus the matching `pg_dump` and `psql` options. It lives in our wiki today.)

## Team SQL conventions (add these so agents follow them everywhere)

- Table names are snake_case and plural; columns are snake_case.
- Never use `SELECT *` in application queries.
- Every migration file is idempotent and named `YYYYMMDDHHMM_description.sql`.
- Prefer `timestamptz` over `timestamp`.

These apply to all SQL in the repo, not only the refresh.
