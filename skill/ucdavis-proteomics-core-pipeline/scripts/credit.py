#!/usr/bin/env python3
"""
credit.py -- who prepared a report and which AI model helped: the ONE writer and the ONE reader of
the "Prepared by" and "AI assistance" lines in the report header, the README and the Methods.

  python3 credit.py record <session dir>     write <session>/output/credit.json from the records
  python3 credit.py show <session dir>       the lines as the documents will carry them (JSON)

Nothing in it is typed. Each part is read from a record, and a part no record holds is left out
(the line is not written, never filled in):

  Prepared by    the Core staff member running `record` (the login on this computer), and only
                 under the name on their line of the Core's staff file (`credit: <name>`,
                 staff.credit_for): the file is a Core admin's, and the name is there because the
                 person agreed to it. No `credit:`, no usable staff file, or not Core staff: no
                 "Prepared by" line. The login itself is never written here, nor why the list
                 gave no name (that can hold logins: it is printed to whoever ran `record`).
                 A name is checked against the list again each time the record is read. The first person
                 recorded stays (`--replace` names whoever runs it now).
  AI assistance  the model ids in the session's saved conversations (logs/conversation/*.jsonl,
                 save_transcript.py: what Claude Code itself wrote on each assistant message), in
                 the order first seen -- so a session that changed model lists each -- with the
                 skill version(s) that recorded it. Another agent leaves no such record: no model
                 is named.

The conversation must be saved before the line can name a model: `save_transcript.py <S>` (in
hive_remote mode `save_transcript.py --hive "$S"` on the driving computer), then `record`. The
report (make_analysis_html.py), the README (session_docs.py, at finalize) and the Methods
(make_methods.py --session) each call refresh() first, so a conversation saved since is counted.

The record is client-facing (it holds only what the documents print). The delivery scan
(staff.leak_scan) looks for staff names in a decision's text, not here: this is the one place a
staff name is meant to be.

Never fails a step: a session it cannot read or write gives no lines, and one line on stderr.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA = "report_credit"
RECORD = os.path.join("output", "credit.json")
CONV_DIR = os.path.join("logs", "conversation")
AFFILIATION = "UC Davis Proteomics Core"
SKILL_LABEL = "the UC Davis Proteomics Core pipeline skill"
MODEL_SOURCE = ("the model id on each assistant message of the session's saved conversations "
                "(logs/conversation, save_transcript.py)")
#: Claude Code's own placeholders for a message no model wrote.
NOT_MODELS = ("<synthetic>", "synthetic", "unknown", "")
# A model id as a document may print it: letters, digits, . _ - only, with the tail a cloud
# provider adds (":0", "@20250514"). No "/", no other ":" or "@": nothing that reads as a link
# or an address -- the id comes from a transcript, and lands in client documents.
_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,79}(?::\d{1,3}|@\d{8})?$")
#: The record's one reason for naming nobody: no login, path or list owner in it (staff.
#: credit_for's own reason can hold them, and goes to whoever ran `record`, not into the record).
NO_PREPARER = ("nobody is named: whoever ran credit.py record has no usable `credit:` name on "
               "the Core staff list")
_FAMILIES = ("opus", "sonnet", "haiku", "fable", "mythos")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def model_name(model_id):
    """A Claude model id as its name ("claude-opus-5-5" -> "Claude Opus 5.5",
    "claude-3-5-sonnet-20241022" -> "Claude 3.5 Sonnet"), or None for an id of another shape --
    then the id alone is shown."""
    mid = re.sub(r"\[[^\]]*\]$", "", model_id or "")              # a context-window tag
    mid = re.sub(r"^(?:[a-z]{2,6}\.)?anthropic\.", "", mid)        # a cloud provider's prefix
    while True:                                                   # its tails: -v1:0, @date, -date
        cut = re.sub(r"(?::\d{1,3}|[-@]\d{8}|-latest|-v\d{1,2})$", "", mid)
        if cut == mid:
            break
        mid = cut
    fam = "|".join(_FAMILIES)
    m = re.match(rf"^claude-({fam})-(\d{{1,2}})(?:-(\d{{1,2}}))?$", mid)
    if m:
        return (f"Claude {m.group(1).capitalize()} {m.group(2)}"
                + (f".{m.group(3)}" if m.group(3) else ""))
    m = re.match(rf"^claude-(\d{{1,2}})(?:-(\d{{1,2}}))?-({fam})$", mid)
    if m:
        return (f"Claude {m.group(1)}" + (f".{m.group(2)}" if m.group(2) else "")
                + f" {m.group(3).capitalize()}")
    return None


def clean_id(model_id):
    """The id as shown: without Claude Code's context-window tag ("claude-opus-5-5[1m]")."""
    return re.sub(r"\[[^\]]*\]$", "", model_id or "").strip()


def models_in(session_dir):
    """The models that wrote the session's saved conversations -> [{"model_id", "model", "first",
    "last"}], in the order first seen (by timestamp, then file). A line that is not an assistant
    message with a model id is passed over; nothing here trusts Claude Code's format."""
    seen = {}
    for path in sorted(glob.glob(os.path.join(session_dir, CONV_DIR, "*.jsonl"))):
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for raw in fh:
                if '"model"' not in raw:
                    continue
                try:
                    e = json.loads(raw)
                except ValueError:
                    continue
                msg = e.get("message") if isinstance(e, dict) else None
                if e.get("type") != "assistant" or not isinstance(msg, dict):
                    continue
                mid = msg.get("model")
                if not isinstance(mid, str) or mid.strip().lower() in NOT_MODELS:
                    continue
                mid = clean_id(mid)
                if not _MODEL_ID.match(mid):
                    continue
                ts = e.get("timestamp") if isinstance(e.get("timestamp"), str) else None
                rec = seen.setdefault(mid, {"model_id": mid, "model": model_name(mid),
                                            "first": ts, "last": ts})
                if ts:
                    rec["first"] = min(rec["first"] or ts, ts)
                    rec["last"] = max(rec["last"] or ts, ts)
    return sorted(seen.values(), key=lambda r: (r["first"] is None, r["first"] or ""))


def _skill_version():
    try:
        import skill_version as sv
        v = sv.skill_version()
        return None if v == sv.UNKNOWN else v
    except Exception:                              # no version is a part left out, not a failure
        return None


def _ts(v):
    return v if isinstance(v, str) and re.match(r"^\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:?\d\d)?$", v) else None


def _checked(rec):
    """A record as read from disk, holding only what this script could have written: the session
    folder is group-writable, and what is here is printed in client documents. A preparer whose
    name is not a person's name -- or, where the Core staff list can be read, is no longer a
    `credit:` name on it (consent withdrawn, or a name written in by hand) -- is dropped; so is a
    model id of another shape. The model's name is always derived again from its id."""
    import staff
    pb = rec.get("prepared_by")
    name = pb.get("name") if isinstance(pb, dict) else None
    if not staff.is_credit_name(name):
        name = None
    else:
        try:
            listed, _ = staff.credit_names()
        except Exception:
            listed = None
        if listed is not None and name not in listed.values():
            name = None
    ai = []
    for m in rec.get("ai") if isinstance(rec.get("ai"), list) else []:
        mid = m.get("model_id") if isinstance(m, dict) else None
        if isinstance(mid, str) and _MODEL_ID.match(mid) and mid not in [x["model_id"] for x in ai]:
            ai.append({"model_id": mid, "model": model_name(mid),
                       "first": _ts(m.get("first")), "last": _ts(m.get("last"))})
    vs = rec.get("skill_versions")
    return {"prepared_by_name": name, "ai": ai,
            "skill_versions": [v for v in (vs if isinstance(vs, list) else [])
                               if isinstance(v, str) and re.match(r"^\d+(?:\.\d+){1,3}[\w.+-]{0,20}$", v)],
            "recorded": _ts(rec.get("recorded"))}


def load(session_dir):
    """The session's credit record as written by this script (_checked), or {} when there is
    none (or it is not one)."""
    try:
        with open(os.path.join(session_dir, RECORD), encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(rec, dict) or rec.get("schema") != SCHEMA:
        return {}
    c = _checked(rec)
    return _shape(c["prepared_by_name"], c["ai"], c["skill_versions"], c["recorded"])


PREPARER_SOURCE = ("the Core staff list's `credit:` name for the staff member who ran "
                   "credit.py record")


def _shape(name, ai, versions, recorded):
    return {"schema": SCHEMA,
            "prepared_by": ({"name": name, "affiliation": AFFILIATION, "source": PREPARER_SOURCE}
                            if name else None),
            "no_preparer_because": None if name else NO_PREPARER,
            "ai": ai, "ai_source": MODEL_SOURCE, "skill_versions": versions,
            "recorded": recorded or now()}


def _merge_models(old, new):
    """Models of an earlier record kept beside those read now (a conversation saved on another
    computer may not be in this copy of the session)."""
    by = {m["model_id"]: dict(m) for m in old}
    for m in new:
        o = by.get(m["model_id"])
        if o is None:
            by[m["model_id"]] = dict(m)
            continue
        firsts = [x for x in (o.get("first"), m.get("first")) if x]
        lasts = [x for x in (o.get("last"), m.get("last")) if x]
        o.update(first=min(firsts) if firsts else None, last=max(lasts) if lasts else None)
    return sorted(by.values(), key=lambda r: (r.get("first") is None, r.get("first") or ""))


def build(session_dir, preparer=True, replace=False):
    """The record as the session's records give it now -> (record, why nobody is named or None:
    for whoever runs this, never for the record). `preparer`: look up who runs this (record:
    yes; refresh: no -- a document being rendered names nobody new)."""
    old = load(session_dir)
    name = (old.get("prepared_by") or {}).get("name")
    why = None
    if preparer and (replace or not name):
        import staff
        try:
            name, why = staff.credit_for()
        except Exception as e:                     # the list could not be looked at: nobody
            name, why = None, f"{type(e).__name__}: {e}"
    versions = list(old.get("skill_versions") or [])
    v = _skill_version()
    if v and v not in versions:
        versions.append(v)
    return _shape(name, _merge_models(old.get("ai") or [], models_in(session_dir)), versions,
                  old.get("recorded")), why


def _same(a, b):
    drop = ("recorded", "updated")
    return ({k: v for k, v in a.items() if k not in drop}
            == {k: v for k, v in b.items() if k not in drop})


def write(session_dir, rec):
    import safe_write
    out = os.path.join(session_dir, RECORD)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    safe_write.write_file(out, json.dumps(rec, indent=2, ensure_ascii=False) + "\n", 0o664)
    return out


def _on_disk(session_dir):
    try:
        with open(os.path.join(session_dir, RECORD), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, TypeError):
        return None


def record(session_dir, replace=False):
    """Write the record (credit.py record). -> (the record, why nobody is named or None)."""
    rec, why = build(session_dir, preparer=True, replace=replace)
    disk = _on_disk(session_dir)
    if not (isinstance(disk, dict) and _same(rec, disk)):
        rec["updated"] = now()
        write(session_dir, rec)
    return rec, why


def refresh(session_dir):
    """What a document being rendered calls: the record with any conversation saved since, written
    back when it changed (or when what is on disk is not what this script wrote). Names nobody
    new, makes no record where `record` never ran and nothing is known, and never raises.
    -> the record ({} when there is nothing to say)."""
    try:
        if not session_dir or not os.path.isdir(session_dir):
            return {}
        disk = _on_disk(session_dir)
        rec, _ = build(session_dir, preparer=False)
        if disk is None and not rec["ai"]:
            return {}
        if not (isinstance(disk, dict) and _same(rec, disk)):
            rec["updated"] = now()
            try:
                write(session_dir, rec)
            except OSError as e:
                sys.stderr.write(f"[credit] {RECORD} not updated ({e.strerror or e}); the "
                                 "document still carries what the records give\n")
        return rec
    except Exception as e:                          # a credit line never costs a document
        sys.stderr.write(f"[credit] no credit lines ({type(e).__name__}: {e})\n")
        return {}


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def prepared_text(rec):
    """"<name>, UC Davis Proteomics Core", or None."""
    pb = rec.get("prepared_by") if isinstance(rec, dict) else None
    if not isinstance(pb, dict) or not pb.get("name"):
        return None
    return f"{pb['name']}, {pb.get('affiliation') or AFFILIATION}"


def ai_text(rec):
    """"Claude Opus 5.5 (claude-opus-5-5), running the ... skill v2.15.1", or None when no model
    is recorded."""
    ms = [m for m in (rec.get("ai") or []) if isinstance(m, dict) and m.get("model_id")] \
        if isinstance(rec, dict) else []
    if not ms:
        return None
    names = [f"{m['model']} ({m['model_id']})" if m.get("model") else m["model_id"] for m in ms]
    vs = [v for v in (rec.get("skill_versions") or []) if isinstance(v, str)]
    skill = SKILL_LABEL + (" v" + _join(vs) if vs else "")
    return f"{_join(names)}, running {skill}"


def facts(rec):
    """[("Prepared by", text), ("AI assistance", text)]: only the lines the record supports."""
    return [(k, v) for k, v in (("Prepared by", prepared_text(rec)),
                                ("AI assistance", ai_text(rec))) if v]


def sentence(rec):
    """The Methods' sentence, or None when the record supports neither part."""
    who, ai = prepared_text(rec), ai_text(rec)
    if who and ai:
        return f"The data analysis and report were prepared by {who}, with AI assistance from {ai}."
    if who:
        return f"The data analysis and report were prepared by {who}."
    if ai:
        return f"The data analysis and report were prepared with AI assistance from {ai}."
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="write <session>/output/credit.json from the records")
    r.add_argument("session")
    r.add_argument("--replace", action="store_true",
                   help="name whoever runs this now as the preparer (default: the first stays)")
    s = sub.add_parser("show", help="the lines as the documents carry them")
    s.add_argument("session")
    a = ap.parse_args(argv)
    sd = os.path.abspath(a.session)
    if not os.path.isdir(sd):
        print(json.dumps({"ok": False, "error": f"no session folder {a.session!r}"}))
        return 0
    why = None
    try:
        if a.cmd == "record":
            rec, why = record(sd, a.replace)
        else:
            rec = load(sd)
    except Exception as e:                          # never fails a step
        print(json.dumps({"ok": False, "error": f"{RECORD} not written: {type(e).__name__}: {e}"}))
        return 0
    out = {"ok": True, "record": os.path.join(sd, RECORD) if rec else None,
           "lines": dict(facts(rec)), "methods_sentence": sentence(rec)}
    if rec and not prepared_text(rec):
        # the detail (it can name a login or the list's path) is for whoever ran this only
        out["no_preparer_because"] = why or rec.get("no_preparer_because")
    if rec and not ai_text(rec):
        out["ai_note"] = ("no model is named: no saved conversation holds a model id (save it "
                          "first: save_transcript.py <session>, or --hive \"$S\" in hive_remote "
                          "mode; another agent leaves none)")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
