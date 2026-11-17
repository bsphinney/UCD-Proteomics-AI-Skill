# Using the skill with a coding agent other than Claude Code

Written 2026-11-17 against skill 2.15.0, by surveying the skill's files. The other-agent facts were read from each
tool's own documentation on that date; the source is linked next to each one. These tools change
fast, so check the link before you rely on a detail. Nothing here has been tested by running the
skill under another agent.

## Summary

**What works anywhere.** Almost all of the skill is plain files and scripts: Python, bash and R
programs in [`scripts/`](../skill/ucdavis-proteomics-core-pipeline/scripts/), written steps in
[`references/`](../skill/ucdavis-proteomics-core-pipeline/references/), and a router,
[`SKILL.md`](../skill/ucdavis-proteomics-core-pipeline/SKILL.md). The search, the statistics, the
report builder, SLURM and SSH to HIVE, Slack, the podcast (Gemini or Kokoro voices) and the
reproducibility bundle do not call Claude. Any agent that can read files and run shell commands
can follow the steps.

**What needs Claude Code.** Four things:

1. The install and update commands (`claude plugin ...`, `/plugin`, `/reload-plugins`).
2. Three hooks that save the chat transcript and nag the agent to finish. Without them the
   skill still works, but the chat record is not saved.
3. Reading Claude Code's own transcript files to build the conversation record.
4. A few instructions that name Claude Code tools: the `Agent` tool for expert reviewers, the
   `Monitor` tool and `/loop` for Slack watching, `run_in_background` for long jobs.

**How hard is a port.** A first, useful port is small: copy the skill folder to the place the
other agent looks for skills (many now read `.agents/skills/`). The core pipeline then runs.
Expect the version check at session start to fail or be skipped, expect no saved transcript, and
expect the reviewer step to need a hand-written substitute. Nothing breaks the science. The
skill's own text calls other agents out in one place already: `save_transcript.py` says "Other
agents (not Claude Code): there is no transcript to find" and relies on `logs/decisions.md`
instead ([save_transcript.py:50-52](../skill/ucdavis-proteomics-core-pipeline/scripts/save_transcript.py)).

## Where the skill depends on Claude Code

Paths are relative to `skill/ucdavis-proteomics-core-pipeline/` unless they start with `../` or `.`.
"Breaks" = the step fails or is skipped. "Degrades" = the work finishes with less. "Cosmetic" = only
wording.

| Claude-specific thing | Where | Under another agent | Matters | Workaround |
|---|---|---|---|---|
| Plugin packaging: `.claude-plugin/plugin.json` and the marketplace file | `.claude-plugin/plugin.json`; `../.claude-plugin/marketplace.json`; `../AGENTS.md:20-23` | Other agents ignore these files. | Breaks the install path only | Copy the folder into the agent's skills folder (section below). Keep the files: the skill's scripts read the version from `plugin.json`. |
| `plugin.json` is the **one source of the skill version**, read by many scripts | `scripts/skill_version.py:36,50`; `scripts/skill_version.R:17`; `scripts/notify_slack.py:415`; `scripts/record_run.py:3322`; `scripts/hive_exec.sh:27,289`; `scripts/bump_version.py:42-43` | Works, as long as the file is still there beside `scripts/`. | Breaks if you delete `.claude-plugin/` | Copy the whole skill folder, including the hidden `.claude-plugin/` directory. |
| Install and update by `claude plugin ...` and slash commands `/plugin`, `/reload-plugins` | `SKILL.md:107,123,127`; `references/install.md:20-31`; `references/access.md:236-243,688-698`; `references/notes.md:336`; `scripts/provenance.py:984-986`; `scripts/skill_version.sh` (about 20 places, e.g. 55, 95, 640, 649, 794, 851, 944) | The version check (step 0) tries to run the `claude` command. Without it, the update steps cannot run and the agent is told to do things by hand. `skill_version.sh` skips the self-move when `claude` is missing or the session is not Claude Code CLI or VS Code. | Degrades (breaks the auto-update) | Update by `git pull` in your clone and re-copy. Tell the agent to ignore the `/reload-plugins` lines. |
| `${CLAUDE_PLUGIN_ROOT}` in the hook commands | `hooks/hooks.json:9,20,31` | The variable is empty. The hook commands fail. | Breaks the hooks only | See the hooks row. Scripts themselves are called as `scripts/<name>`, relative, with no plugin variable. |
| Skills folder `~/.claude/skills`, config dir `$CLAUDE_CONFIG_DIR` | `scripts/check_access.sh:312-313`; `references/access.md:80`; `references/de-analysis.md:693` (the HPC@UCD skill's helper path) | `check_access.sh` looks for the required `ucd-hpc` skill under `~/.claude/skills`, and may report it missing when it is installed under another agent's folder. | Degrades | Install `ucd-hpc` where your agent reads skills, then ignore a false "not installed" note, or point the check at the right folder. |
| **Stop hook**: reminds the agent once, with the finish checklist, if an analysis has items missing | `hooks/hooks.json:27-34`; `scripts/finish_stop_hook.py:1-37,169-190` | No reminder. The agent may end without finalizing, writing the report or making the bundle. This is the failure the hook was added for. | Degrades (quality) | Ask the agent to run `python3 scripts/session.py status --session <dir>` before it stops (`SKILL.md:25` already names it), or wire the script to your agent's stop hook (see below). |
| **PreCompact and SessionEnd hooks**: save the conversation into the session folder | `hooks/hooks.json:4-25`; `scripts/transcript_hook.py:1-40` | No transcript is saved. | Degrades | Run `save_transcript.py` by hand, or accept `logs/decisions.md` as the record. |
| Hook input and output format: stdin JSON `{session_id, transcript_path, cwd, hook_event_name, stop_hook_active}`; stdout `hookSpecificOutput.additionalContext` | `scripts/finish_stop_hook.py:32-37,169-190`; `scripts/transcript_hook.py:11-16` | Other agents send different fields and expect different output. The script then finds no session and exits silently, which is safe. | Degrades | A small wrapper that translates fields. See the per-agent notes. |
| Transcript saving reads **Claude Code's private file format and paths**: `CLAUDE_CODE_SESSION_ID`, `<config>/projects/<cwd>/<id>.jsonl`, entry types, subagent files, the `Skill` tool call | `scripts/save_transcript.py:26-29,216-325,375-403,497-603`; `scripts/session.py:590-592,1017-1020`; `scripts/log_decision.py:69-70`; `references/outputs.md:276-308,322` | The script says "not a Claude Code conversation here", writes nothing, exits 0. `session.py status` marks the conversation item `[SKIPPED]` rather than failing. | Degrades | Use `scripts/log_decision.py` at each decision; it is the same record by design. To save a real transcript, export it from your agent and pass it with `--transcript <file> --session-id <id>`, but the parser only understands Claude Code's format (`save_transcript.py:12`), so it will be mostly "[unrecognised entry]". |
| `CLAUDE_CODE_ENTRYPOINT` (CLI, VS Code, Desktop) decides whether the marketplace self-move runs | `references/access.md:693-696`; `references/install.md:71-75` | Not set, so the move is skipped. | Cosmetic | None needed. |
| `--call-id` for transcripts when **Claude Code subagents** share the parent's session id | `SKILL.md:259`; `scripts/save_transcript.py:375-382,463-465`; `scripts/session.py:592`; `scripts/checkpoint.py:160,367` | Harmless: it is only needed when subagents run and a transcript is saved. | Cosmetic | Ignore. |
| **Expert reviewers**: "spawn three agents in parallel (one message, three `Agent` calls)" | `SKILL.md:396-400`; `references/anomaly-checks.md:145-157,197`; `references/podcast.md:406` (one `Agent` call) | An agent with no subagent tool will not know what "Agent" means. It may skip the review or play all three roles in one pass. A same-context review is weaker, because the point of the step is a reviewer who did not write the work. | Degrades | Say: "run each reviewer as a separate fresh session or subagent, or do three sequential passes with only the report and file paths as input." Codex, Gemini CLI, Cursor, Copilot, OpenCode and Goose each have a subagent feature (below). |
| **Monitor tool**, `/loop`, `run_in_background` for watching a run or a Slack thread | `references/slack-collab.md:286-293,505`; `references/watcher.md:359`; `references/access.md:506`; `scripts/board_client.py:474`; `SKILL.md:113,156,231,347,432,444,451` ("in the background") | Without a background-task feature the agent blocks on long commands and may hit its command timeout (the text says a killed call cancels the `srun`). The Slack watch needs a loop. | Degrades; for long HIVE steps it can break | Use the agent's own background or long-running command option. Or run `hive_exec.sh --job` and poll with a short command. The scripts print one JSON line per event, so any polling loop can read them. |
| Claude's own questions and approvals: "ask the user", "the decision is the person's, never Claude's" | `SKILL.md:142,372,489,495-499`; `references/board.md` | Wording only. Another agent should read "Claude" as "the agent". The rule (a person decides, never the agent) must still hold. | Cosmetic | None. Do not relax the rule. |
| The report text says **Claude** wrote it | `scripts/make_analysis_html.py:1062` ("Claude, Anthropic's AI model, ran each step"); `scripts/provenance.py:1665` ("run by the above Claude skill (in Claude Code / Claude Desktop)"); `scripts/make_podcast.py:4897,4939,4970`; `scripts/analysis_prompt.py:8` | A report written by another model would still say Claude did the work. That is a **wrong statement in a deliverable.** | Degrades (accuracy) | Edit those lines to take the agent and model name from a setting or from the agent, before using another agent on real data. Do this first. |
| Agent-name lists | `scripts/staff.py:62,73` (treats "gpt", "gemini", "copilot", "claude code" as agent names, not people) | Already agent-neutral. | None | None. |
| Prompt phrased for Claude ("the agent IS Claude") | `scripts/analysis_prompt.py:7-10` | The brief is plain Markdown. Works with any model. | Cosmetic | None. |
| `SKILL.md` front matter | `SKILL.md:1-15` (only `name` and `description`) | Already the open Agent Skills format. No Claude-only fields (no `allowed-tools`, no `hooks:`). | None | None. |
| Skill loading model: description-triggered, `references/` read on demand | `SKILL.md:1-15`, router layout | The same model is used by the other agents below. | None | Their trigger quality depends on the description. Test a few phrasings. |
| Skill size | `SKILL.md` is 499 lines; the spec recommends under 500 and the body under about 5,000 tokens | Some agents may load it whole. | Cosmetic | None. |
| Tests and checks | `tests/`, `../.github/workflows/skill-checks.yml`, `../tools/` | Plain `unittest`. No agent needed. | None | None. |

### Things that look Claude-specific but are not

- **Podcast voices.** Gemini (cloud) and Kokoro/Whisper (on HIVE) are used for audio. They are
  unrelated to which coding agent you run. See `references/podcast.md`.
- **Slack, the board, CoreOmics, Bioshare, FRAN.** HTTP APIs and scripts. A "Claude" in the Slack
  text is a label (`scripts/board_client.py:644` is a field named `claude`), not a dependency.
  `references/slack-app-manifest.yaml:18` mentions Claude Code in a description only.
- **HIVE, SLURM, SSH, Apptainer, DIA-NN, Sage, FragPipe, R/limma/limpa.** All plain programs.
- **Secret redaction** lists `sk-ant-...` and OpenAI key patterns (`scripts/notify_slack.py:173`;
  `references/notifications.md:234`). It guards against leaks. It is not an API call.
- **The skill never calls the Anthropic API or the `claude -p` command to do its work.** The
  only `claude` command it runs is `claude plugin ...` for updates (above). A search for
  `claude -p` in the scripts finds only a comment about a past test
  (`scripts/transcript_hook.py:11`).
- **`ucd-hpc`.** The HPC@UCD skill is mandatory on the clusters and is itself a SKILL.md skill, so
  it ports the same way.

## Starting points per agent

All of these now read `SKILL.md` folders and `AGENTS.md`. Each line below was read from the
named page on 2026-11-17. "Not stated" means the page I read did not say, not that it is absent.

**Open format first.** The Agent Skills format is an open spec:
[agentskills.io/specification](https://agentskills.io/specification). Required front matter is
`name` (must match the folder name) and `description`. Optional: `license`, `compatibility`,
`metadata`, and an experimental `allowed-tools`. Folders `scripts/`, `references/`, `assets/` are
the conventions this skill already uses. Our `SKILL.md` front matter is valid under it.
Whether our folder name `ucdavis-proteomics-core-pipeline` matches the `name` field: yes, both are
that string.

A common location now works in several tools: **`.agents/skills/<skill>/`** (project) or
**`~/.agents/skills/<skill>/`** (your user). Putting the skill there is the best first try.

### OpenAI Codex CLI
- Instructions: reads `AGENTS.md` from the repo root down to the current folder, total capped at
  32 KiB by default (`project_doc_max_bytes`). Our `AGENTS.md` is small, so it fits.
  [AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- Skills: `.agents/skills` in the repo, `$HOME/.agents/skills`, `/etc/codex/skills`. Needs `name`
  and `description`. Chosen by description, or by `/skills` or `$`. Optional `agents/openai.yaml`.
  [Skills](https://learn.chatgpt.com/docs/build-skills)
- Hooks: yes, on by default, including `PreCompact`, `Stop`, `SessionStart`, `SessionEnd`. Config in
  `~/.codex/hooks.json` or `.codex/hooks.json`; hooks must be trusted via `/hooks`. Stdin JSON has
  `session_id`, `transcript_path`, `cwd`, `hook_event_name`. For `Stop`, plain text on stdout is
  invalid; use JSON. This is the closest match to Claude Code's hooks.
  [Hooks](https://learn.chatgpt.com/docs/hooks)
- Subagents: yes, TOML files in `.codex/agents/`, enabled by default, but Codex only uses them
  when you ask for subagents or parallel agents.
  [Subagents](https://developers.openai.com/codex/subagents)
- Background commands: not verified.
- Minimal port: copy the skill to `.agents/skills/ucdavis-proteomics-core-pipeline/`; say
  "use subagents to run the three reviewers"; skip the hooks at first.

### Gemini CLI
- Instructions: reads `GEMINI.md` (global `~/.gemini/GEMINI.md`, and in the workspace and parents).
  It can read `AGENTS.md` if you set `context.fileName` in `settings.json` to include it.
  [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/)
- Skills: `~/.gemini/skills/` or `~/.agents/skills/`; `.gemini/skills/` or `.agents/skills/` in a
  workspace. Name and description are put in the prompt; the model calls `activate_skill`, and
  the user is asked to approve. The page did not describe the file format.
  [Skills](https://geminicli.com/docs/cli/skills/)
- Hooks: yes, in `settings.json`: `SessionStart`, `SessionEnd`, `BeforeAgent`, `AfterAgent`,
  `BeforeTool`, `AfterTool`, `PreCompress`, `Notification`. Command hooks only. Stdout must be
  only JSON. There is no `Stop` by that name (`AfterAgent` is the nearest; unverified). Only
  `CLAUDE_PROJECT_DIR` is offered as an alias.
  [Hooks](https://geminicli.com/docs/hooks/)
- Subagents: yes, Markdown files in `.gemini/agents/`, on by default, called by `@name` or chosen by
  the main agent. Parallel running: not stated. Subagents cannot call other subagents.
  [Subagents](https://geminicli.com/docs/core/subagents/)
- Note: the skills and subagents pages carry a banner saying Gemini CLI was replaced by Antigravity
  CLI on 2026-06-18 for unpaid-tier and Google One users. I did not check Antigravity.
- Minimal port: skill into `.agents/skills/`; add `AGENTS.md` to `context.fileName`.

### Cursor
- Instructions: reads `AGENTS.md` in the root and subfolders; also `.cursor/rules/*.mdc`.
  [Rules](https://cursor.com/docs/context/rules)
- Skills: `.agents/skills/`, `.cursor/skills/`, user-level `~/.agents/skills/`, `~/.cursor/skills/`,
  and for compatibility `.claude/skills/` and `.codex/skills/`. Needs `name` (matching the folder)
  and `description`.
  [Skills](https://cursor.com/docs/skills)
- Hooks: yes (`hooks.json`, `~/.cursor/hooks.json` or `.cursor/hooks.json`): `sessionStart`,
  `sessionEnd`, `preCompact`, `stop`, `subagentStart`, others. Stdin has `conversation_id` and
  `transcript_path`; a `stop` hook can return `followup_message`. Exit 2 blocks, as in Claude
  Code. Cursor says it can load hooks from Claude Code; the mapping is on a separate page I did
  not read (unverified).
  [Hooks](https://cursor.com/docs/hooks)
- Subagents: the skills page mentions a `/create-subagent` skill; no detail. Treat as unverified.
- Background commands: not verified.
- Minimal port: place the skill in `.cursor/skills/`; no other change for a first run.

### GitHub Copilot (coding agent, CLI, VS Code agent mode)
- Instructions: `AGENTS.md` (nearest wins), `.github/copilot-instructions.md`; `CLAUDE.md` or
  `GEMINI.md` accepted as a single root file.
  [Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)
- Skills: project `.github/skills`, `.claude/skills` or `.agents/skills`; personal `~/.copilot/skills`
  or `~/.agents/skills`. Supported in Copilot CLI, the cloud agent, and agent mode in VS Code,
  Visual Studio and JetBrains (varies by version). A skill with a mismatched folder name fails
  silently in VS Code.
  [About skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills),
  [VS Code skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- Hooks: in VS Code, preview. `.github/hooks/*.json`; events `sessionStart`, `sessionEnd`,
  `preCompact`, `agentStop`, `subagentStart`, `preToolUse`. VS Code also reads
  `.claude/settings.json`. Output rules differ from Claude Code's.
  [Hooks](https://code.visualstudio.com/docs/copilot/customization/hooks)
- Subagents: custom agents exist; a skill with `context: fork` runs in a subagent (VS Code page).
- **The cloud coding agent runs in GitHub Actions with a 59-minute limit per session and can
  change only the one repository** (same docs, [coding agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)).
  This skill needs SSH to HIVE and multi-hour searches, so it is a poor fit there. Use the CLI or
  VS Code on your own computer.
- Minimal port: `.github/skills/` or `.agents/skills/`; use VS Code or Copilot CLI locally.

### OpenCode
- Instructions: `AGENTS.md`; falls back to `CLAUDE.md` and `~/.claude/CLAUDE.md` when there is no
  `AGENTS.md`. Can be switched off by environment variables.
  [Rules](https://opencode.ai/docs/rules/)
- Skills: reads `.opencode/skills`, `.claude/skills`, `.agents/skills` (project) and
  `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` (global). The model loads a
  skill with a `skill` tool. A skill without a `description` is not advertised.
  [Skills](https://opencode.ai/docs/skills/)
- Hooks: it has JS/TS plugins in `.opencode/plugins/`. I did not find the event list; unverified.
  [Plugins](https://opencode.ai/docs/plugins/)
- Subagents: yes; Markdown in `.opencode/agents/`, run in child sessions through a `subagent`
  tool; ask in plain text ("use the reviewer subagent").
  [Agents](https://opencode.ai/docs/agents/)
- Minimal port: it already finds a Claude Code install under `~/.claude/skills`; otherwise copy
  to `~/.agents/skills/`.

### Goose
- Instructions: reads `AGENTS.md` then `.goosehints` by default; `CONTEXT_FILE_NAMES` changes the list.
  [Hints](https://goose-docs.ai/docs/guides/context-engineering/using-goosehints)
- Skills: `~/.agents/skills/`, project `.agents/skills/`, and for compatibility `.claude/skills/`
  and `~/.claude/skills/`. Needs `name` and `description`.
  [Skills](https://goose-docs.ai/docs/guides/context-engineering/using-skills)
- Subagents: a custom-agents page exists (delegation to isolated sessions). I saw it only in a
  search summary, not the page itself, so treat as unverified.
- Hooks: not verified.
- Minimal port: skill into `~/.agents/skills/`.

## Suggested order of work for a port

1. **Fix the authorship statements first** (`make_analysis_html.py:1062`, `provenance.py:1665`,
   `make_podcast.py:4939`). Make the agent and model name a setting. Until then, do not use another
   agent on a real report. This is the one place the output would say something untrue.
2. **Copy the whole skill folder** (with `.claude-plugin/`) to `.agents/skills/` or your agent's
   folder. Ask a test question ("analyze these .raw files") and check the agent picks the skill.
   Use a small public dataset, never client data.
3. **Install the HPC@UCD skill (`ucd-hpc`) the same way** if you work on HIVE, Farm or Franklin.
   It is required there. Fix the folder it is looked for in (`check_access.sh:312-313`).
4. **Tell the agent three things in your own `AGENTS.md` or prompt**: ignore `/plugin` and
   `/reload-plugins`; run long steps as background or long commands; run the three reviewers as
   separate fresh sessions or subagents.
5. **Replace the Stop hook with one command.** Run `session.py status --session <dir>` before ending.
   Later, if your agent has a stop hook (Codex, Cursor, Gemini `AfterAgent`, Copilot `agentStop`),
   wrap `finish_stop_hook.py` to translate the input fields and output format.
6. **Transcripts.** Keep using `log_decision.py`. Only write a new parser for your agent's
   transcript format if you need the full chat.
7. **Updates.** Put the clone under `git pull` and re-copy. Make `skill_version.sh` skip `claude plugin`
   when `claude` is absent (it already does in some paths).
8. **Add a test.** Run the same small dataset under Claude Code and the other agent. Compare the
   report, the Methods, `session.py status`, and `MANIFEST.txt`.

## Not verified

- Behaviour of this skill under any non-Claude agent: nothing was run.
- Codex background-command support; Cursor subagent and background features; Goose hooks;
  OpenCode plugin event names; Gemini `AfterAgent` as an equivalent of `Stop`.
- Cursor's mapping of Claude Code hook files (separate "Third Party Hooks" page, not read).
- Goose subagent details (search summary only).
- Antigravity CLI, which replaced Gemini CLI for some users (banner only).
- Whether each agent runs `scripts/<name>` paths relative to the skill folder: `SKILL.md`
  uses relative `scripts/` paths and never states a base directory, so an agent must know where
  the skill folder is. This was not tested.
