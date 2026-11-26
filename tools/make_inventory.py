#!/usr/bin/env python3
"""Write docs/SKILL_INVENTORY.md: every file the skill ships, what it does and what uses it.

Generated, never hand-written: what a file does comes from the file's own header, so the header
is the one place it is said (a Python module's docstring, the first comment block of a shell or R
script, a reference's first heading and line, a JSON file's "_about", an HTML page's first
<!-- comment -->). A file that is another project's, byte for byte (a FragPipe or Radiant preset),
cannot carry a header of ours: the SOURCES.json beside it says what it is, and that is read. Where it is named in
SKILL.md and the references, and whether it is run directly or only called by other scripts, is
found by searching the skill's own text. To change a file's line in the inventory, change the
file's header and run this again.

    python3 tools/make_inventory.py              write docs/SKILL_INVENTORY.md
    python3 tools/make_inventory.py --check      exit 1 if the committed inventory is out of date
    python3 tools/make_inventory.py --missing F  also write the files with no usable header to F

This tool lives outside skill/, so it is not part of the plugin that users install. Standard
library only.
"""
import argparse
import ast
import collections
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True        # it imports the skill's identifier rule from skill/.../tests
TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
SKILL_REL = "skill/ucdavis-proteomics-core-pipeline"
OUT_REL = "docs/SKILL_INVENTORY.md"
NO_DESCRIPTION = "no description"
SKIP_NAMES = {"__pycache__", ".pytest_cache", ".DS_Store", ".mypy_cache", ".ruff_cache"}

# The jobs the inventory is grouped by, in the order a run meets them. A file goes in the first
# group one of whose patterns matches its path under the skill (re.search). This table is a
# grouping, not a description: what each file does is read from the file. A file no rule matches
# lands in "Other", which says to add a rule here.
GROUPS = (
    ("The skill and the plugin",
     "What Claude Code installs and reads first.",
     (r"^SKILL\.md$", r"^\.claude-plugin/", r"^hooks/")),
    ("Staff only",
     "Used by UC Davis Proteomics Core staff only: the project board, notes from the Core, the QC "
     "runs around a project, who may sign a decision, and Claude-to-Claude work in Slack.",
     (r"/board", r"/notes\.", r"/staff\.py$", r"/core_admins\.txt$", r"/qc_bracket\.py$",
      r"/qc-bracket\.md$", r"/slack[-_]", r"/coreomics_key_to_hive\.sh$")),
    ("Setup and tools",
     "Installing the toolchain and the pinned engines, checking the environment, and keeping the "
     "skill current.",
     (r"/setup\.sh$", r"/acquire_tools\.sh$", r"/detect_env\.sh$", r"/check_access\.sh$",
      r"/build_diann_docker\.sh$", r"/diann_release\.sh$", r"/ensure_dotnet8\.sh$",
      r"/skill_version\.", r"/bump_version\.py$", r"/report_issue\.sh$", r"/install\.md$",
      r"/environment\.md$", r"/fragpipe_bootstrap\.py$", r"/build_directlfq_venv\.sh$",
      r"/skill-issues\.md$")),
    ("Cluster and transport",
     "Reaching HIVE, running on compute nodes and never on a login node, watching jobs, and "
     "recovering from node faults.",
     (r"/hive_", r"/on_compute\.py$", r"/node_fault\.py$", r"/watch_run\.sh$",
      r"/watcher\.md$", r"/checkpoint\.py$", r"/cpu_hours\.py$", r"/safe_write\.py$",
      r"/access\.md$", r"/share_map\.py$", r"/queue_actual\.py$", r"/slurm_states\.py$")),
    ("Search",
     "From raw files to a search report: acquisition and instrument, the database, the parameters, "
     "the engines and their parallel chains.",
     (r"^presets/", r"/detect_acquisition", r"/acq_time", r"/bruker_", r"/thermo_resolution",
      r"/estimate_params", r"/resolve_defaults", r"/resolve_organism", r"/fetch_", r"/make_presets",
      r"/run_search", r"/diann_", r"/dda_first_pass", r"/probe_", r"/check_report_runs",
      r"/pass_comparison", r"radiant", r"/diatracer", r"/fragpipe", r"/sage_", r"/denovo_",
      r"/cleavage_rules", r"/protein_ids", r"/compare_searches", r"/superseded_databases",
      r"/near_identical_contaminants", r"/silac\.py$", r"/parameters\.md$",
      r"/search-engines\.md$", r"/pipeline_notes\.py$", r"/denovo\.md$", r"/engine_choice\.py$",
      r"/faims\.py$", r"/fasta_guard\.py$")),
    ("Differential expression",
     "The study design, the quantities, the statistics, the checks on them, and the set tests.",
     (r"/run_de\.R$", r"/blocking\.R$", r"/contaminant", r"/limpa_compat\.R$", r"/build_maxlfq",
      r"/run_sets\.R$", r"/set_tests\.R$", r"/sim_set_tests\.R$", r"/set-tests\.md$", r"silac",
      r"/experiment_type", r"/normalization_check", r"/collect_conditions", r"/conditions\.md$",
      r"/sample_type", r"/sample_quality", r"/audit", r"/anomaly-checks\.md$",
      r"/compare_analyses", r"/de-analysis\.md$", r"/no-de-route\.md$", r"/study-questions\.md$",
      r"/compute_record\.R$", r"/run_name\.R$")),
    ("Report and Methods",
     "The report of record, its figures and wording, the Methods, the podcast and the peak check.",
     (r"/make_report", r"/credit\.py$", r"/make_analysis_html", r"/make_figures", r"/make_methods", r"/methods\.md$",
      r"/analysis_prompt", r"/analysis\.md$", r"podcast", r"/kokoro", r"/client_text",
      r"/report_style", r"/report_files", r"/html_to_pdf", r"/to_docx", r"/make_comparison_report",
      r"/cross-tool-comparison\.md$", r"/skyline", r"/outputs\.md$")),
    ("The protein screen",
     "\"Show me the data for <protein>\": the data behind it, the facts looked up for each protein, "
     "and the pages that draw it.",
     (r"/protein_screen", r"/make_protein_screen\.py$", r"/make_screen_data\.R$",
      r"/screen_shares\.R$", r"/protein_facts\.py$", r"/protein-card-sources\.md$",
      r"/protein-screen\.md$")),
    ("Reproducibility and finalize",
     "The session folder, the reproducibility bundle, the decisions log and the conversation "
     "record, and the public-repository deposit.",
     (r"/provenance", r"/repro", r"/runtime_record", r"/session", r"/custom_work", r"/scratch_files",
      r"/log_decision", r"/save_transcript", r"/transcript_hook", r"/make_deposit\.py$",
      r"/deposit\.md$", r"/finish_stop_hook\.py$")),
    ("Delivery and CoreOmics",
     "Core service runs: the CoreOmics submission, high-throughput plates, delivery to the "
     "collaborator, the job-end hook, the run registry and the FRAN hand-off.",
     (r"/core_submission", r"/core-submissions\.md$", r"/submission_report", r"/ht_",
      r"/ht-submissions\.md$", r"/notify_slack", r"/notifications\.md$", r"/fran",
      r"/record_run", r"/run-registry\.md$", r"/core_sync\.sh$")),
)
OTHER = ("Other", "Files no rule in tools/make_inventory.py's GROUPS places yet: add one.")

ABBREV = ("e.g.", "i.e.", "vs.", "etc.", "cf.", "approx.", "incl.", "Fig.", "no.", "v.", "et al.")


# ---------------------------------------------------------------- the shipped files

def shipped_files(repo=REPO):
    """Every file under the skill, as paths relative to the skill folder, sorted. git's list
    when the repository is a git checkout (what is committed is what ships), else the folder."""
    skill = os.path.join(repo, SKILL_REL)
    try:
        out = subprocess.run(["git", "-C", repo, "ls-files", "-z", "--", SKILL_REL],
                             capture_output=True, check=True).stdout.decode("utf-8")
        files = [p[len(SKILL_REL) + 1:] for p in out.split("\0") if p]
        if files:
            return sorted(f for f in files if os.path.isfile(os.path.join(skill, f)))
    except (OSError, subprocess.CalledProcessError):
        pass
    found = []
    for dp, dns, fns in os.walk(skill):
        dns[:] = [d for d in dns if d not in SKIP_NAMES]
        for fn in fns:
            if fn not in SKIP_NAMES and not fn.endswith(".pyc"):
                found.append(os.path.relpath(os.path.join(dp, fn), skill).replace(os.sep, "/"))
    return sorted(found)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------- what a file says it does

def comment_paragraphs(text, marks=("#",)):
    """The paragraphs of the file's first comment block (after a shebang), blank comment lines
    separating them; ruler lines (===, ---) are dropped."""
    paras, cur, started = [], [], False
    for line in text.splitlines():
        s = line.strip()
        if not started and (not s or s.startswith("#!") or
                            re.match(r"#\s*(-\*-|shellcheck|SBATCH|vim:)", s)):
            continue
        mark = next((m for m in marks if s.startswith(m)), None)
        if mark is None:
            break
        started = True
        raw = re.sub(r"^(" + "|".join(re.escape(m) for m in marks) + r")+'?\s?", "", s)
        t = raw.strip()
        if cur and raw[:2] == "  " and (re.search(r"\S {2,}\S", t) or re.match(r"([-*•]|\d+[.)])\s", t)):
            paras.append(" ".join(cur))                       # an indented table or list: stop
            cur = []                                          # (a hanging indent continues)
            continue
        if not t or set(t) <= set("=-*#~_ "):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        cur.append(t)
    if cur:
        paras.append(" ".join(cur))
    return paras


def docstring_paragraphs(text):
    try:
        doc = ast.get_docstring(ast.parse(text))
    except SyntaxError:
        return []
    if not doc:
        return []
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", doc) if p.strip()]


def pick_paragraph(paras, name):
    """The paragraph that names the file ("x.py -- ..."), else the first one."""
    stem = re.escape(name)
    for p in paras:
        if re.match(r"`?" + stem + r"`?\s*(--|—|-|:)", p):
            return p
    return paras[0] if paras else ""


def strip_name(text, name):
    """'x.py -- does y.' -> 'does y.' (and 'x.py: ...', 'x.py — ...')."""
    return re.sub(r"^`?" + re.escape(name) + r"`?\s*(--|—|-|:)\s*", "", text).strip()


SENTENCE_END = re.compile(r"[.!?](?=\s+(?:[A-Z(`\"']|[a-z_][\w-]*\.(?:py|sh|R|md|json)\b)|\s*$)")


def first_sentence(text, limit=300):
    text = " ".join(text.replace("**", "").split())
    ends = [m.end() for m in SENTENCE_END.finditer(text)
            if not any(text[:m.end()].endswith(a) for a in ABBREV)]
    if ends:
        cut = ends[0]
        if text[cut - 1] == "?" and len(ends) > 1:           # a question: take its answer too
            cut = ends[1]
        text = text[:cut]
    text = re.sub(r"\s*\((?:skill\s+)?\d+\.\d+(?:\.\d+)?(?:,[^)]*)?\)", "", text)  # "(2.14.2, L11)"
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
        text = cut + " …"
    text = text.strip()
    first = text.split(" ", 1)[0]
    if text[:1].islower() and not re.search(r"[._/:()]", first):
        text = text[0].upper() + text[1:]
    return text


def markdown_summary(text):
    """A reference's first heading, and the first sentence of its first paragraph."""
    lines, fence = text.splitlines(), False
    if lines and lines[0].strip() == "---":                  # front matter (SKILL.md)
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        fm = "\n".join(lines[1:end])
        m = re.search(r"(?ms)^description:\s*>?-?\s*\n?(.*?)(?=^\S|\Z)", fm)
        if m:
            return first_sentence(" ".join(m.group(1).split()))
        lines = lines[end + 1:]
    heading, body = "", []
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if s.startswith("#"):
            if heading and body:
                break
            if not heading:
                heading = s.lstrip("#").strip()
            continue
        if heading and s:
            body.append(s)
        elif heading and body:
            break
    lead = first_sentence(" ".join(body)) if body else ""
    if heading and lead:
        return f"{heading}: {lead}"
    return heading


def vendor_entry(sources_text, name):
    """'<vendor workflow> (<source>), unchanged: <used for>.' from a SOURCES.json beside a
    vendor file (its "presets" entry for `name`), or '' when it has none."""
    try:
        data = json.loads(sources_text)
    except ValueError:
        return ""
    e = (data.get("presets") or {}).get(name) if isinstance(data, dict) else None
    if not isinstance(e, dict) or not isinstance(e.get("used_for"), str):
        return ""
    what = e.get("vendor_workflow") or name
    src = f" ({e['source']})" if isinstance(e.get("source"), str) else ""
    vendor = e.get("vendor") or data.get("vendor") or "The vendor"
    return f"{vendor}'s own {what} preset{src}, unchanged, for {e['used_for']}."


def describe(rel, text, sources_text=None):
    """What the file says it does, in one sentence ('' when its header gives none).
    `sources_text`: the SOURCES.json beside the file, for a vendor file with no header of ours."""
    name = os.path.basename(rel)
    if sources_text is not None:
        v = vendor_entry(sources_text, name)
        if v:
            return first_sentence(v)
    if rel.endswith(".html"):
        m = re.search(r"<!--(.*?)-->", text, re.S)
        paras = [" ".join(m.group(1).split())] if m else []
        return first_sentence(strip_name(pick_paragraph(paras, name), name))
    if rel.endswith(".md"):
        return markdown_summary(text)
    if rel.endswith(".json"):
        try:
            data = json.loads(text)
        except ValueError:
            return ""
        if isinstance(data, dict):
            for key in ("_about", "about", "description", "_comment"):
                if isinstance(data.get(key), str):
                    return first_sentence(data[key])
        return ""
    if rel.endswith(".py"):
        paras = docstring_paragraphs(text) or comment_paragraphs(text)
    elif rel.endswith((".radiantConfig", ".ini", ".cfg")):
        paras = comment_paragraphs(text, ("#", ";"))
    else:                                                    # .sh .R .txt .tsv .yaml .workflow
        paras = comment_paragraphs(text)
    return first_sentence(strip_name(pick_paragraph(paras, name), name))


def usable(desc, rel):
    """A description says what the file does: a few words, not only a name or a usage line."""
    if not desc:
        return False, "no header"
    words = [w for w in desc.split() if re.search(r"[A-Za-z]", w)]
    stem = os.path.splitext(os.path.basename(rel))[0].lower()
    if len(words) < 4:
        return False, "the header is only a name or a label"
    if re.match(r"(?i)(usage|copyright|license|spdx|todo|fixme)\b", desc):
        return False, "the header is a usage or licence line"
    if desc.lower().strip(" .:") in (stem, os.path.basename(rel).lower()):
        return False, "the header is only the file's name"
    return True, ""


def kind(rel):
    ext = os.path.splitext(rel)[1]
    if rel == "SKILL.md":
        return "skill instructions"
    if rel.startswith(".claude-plugin/"):
        return "plugin manifest"
    if rel.startswith("hooks/"):
        return "plugin hook"
    if rel.startswith("presets/"):
        return "engine preset"
    if rel.startswith("references/"):
        return "reference" if ext == ".md" else "reference data"
    return {".py": "Python", ".sh": "shell", ".R": "R", ".json": "data (JSON)",
            ".tsv": "data (table)", ".txt": "data (list)", ".yaml": "data (YAML)",
            ".sbatch": "job template"}.get(ext, "file")


# ---------------------------------------------------------------- no identifier in a public page

IDENTIFIER_WHY = ("its header's first sentence names a person, a login or a submission number "
                  "(the skill's identifier rule), so it is not copied here")


def identifier_rule(repo):
    """The skill's own rule for a real identifier, as text -> [hits]: problems() (staff logins and
    names, real submission numbers) and, when the Core's private list is on this machine, the
    client names. Read from the skill's tests (identifier_rules.py, or the 2.15 guard
    test_no_real_identifiers.py); a tree with neither is an error, never a silent skip."""
    tests = os.path.join(repo, SKILL_REL, "tests")
    sys.path.insert(0, tests)
    try:
        try:
            import identifier_rules as rules
        except ImportError:
            try:
                import test_no_real_identifiers as rules
            except ImportError:
                sys.exit(f"make_inventory: no identifier rule in {tests} (identifier_rules.py or "
                         "test_no_real_identifiers.py): the inventory is public and must be checked")
    finally:
        sys.path.remove(tests)
    names = rules.client_list()[0] if hasattr(rules, "client_list") else None

    def hits(text):
        found = list(rules.problems(OUT_REL, text))
        if names and hasattr(rules, "client_names"):
            found += [f"a client name (private list entry {n})" for n in rules.client_names(text, names)]
        return found
    return hits


# ---------------------------------------------------------------- who names and calls it

def code_text(rel, text):
    """The text of a script with its comments (and Python docstrings) taken out, so a mention
    in a comment ("see run_search.py") is not taken for a call."""
    if rel.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return text
        bits = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mods = [a.name for a in node.names]
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods.append(node.module)
                bits.extend("import " + m for m in mods)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                bits.append(node.value)
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d = ast.get_docstring(node, clean=False)
                if d:
                    docs.add(d)
            if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
                    and isinstance(node.value.value, str):
                docs.add(node.value.value)
        return "\n".join(b for b in bits if b not in docs)
    out = []
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("#"):
            continue
        out.append(re.sub(r"(^|\s)#.*$", "", line))
    return "\n".join(out)


def name_re(name):
    return re.compile(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])")


def doc_sections(text):
    """[(heading, text of the section)] of a Markdown file, code fences included in the text."""
    out, head, buf, fence = [], "", [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
        if not fence and re.match(r"#{1,4} ", s):
            out.append((head, "\n".join(buf)))
            head, buf = s.lstrip("#").strip(), []
            continue
        buf.append(line)
    out.append((head, "\n".join(buf)))
    return out


def command_re(name):
    n = re.escape(name)
    return re.compile(
        r"(?:\b(?:python3?|bash|sh|Rscript|sbatch|source)\s+(?:-\S+\s+)*[\"']?[^\s\"']*?" + n +
        r"(?![\w-])|(?:^|[\s`(\"'])(?:\S*/)?scripts/" + n + r"\s+(?:-{1,2}\w|[a-z]+\b))", re.M)


def short_heading(h):
    h = re.sub(r"[`*]", "", h)
    h = re.sub(r"\s+[—–-]\s+.*$", "", h)
    return h if len(h) <= 48 else h[:46].rsplit(" ", 1)[0] + " …"


# ---------------------------------------------------------------- the inventory

def entries(repo=REPO):
    """One dict per shipped file outside tests/, plus the tests summary."""
    skill = os.path.join(repo, SKILL_REL)
    files = shipped_files(repo)
    texts = {}
    for rel in files:
        with open(os.path.join(skill, rel), "rb") as fh:
            data = fh.read()
        texts[rel] = None if b"\0" in data[:8192] else data.decode("utf-8", "replace")
    docs = ["SKILL.md"] + sorted(f for f in files if f.startswith("references/") and f.endswith(".md"))
    sections = {d: doc_sections(texts[d]) for d in docs if texts.get(d) is not None}
    callers_src = {rel: code_text(rel, texts[rel]) for rel in files
                   if not rel.startswith("tests/") and texts[rel] is not None
                   and rel.endswith((".py", ".sh", ".R"))}
    hook_commands = "\n".join(hook_command_lines(texts[rel]) for rel in files
                              if rel.startswith("hooks/") and rel.endswith(".json"))
    rows = []
    id_hits = identifier_rule(repo)
    for rel in files:
        if rel.startswith("tests/"):
            continue
        name = os.path.basename(rel)
        text = texts[rel] or ""
        src_rel = os.path.join(os.path.dirname(rel), "SOURCES.json").lstrip("/")
        desc = (describe(rel, text, texts.get(src_rel) if src_rel != rel else None)
                if texts[rel] is not None else "")
        ok, why = usable(desc, rel)
        if ok and id_hits(desc):
            ok, why = False, IDENTIFIER_WHY
        rx = name_re(name)
        named, command = [], False
        for d, secs in sections.items():
            if d == rel:
                continue
            heads = [h for h, body in secs if rx.search(body) or rx.search(h)]
            if not heads:
                continue
            if command_re(name).search(texts[d]):
                command = True
            label = os.path.basename(d)
            if d == "SKILL.md":
                shown = list(dict.fromkeys(short_heading(h) for h in heads if h))
                more = f", +{len(shown) - 3} more" if len(shown) > 3 else ""
                named.append(label + (" (" + "; ".join(shown[:3]) + more + ")" if shown else ""))
            else:
                named.append(label)
        stem = os.path.splitext(name)[0]
        imp = re.compile(r"^import " + re.escape(stem) + r"(\.|$)", re.M) if rel.endswith(".py") else None
        callers = sorted(os.path.basename(c) for c, src in callers_src.items()
                         if c != rel and (rx.search(src) or (imp and imp.search(src))))
        hook = bool(rx.search(hook_commands))
        rows.append({"path": rel, "kind": kind(rel), "what": desc if ok else NO_DESCRIPTION,
                     "missing_why": why, "named_in": named,
                     "runs": how_it_runs(rel, command, callers, hook, named),
                     "group": group_of(rel)})
    return rows, tests_summary(files, texts)


def hook_command_lines(text):
    """The "command" strings of a plugin hooks file: what Claude Code actually runs."""
    found = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "command" and isinstance(v, str):
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(json.loads(text))
    return "\n".join(found)


def how_it_runs(rel, command, callers, hook, named):
    shown = ", ".join(callers[:4]) + (f" +{len(callers) - 4} more" if len(callers) > 4 else "")
    if rel == "SKILL.md":
        return "read by Claude when the skill starts"
    if rel.startswith(".claude-plugin/"):
        return "read by Claude Code when it installs or updates the plugin"
    if rel.startswith("hooks/"):
        return "run by Claude Code at the events it names"
    if rel.endswith(".md"):
        return "read by Claude when SKILL.md sends it there" if named else "not named by SKILL.md or a reference"
    data = not rel.endswith((".py", ".sh", ".R"))
    if hook:
        return "run by the plugin hook (hooks/hooks.json)" + (f"; also used by {shown}" if callers else "")
    if command:
        return "run directly (a command in the docs)" + (f"; also used by {shown}" if callers else "")
    if callers:
        return ("read by " if data else "only used by other scripts: ") + shown
    return "named in the docs only" if named else "not named in the docs or by another script"


def group_of(rel):
    path = "/" + rel
    for title, _intro, pats in GROUPS:
        if any(re.search(p, rel) or re.search(p, path) for p in pats):
            return title
    return OTHER[0]


def tests_summary(files, texts):
    tests = [f for f in files if f.startswith("tests/")]
    test_files = [f for f in tests if re.match(r"tests/test_[^/]+\.py$", f)]
    methods = sum(len(re.findall(r"(?m)^\s+def test_\w+", texts[f] or "")) for f in test_files)
    fixtures = [f for f in tests if f.startswith("tests/fixtures/")]
    helpers = [f for f in tests if f not in test_files and f not in fixtures]
    return {"files": len(tests), "test_files": len(test_files), "methods": methods,
            "fixtures": len(fixtures), "helpers": len(helpers)}


def cell(s):
    """A table cell: no row break, no column break, and a `<word>` shown, not read as a tag."""
    parts = s.replace("|", "\\|").replace("\n", " ").split("`")
    # outside `code` only: inside it GitHub shows "&lt;" as it is, and shows "<" anyway
    return "`".join(p if i % 2 else p.replace("<", "&lt;") for i, p in enumerate(parts))


def render(repo=REPO):
    rows, t = entries(repo)
    version = json.loads(read(os.path.join(repo, SKILL_REL, ".claude-plugin", "plugin.json")))["version"]
    by_group = collections.OrderedDict((g[0], []) for g in GROUPS + (OTHER,))
    for r in rows:
        by_group[r["group"]].append(r)
    intro = {g[0]: g[1] for g in GROUPS + (OTHER,)}
    n_missing = sum(r["what"] == NO_DESCRIPTION for r in rows)
    out = [
        "# What's in the skill",
        "",
        "<!-- GENERATED by tools/make_inventory.py from each file's own header. Do not edit by "
        "hand: change the file's header, then run `python3 tools/make_inventory.py`. -->",
        "",
        f"Every file the skill `ucdavis-proteomics-core-pipeline` ships (version {version}, under "
        f"`{SKILL_REL}/`), grouped by the job it does. **What it does** is the first sentence of "
        "the file's own header, so the file is the one place it is said. **Named in** lists where "
        "SKILL.md (with its steps) and the references mention it. **How it runs** says whether the "
        "instructions run it as a command, or only other scripts use it: a script that names it "
        "in its code (a call, an import or a file it reads; comments do not count). Both are "
        "found by searching the skill's text, not written by hand, so a script that names a file "
        "only in a message is listed as using it.",
        "",
        f"{len(rows)} files, plus the tests (below)." + (
            f" {n_missing} file(s) say *{NO_DESCRIPTION}*: their header does not yet say what "
            "they do." if n_missing else ""),
        "",
    ]
    out.append("Jump to: " + " · ".join(
        f"[{g}](#{re.sub(r'[^a-z0-9 -]', '', g.lower()).replace(' ', '-')})"
        for g, rs in by_group.items() if rs) + " · [Tests](#tests)")
    out.append("")
    for g, rs in by_group.items():
        if not rs:
            continue
        out += [f"## {g}", "", intro[g], "",
                "| File | Kind | What it does | Named in | How it runs |",
                "|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: (r["path"].count("/") > 0, r["path"])):
            out.append("| `{}` | {} | {} | {} | {} |".format(
                r["path"], r["kind"], cell(r["what"]),
                cell("; ".join(r["named_in"])) or "–", cell(r["runs"])))
        out.append("")
    out += ["## Tests", "",
            f"`tests/`: {t['files']} files: {t['test_files']} test files holding {t['methods']} "
            f"test methods, {t['helpers']} shared helpers and {t['fixtures']} fixture files. "
            "Standard library only; run them with "
            f"`python3 -m unittest discover -s {SKILL_REL}/tests`.", ""]
    text = "\n".join(out)
    id_hits = identifier_rule(repo)
    left = [line for line in text.splitlines() if id_hits(line)]
    if left:
        sys.exit(f"make_inventory: {len(left)} line(s) of the inventory hold an identifier "
                 "(a heading or a name in the docs); fix the source text, never this page")
    return text, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=REPO, help="the repository (default: the one holding tools/)")
    ap.add_argument("--out", help=f"default: <root>/{OUT_REL}")
    ap.add_argument("--check", action="store_true", help="compare with the file, write nothing")
    ap.add_argument("--missing", help="write the files whose header gives no description here")
    a = ap.parse_args()
    out = a.out or os.path.join(a.root, OUT_REL)
    text, rows = render(a.root)
    if a.missing:
        with open(a.missing, "w", encoding="utf-8") as fh:
            miss = [r for r in rows if r["what"] == NO_DESCRIPTION]
            fh.write(f"# Files under {SKILL_REL}/ whose header gives no usable one-line "
                     f"description ({len(miss)} of {len(rows)}), from tools/make_inventory.py\n")
            for r in miss:
                fh.write(f"{r['path']}\t{r['missing_why']}\n")
    if a.check:
        try:
            current = read(out)
        except FileNotFoundError:
            current = None
        if current != text:
            sys.exit(f"{out} is out of date: run python3 tools/make_inventory.py")
        print(f"{out} is current ({len(rows)} files)")
        return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {out} ({len(rows)} files)")


if __name__ == "__main__":
    main()
