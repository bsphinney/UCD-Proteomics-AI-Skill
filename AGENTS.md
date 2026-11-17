# AGENTS.md

Notes for AI coding agents (Claude Code, Codex, Cursor and others) that work in this repository
or are asked to install the skill. People should start with the [README](README.md).

## What this repository is

The UC Davis Proteomics Core pipeline as an agent skill: `ucdavis-proteomics-core-pipeline`.
It takes raw mass-spec files (`.raw`, `.d`, `.mzML`) to a search (DIA-NN, FragPipe or Sage),
differential expression (limpa/limma), a report, a Methods section and a reproducibility bundle.

- The skill itself is `skill/ucdavis-proteomics-core-pipeline/`. Its entry point is
  [`SKILL.md`](skill/ucdavis-proteomics-core-pipeline/SKILL.md), a short router that sends the agent
  to the files in `references/` for the detail.
- Every file the skill ships, with what it does and what uses it (the scripts, the references and
  the plugin hooks), is listed in [`docs/SKILL_INVENTORY.md`](docs/SKILL_INVENTORY.md).

## If you were asked to install or use the skill

Install it as a Claude Code plugin (one line, in a terminal):

```
claude plugin marketplace add https://github.com/bsphinney/UCD-Proteomics-AI-Skill.git && claude plugin install ucdavis-proteomics-core-pipeline@ucdavis-proteomics-core
```

Using another agent (Codex, Gemini CLI, Cursor, Copilot, OpenCode, Goose)? Read
[`docs/OTHER_AGENTS.md`](docs/OTHER_AGENTS.md) first: it lists what in the skill is specific to
Claude Code, what happens without it, and where each agent looks for skills.

Then follow `SKILL.md`. Do not hand-write a search job or a DIA-NN/Sage command line instead: the
skill derives the parameters from the data, pins the engine version and records provenance.

## If you are changing the repository

Layout: `skill/` (what gets installed: `SKILL.md`, `references/`, `scripts/`, `presets/`,
`hooks/`, `tests/`), `docs/` (the GitHub Pages site and the inventory), `tools/` (the inventory
generator and its tests), `contaminants/`, `.claude-plugin/` (the marketplace catalogue).

Run the same checks GitHub runs ([`.github/workflows/skill-checks.yml`](.github/workflows/skill-checks.yml)):

```
python3 -m unittest discover -s skill/ucdavis-proteomics-core-pipeline/tests
python3 -m unittest discover -s tools
python3 tools/make_inventory.py --check
```

Rules the checks enforce:

- **The inventory is generated.** After adding, removing or renaming a file in the skill, or
  changing a file's header, run `python3 tools/make_inventory.py`. Never edit
  `docs/SKILL_INVENTORY.md` by hand. Every new file needs a header whose first sentence says what
  it does.
- **Versions agree.** `skill/ucdavis-proteomics-core-pipeline/.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` carry the same version. Add a `CHANGELOG.md` entry for each
  release.
- **Every `scripts/<file>` named in the docs exists**, scripts with a shebang are executable, and
  the shell and Python scripts parse.
- **No dev-only files in the skill payload** (`TODO.md`, `NOTES.md`, `scratch.md`,
  `TODO_TEST_ON_HIVE.md`): everything under `skill/` lands in every user's plugin cache.
- **Links resolve.** Relative links in the README must point at files that exist.

Rules the checks cannot enforce:

- **No client data, names or identifiers**, ever: not in code, tests, examples or docs. Use public
  datasets (for example PRIDE PXD063416) for examples and fixtures.
- **Never hard-code a description of what the analysis did.** Methods text, reports and logs read
  it from the run's own records, so they stay true for every engine and route.
- **On UC Davis clusters (HIVE, Farm, Franklin)** follow the HPC@UCD agent skill
  (see [docs.hpc.ucdavis.edu](https://docs.hpc.ucdavis.edu)): no computing on login nodes, and an
  explicit account, partition, time and memory on every job.

Changes come in as pull requests. Questions and bugs:
[issues](https://github.com/bsphinney/UCD-Proteomics-AI-Skill/issues).
