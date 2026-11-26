#!/usr/bin/env python3
"""
The "Prepared by" and "AI assistance" lines are generated from records, never typed (credit.py).

  * the model named is the id Claude Code wrote on each assistant message of the session's saved
    conversations: every model, in the order first seen; a placeholder is no model;
  * the staff member is named only under the `credit:` name on their line of the Core's trusted
    staff file -- no line, no name; the login is never written;
  * a part no record holds is left out of the report header, the READMEs and the Methods;
  * the delivery's staff-name scan does not trip on the one place a name is meant to be.

Hermetic: temp dirs and synthetic logins and names (jdoe, "Jane Doe").
"""
import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
sys.path.insert(0, SCRIPTS)

import credit  # noqa: E402
import staff  # noqa: E402

ME = getpass.getuser()
OPUS, SONNET = "claude-opus-5-5", "claude-sonnet-5-5"


def msg(model, ts, kind="assistant"):
    return json.dumps({"type": kind, "timestamp": ts,
                       "message": {"role": kind, "model": model, "content": "x"}})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.s = os.path.join(self.tmp, "session")
        os.makedirs(os.path.join(self.s, "logs", "conversation"))
        os.makedirs(os.path.join(self.s, "output"))
        env = mock.patch.dict(os.environ, {
            staff.STAFF_FILE_ENV: os.path.join(self.tmp, "no_staff_list.txt")})
        env.start()
        self.addCleanup(env.stop)

    def conversation(self, name, *lines):
        with open(os.path.join(self.s, "logs", "conversation", name + ".jsonl"), "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def staff_list(self, text):
        d = os.path.join(self.tmp, "config")
        os.makedirs(d, mode=0o755, exist_ok=True)
        os.chmod(d, 0o755)
        path = os.path.join(d, "core_staff.txt")
        with open(path, "w") as fh:
            fh.write(text)
        os.chmod(path, 0o644)
        os.environ.update({staff.STAFF_FILE_ENV: path, "SKILL_SLACK_TEST_LOOPBACK": "1",
                           "SKILL_CORE_ADMINS": ME})
        return path


class ModelNames(unittest.TestCase):
    def test_a_claude_id_reads_as_its_name(self):
        for mid, name in (("claude-opus-5-5", "Claude Opus 5.5"),
                          ("claude-fable-5-2", "Claude Fable 5.2"),
                          ("claude-opus-4", "Claude Opus 4"),
                          ("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5"),
                          ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
                          ("claude-opus-5-5[1m]", "Claude Opus 5.5"),
                          ("us.anthropic.claude-haiku-5-5", "Claude Haiku 5.5"),
                          ("us.anthropic.claude-sonnet-4-20250514-v1:0", "Claude Sonnet 4"),
                          ("claude-opus-4@20250514", "Claude Opus 4")):
            self.assertEqual(credit.model_name(mid), name, mid)

    def test_another_shape_has_no_made_up_name(self):
        for mid in ("gpt-5", "gemini-3-pro", "claude-next", "claude-sonnet-4-20250514-x", ""):
            self.assertIsNone(credit.model_name(mid), mid)


class Models(Base):
    def test_every_model_in_the_order_first_seen(self):
        self.conversation("b", msg(SONNET, "2026-11-25T10:00:00Z"), msg(OPUS, "2026-11-25T11:00:00Z"))
        self.conversation("a", msg(OPUS + "[1m]", "2026-11-24T09:00:00Z"),
                          msg("<synthetic>", "2026-11-24T09:01:00Z"),
                          msg(OPUS, "2026-11-24T09:02:00Z", kind="user"),
                          "not json", json.dumps({"type": "assistant", "message": "text"}))
        got = credit.models_in(self.s)
        self.assertEqual([m["model_id"] for m in got], [OPUS, SONNET])
        self.assertEqual(got[0]["first"], "2026-11-24T09:00:00Z")
        self.assertEqual(got[0]["last"], "2026-11-25T11:00:00Z")
        self.assertEqual(got[0]["model"], "Claude Opus 5.5")

    def test_an_id_that_reads_as_a_link_or_an_address_is_no_model(self):
        self.conversation("a", *(msg(m, "2026-11-25T10:00:00Z") for m in (
            "http://evil.example/x", "foo@bar.com", "a/b", "x:y", "[x](y)", "<b>", "a b")),
            msg("us.anthropic.claude-sonnet-4-20250514-v1:0", "2026-11-25T10:00:01Z"))
        self.assertEqual([m["model_id"] for m in credit.models_in(self.s)],
                         ["us.anthropic.claude-sonnet-4-20250514-v1:0"])

    def test_no_saved_conversation_names_no_model(self):
        self.assertEqual(credit.models_in(self.s), [])
        rec, why = credit.record(self.s)
        self.assertIsNone(credit.ai_text(rec))
        self.assertEqual(credit.facts(rec), [])
        self.assertIsNone(credit.sentence(rec))


class PreparedBy(Base):
    def test_without_a_staff_list_nobody_is_named(self):
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        rec, why = credit.record(self.s)
        self.assertIsNone(rec["prepared_by"])
        self.assertEqual(rec["no_preparer_because"], credit.NO_PREPARER)
        self.assertIn("does not exist", why)                # the detail: to whoever ran it
        self.assertEqual([k for k, _ in credit.facts(rec)], ["AI assistance"])

    def test_the_credit_name_on_the_staff_list_is_the_line(self):
        self.staff_list(f"# staff\n{ME}  credit: Jane Doe   # agreed 2026-11-25\nasmith\n")
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        rec, why = credit.record(self.s)
        self.assertEqual(credit.prepared_text(rec), "Jane Doe, UC Davis Proteomics Core")
        with open(os.path.join(self.s, credit.RECORD)) as fh:
            text = fh.read()
        self.assertNotIn(ME, text.replace("Jane Doe", ""))  # the login is never written
        self.assertNotIn(self.tmp, text)                    # nor where the staff list is
        self.assertEqual(
            credit.sentence(rec),
            "The data analysis and report were prepared by Jane Doe, UC Davis Proteomics Core, "
            f"with AI assistance from {credit.ai_text(rec)}.")

    def test_staff_without_a_credit_name_are_not_named(self):
        self.staff_list(f"{ME}  # no credit asked for\nasmith credit: Ann Smith\n")
        rec, why = credit.record(self.s)
        self.assertIsNone(rec["prepared_by"])
        self.assertIn("no `credit:` name", why)
        self.assertEqual(rec["no_preparer_because"], credit.NO_PREPARER)

    def test_a_credit_that_is_not_a_persons_name_names_nobody(self):
        for bad in ("<b>Jane</b>", "Jane [Doe](x)", "Jane_Doe", "Jane & Doe", "Jane Doe https://x.example",
                    "J" * 90, "1234"):
            self.staff_list(f"{ME} credit: {bad}\n")
            self.assertEqual(staff.credit_names()[0], {}, bad)
        self.staff_list(f"{ME}  # credit: Jane Doe\n")          # in a comment: not a credit
        self.assertEqual(staff.credit_names()[0], {})
        self.staff_list(f"{ME} pre-credit: Jane Doe\n")          # another word: not a credit
        self.assertEqual(staff.credit_names()[0], {})
        self.staff_list(f"{ME} credit: Jose\u0301 Doe\n")        # a decomposed accent
        self.assertEqual(staff.credit_names()[0], {ME.lower(): "Jos\u00e9 Doe"})
        for good in ("Jane Doe", "Jean-Luc O'Neil", "María J. Pérez", "Jane Doe, Ph.D.",
                     "Ai Nguyen"):
            self.staff_list(f"{ME} credit = {good}\n")
            self.assertEqual(staff.credit_names()[0], {ME.lower(): good}, good)

    def test_a_staff_list_that_is_not_trusted_names_nobody_and_no_login_is_recorded(self):
        path = self.staff_list(f"{ME} credit: Jane Doe\n")
        os.chmod(path, 0o666)
        self.assertEqual(staff.credit_for()[0], None)
        rec, why = credit.record(self.s)
        self.assertIsNone(rec["prepared_by"])
        self.assertIn("not trusted", why)
        os.environ["SKILL_CORE_ADMINS"] = "someadmin"      # the reason now names two logins
        os.chmod(path, 0o644)
        rec, why = credit.record(self.s)
        self.assertIn(ME, why)
        self.assertIn("someadmin", why)
        with open(os.path.join(self.s, credit.RECORD)) as fh:
            text = fh.read()
        for word in (ME, "someadmin", self.tmp, "core_staff"):
            self.assertNotIn(word, text)

    def test_the_first_preparer_stays_unless_replaced(self):
        self.staff_list(f"{ME} credit: Jane Doe\nasmith credit: Ann Smith\n")
        credit.record(self.s)
        self.staff_list(f"{ME} credit: Ann Smith\nasmith credit: Jane Doe\n")
        self.assertEqual(credit.record(self.s)[0]["prepared_by"]["name"], "Jane Doe")
        self.assertEqual(credit.record(self.s, replace=True)[0]["prepared_by"]["name"], "Ann Smith")

    def test_a_name_no_longer_on_the_list_is_dropped_when_the_record_is_read(self):
        self.staff_list(f"{ME} credit: Jane Doe\n")
        credit.record(self.s)
        self.staff_list("asmith credit: Ann Smith\n")       # consent withdrawn
        self.assertIsNone(credit.load(self.s)["prepared_by"])
        self.assertEqual(credit.facts(credit.refresh(self.s)), [])
        with open(os.path.join(self.s, credit.RECORD)) as fh:
            self.assertNotIn("Jane", fh.read())             # and written back without it

    def test_a_record_edited_by_hand_prints_nothing_this_script_did_not_write(self):
        self.staff_list(f"{ME} credit: Jane Doe\n")
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        credit.record(self.s)
        path = os.path.join(self.s, credit.RECORD)
        with open(path) as fh:
            rec = json.load(fh)
        rec["prepared_by"] = {"name": "Anyone **bold** [x](http://evil.example)",
                              "affiliation": "Evil [Corp](http://evil.example)"}
        rec["ai"] = [{"model_id": OPUS, "model": "The Best [Model](http://evil.example)"},
                     {"model_id": "http://evil.example/x"}, {"model_id": ["x"]}, 5]
        rec["skill_versions"] = ["2.15.1", "[v](http://evil.example)", 7]
        with open(path, "w") as fh:
            json.dump(rec, fh)
        for got in (credit.load(self.s), credit.refresh(self.s), credit.record(self.s)[0]):
            text = json.dumps([credit.facts(got), credit.sentence(got)])
            self.assertNotIn("evil", text)
            self.assertNotIn("bold", text)
            self.assertIn(f"Claude Opus 5.5 ({OPUS})", text)
        os.environ[staff.STAFF_FILE_ENV] = os.path.join(self.tmp, "gone.txt")   # no list to ask
        rec["prepared_by"] = {"name": "Ann Smith"}          # a name's shape: kept, as written
        with open(path, "w") as fh:
            json.dump(rec, fh)
        self.assertEqual(credit.prepared_text(credit.load(self.s)),
                         "Ann Smith, UC Davis Proteomics Core")


class Refresh(Base):
    def test_a_render_makes_no_record_from_nothing_and_names_nobody(self):
        self.staff_list(f"{ME} credit: Jane Doe\n")
        self.assertEqual(credit.refresh(self.s), {})
        self.assertFalse(os.path.exists(os.path.join(self.s, credit.RECORD)))
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        rec = credit.refresh(self.s)
        self.assertIsNone(rec["prepared_by"])               # only `record` names a person
        self.assertEqual([k for k, _ in credit.facts(rec)], ["AI assistance"])

    def test_a_conversation_saved_later_is_counted_and_an_earlier_model_is_kept(self):
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        credit.record(self.s)
        os.remove(os.path.join(self.s, "logs", "conversation", "a.jsonl"))
        self.conversation("b", msg(SONNET, "2026-11-25T12:00:00Z"))
        rec = credit.refresh(self.s)
        self.assertEqual([m["model_id"] for m in rec["ai"]], [OPUS, SONNET])
        self.assertIn(f"Claude Opus 5.5 ({OPUS}) and Claude Sonnet 5.5 ({SONNET}), running",
                      credit.ai_text(rec))
        self.assertEqual(credit.load(self.s)["ai"], rec["ai"])

    def test_it_never_raises(self):
        self.assertEqual(credit.refresh(os.path.join(self.tmp, "nowhere")), {})
        self.assertEqual(credit.refresh(None), {})
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        for bad in ("[1, 2", '{"schema": "report_credit", "ai": 5, "prepared_by": [1]}',
                    '{"schema": "report_credit", "ai": [{"model_id": ["x"], "first": 3}]}'):
            with open(os.path.join(self.s, credit.RECORD), "w") as fh:
                fh.write(bad)
            rec = credit.refresh(self.s)                    # the bad record costs no line
            self.assertEqual([m["model_id"] for m in rec["ai"]], [OPUS], bad)
        with mock.patch.object(credit, "write", side_effect=OSError(30, "Read-only file system")):
            with open(os.path.join(self.s, credit.RECORD), "w") as fh:
                fh.write("{}")
            self.assertEqual([m["model_id"] for m in credit.refresh(self.s)["ai"]], [OPUS])
        with mock.patch.object(credit, "models_in", side_effect=RuntimeError("x")):
            self.assertEqual(credit.refresh(self.s), {})

    def test_the_cli_never_fails_a_step(self):
        with open(os.path.join(self.s, credit.RECORD), "w") as fh:
            fh.write('{"schema": "report_credit", "ai": [{"model_id": ["x"]}], "recorded": 4}')
        for args in (["record", os.path.join(self.tmp, "nowhere")], ["show", self.s],
                     ["record", self.s]):
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "credit.py"), *args],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            json.loads(r.stdout)


class InTheDocuments(Base):
    def setUp(self):
        super().setUp()
        self.staff_list(f"{ME} credit: Jane Doe\n")
        self.conversation("a", msg(OPUS, "2026-11-25T10:00:00Z"))
        self.rec, why = credit.record(self.s)
        self.who = "Jane Doe, UC Davis Proteomics Core"

    def test_the_report_header(self):
        import make_analysis_html as mah
        facts = dict(mah.session_facts(argparse.Namespace(session=self.s), {}))
        self.assertEqual(facts["Prepared by"], self.who)
        self.assertIn(f"Claude Opus 5.5 ({OPUS})", facts["AI assistance"])
        keys = [k for k, _ in mah.session_facts(argparse.Namespace(session=self.s), {})]
        self.assertLess(keys.index("AI assistance"), keys.index("Report generated"))
        none = dict(mah.session_facts(argparse.Namespace(session=None), {}))
        self.assertNotIn("Prepared by", none)

    def test_the_session_readme(self):
        import session_docs
        text = session_docs.readme_md(session_docs.gather(self.s))
        self.assertIn(f"**Prepared by:** {self.who}", text)
        self.assertIn(f"**AI assistance:** Claude Opus 5.5 ({OPUS})", text)
        self.assertLess(text.index("**Prepared by:**"), text.index("## Start here"))
        os.remove(os.path.join(self.s, credit.RECORD))
        os.remove(os.path.join(self.s, "logs", "conversation", "a.jsonl"))
        self.assertNotIn("Prepared by", session_docs.readme_md(session_docs.gather(self.s)))

    def test_the_delivery_readme(self):
        import core_submission as cs
        summary = {"id": "abc", "internal_id": "PROT_9001", "pi": {}}
        text = cs.build_readme(summary, {"Analysis_Report.html"}, [], credit=credit.facts(self.rec))
        self.assertIn(f"**Prepared by:** {self.who}", text)
        self.assertIn("**AI assistance:** Claude Opus 5.5", text)
        self.assertNotIn("Prepared by:", cs.build_readme(summary, {"Analysis_Report.html"}, []))
        self.assertNotIn("Prepared by:", cs.build_readme(summary, set(), ["a.raw"], mode="raw-only",
                                                        credit=credit.facts(self.rec)))

    def test_the_methods_acknowledgments(self):
        raw = os.path.join(self.tmp, "x.raw")
        open(raw, "w").close()

        def methods(*extra):
            out = os.path.join(self.tmp, "methods.md")
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "make_methods.py"),
                                "--raw", raw, "--out", out, *extra], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(out, encoding="utf-8") as fh:
                return fh.read()
        text = methods("--session", self.s)
        ack = text[text.index("## Acknowledgments"):]
        self.assertIn(credit.sentence(self.rec), ack)
        self.assertIn(f"prepared by {self.who}, with AI assistance from Claude Opus 5.5", ack)
        self.assertNotIn("prepared by", methods())          # no session: no record, no line

    def test_the_delivery_scan_does_not_trip_on_the_credit(self):
        # with the staff member's login and name known to the scan, the credit record and a
        # README carrying the line are clean: the scan reads a decision's text, not this
        readme = os.path.join(self.s, "README.md")
        with open(readme, "w") as fh:
            fh.write(f"**Prepared by:** {self.who}\n")
        with mock.patch.object(staff, "staff_identities",
                               return_value={ME.lower(): "login", "Jane": "name", "Doe": "name"}):
            got = staff.leak_scan(self.s, [(os.path.join(self.s, credit.RECORD), "credit.json"),
                                           (readme, "README.md")])
        self.assertEqual(got["hits"], [])
        self.assertEqual(got["scanned"], 2)
        # and the scan is as strict as before: the same name in a decision's text still holds
        bad = os.path.join(self.s, "de_provenance.json")
        with open(bad, "w") as fh:
            json.dump({"normalization": {"reason": "Jane said to normalise them"}}, fh)
        with mock.patch.object(staff, "staff_identities",
                               return_value={ME.lower(): "login", "Jane": "name", "Doe": "name"}):
            got = staff.leak_scan(self.s, [(bad, "de_provenance.json")])
        self.assertEqual(len(got["hits"]), 1)
        # no key of the credit record is one the scan reads as a decision's text
        with open(os.path.join(self.s, credit.RECORD)) as fh:
            self.assertEqual(list(staff._leak_strings(json.load(fh))), [])


if __name__ == "__main__":
    unittest.main()
