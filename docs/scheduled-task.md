# Scheduled task

The routine runs as a Claude Code Desktop **local** scheduled task (Code tab → Routines → New routine → Local).
Local tasks run on this machine with direct access to the folder; they fire only while the app is open and the Mac is awake, and a missed run is caught up once on wake.

## Register

The schedule (10:00 on Tuesday, Thursday and Saturday) is not one of the presets, so create the task by asking Claude in any Desktop session:

```text
Create a local scheduled task named "genai-catchup-report" for the folder ~/prj/masamallow/genai-catchup.
Schedule: cron "0 10 * * 2,4,6" (10:00 on Tuesday, Thursday and Saturday, local time).
Use the prompt in docs/scheduled-task.md of that folder.
```

Or edit the generated file afterwards: `~/.claude/scheduled-tasks/genai-catchup-report/SKILL.md` holds the prompt; schedule, folder and model are edited in the app.

Recommended settings:

- Working folder: this repository.
- Model: the default model of the session is fine; a stronger model improves the synthesis more than it costs.
- Worktree isolation: off (the run must commit to the working copy).
- Settings → Desktop app → General → **Keep computer awake** if 10:00 runs are often missed.

## Prompt

```text
Run the genai-catchup-report skill for today.

- Working folder: this repository (genai-catchup). Read AGENTS.md first.
- Languages: en, ja (English is always written; remove `ja` for an English-only run).
- This is a scheduled run: set `run: scheduled` in the research note front matter.
- If the run is a catch-up after sleep, still use today's date and widen the fetch window
  (`uv run scripts/fetch_feeds.py fetch --days N`) so that the gap since the last note is covered.
- Finish with the completion message described in the skill (themes with scores, file paths per language,
  failed sources, suggested source changes). Do not push.
```

## First run

1. Open the task and press **Run now**.
2. Approve each permission prompt with "always allow".
   `.claude/settings.json` in the repository already allows `mise run`, `uv run`, `git add`/`commit`, WebFetch and WebSearch, so prompts should be rare.
3. Open the created session and read the completion message.
4. Preview with `mise run serve`, then publish with `mise run publish` when satisfied.

## Cadence notes

- Three runs a week with a 4-day window overlap on purpose; `state/seen.json` removes items already offered.
- If three reports a week turn out to be more than you read, change the cron to `0 10 * * 2,6` and the window to 5 days.
