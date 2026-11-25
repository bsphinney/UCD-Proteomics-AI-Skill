#!/usr/bin/env python3
"""
A decision's reason, in the person's own words, never reaches a client file (a staff report,
2026-11-25: a typed reason carried the staff member's name into the report's QC table, AUDIT.md,
the Methods, de_provenance.json and the check's own record, and the delivery went out).

  * `normalization_check.py decide --reason` goes only to the staff-only record; the check record
    (and so de_provenance.json, the Methods, the audit) carries a sentence GENERATED from the
    check: what was chosen, against which default, what the data check raised and recommended;
  * a record written before 2.16 still holds the typed words: the gate's answer (what run_de.R
    copies), the Methods and the audit regenerate the sentence, and `restate` rewrites the record;
  * `core_submission.py deliver` holds a delivery whose files carry text typed for the Core, or a
    staff login or name in a decision's text (staff.leak_scan), naming the file and never the
    words -- and does not mistake a citation of a staff member's paper for a leak.

Hermetic: temp dirs, synthetic logins and names (jdoe / "Jane Doe").
"""
import json
import os
import subprocess
import sys
import unittest
import zipfile
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
for p in (HERE, SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

import experiment_type as et  # noqa: E402
import normalization_check as nc  # noqa: E402
import staff  # noqa: E402
from test_staff_decisions import StaffEnv, check_record  # noqa: E402

TYPED = "yes normalize them -- Jane 2026-11-24, after hearing both earlier batches did"


def old_record(path, sess):
    """A check record as 2.15 `decide` left it: the typed reason in `reason` and `statement`."""
    check_record(path, sess)
    with open(path) as fh:
        rec = json.load(fh)
    rec["experiment_type"] = {"type": "whole_proteome", "label": "whole proteome", "source": "user"}
    rec["decision"] = {"quantities": et.NORMALISED, "source": "user", "by": staff.ROLE,
                       "reason": TYPED,
                       "statement": f"Core staff chose normalised quantities because {TYPED}.",
                       "at": "2026-11-24T22:27:22Z", "default_was": et.NORMALISED,
                       "data_check_tripped": True,
                       "staff_record": os.path.join("logs", nc.STAFF_RECORD)}
    with open(path, "w") as fh:
        json.dump(rec, fh)
    return path


class TheSentenceIsGenerated(unittest.TestCase):
    def rec(self, default=et.NORMALISED, typed=True, **kw):
        r = {"default": {"quantities": default}, "tripped": True, "trips": ["B1 ..."]}
        if typed:
            r["experiment_type"] = {"type": "ip"}
        r.update(kw)
        return r

    def test_it_says_what_was_chosen_against_the_default(self):
        self.assertEqual(nc.statement(et.NORMALISED, self.rec()),
                         "Core staff reviewed the data check's findings and kept the default, "
                         "normalised quantities.")
        self.assertEqual(nc.statement(et.RAW, self.rec()),
                         "Core staff reviewed the data check's findings and chose non-normalised "
                         "(raw) quantities instead of the default (normalised).")
        self.assertEqual(nc.statement(et.RAW, self.rec(typed=False)),
                         "Core staff reviewed the data check's findings and chose non-normalised "
                         "(raw) quantities.")
        self.assertIn("the data check, which raised nothing",
                      nc.statement(et.RAW, self.rec(tripped=False, trips=[])))

    def test_it_says_what_the_check_recommended_when_the_record_can(self):
        r = self.rec(volcano={}, checks={})
        self.assertTrue(nc.statement(et.NORMALISED, r).endswith(
            "; the check had recommended the same."))
        self.assertTrue(nc.statement(et.RAW, r).endswith(
            "; the check had recommended normalised quantities."))

    def test_a_record_too_thin_to_read_still_gives_a_sentence(self):
        for r in ({}, None, {"default": None}, {"volcano": "x", "tripped": True}):
            self.assertIn("Core staff", nc.statement(et.RAW, r))


class TypedWordsStayWithStaff(StaffEnv):
    def setUp(self):
        super().setUp()
        self.staff_list("jdoe")
        self.s = os.path.join(self.tmp, "S")
        self.path = os.path.join(self.s, "output", "norm_check", nc.RECORD)

    def test_decide_writes_them_to_the_staff_record_only(self):
        check_record(self.path, self.s)
        d = nc.decide(self.path, et.NORMALISED, "jdoe", TYPED)["decision"]
        self.assertEqual((d["reason"], d["statement_from"]),
                         (nc.REASON_STAFF_ONLY, nc.STATEMENT_FROM))
        folder = os.path.dirname(self.path)
        for f in os.listdir(folder):
            with open(os.path.join(folder, f), encoding="utf-8") as fh:
                text = fh.read()
            self.assertNotIn("Jane", text, f)
            self.assertNotIn("normalize them", text, f)
        self.assertEqual(staff.read(os.path.join(self.s, "logs", nc.STAFF_RECORD))[0]["reason"],
                         TYPED)

    def test_an_old_record_never_hands_them_on(self):
        import audit_results
        import make_methods
        old_record(self.path, self.s)
        rec = nc.load(self.path)
        self.assertEqual(len(nc.typed_reasons(rec)), 2)
        said = nc.client_statement(rec)
        self.assertEqual(said, "Core staff reviewed the data check's findings and kept the "
                               "default, normalised quantities; the check had recommended the "
                               "same.")
        self.assertNotIn("Jane", nc.summary_md(rec))
        # the Methods and the audit, from a DE record that copied the old check
        prov = {"normalisation": "DIA-NN", "normalization_check": dict(
            rec, status="decided", quantities_applied=et.NORMALISED)}
        self.assertNotIn("Jane", make_methods.de_normalisation_sentence(prov))
        tables = os.path.join(self.tmp, "tables")
        os.makedirs(tables)
        with open(os.path.join(tables, "de_provenance.json"), "w") as fh:
            json.dump(prov, fh)
        findings = []
        audit_results.audit_normalization_check(findings, prov)
        self.assertTrue(findings)
        self.assertNotIn("Jane", json.dumps(findings))
        # the gate's answer is what run_de.R copies into de_provenance.json
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "normalization_check.py"),
                            "gate", "--check", self.path, "--quantities", et.NORMALISED],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Jane", p.stdout)
        self.assertEqual(json.loads(p.stdout)["decision"]["statement"], said)

    def test_restate_rewrites_an_old_record_and_keeps_the_words_for_staff(self):
        old_record(self.path, self.s)
        rec, changed = nc.restate(self.path)
        self.assertTrue(changed)
        self.assertEqual(rec["decision"]["quantities"], et.NORMALISED)
        self.assertEqual(rec["decision"]["at"], "2026-11-24T22:27:22Z")
        folder = os.path.dirname(self.path)
        for f in os.listdir(folder):
            with open(os.path.join(folder, f), encoding="utf-8") as fh:
                self.assertNotIn("Jane", fh.read(), f)
        entries = staff.read(os.path.join(self.s, "logs", nc.STAFF_RECORD))
        self.assertEqual([(e["event"], e["reason"]) for e in entries], [("restate", TYPED)])
        self.assertEqual(nc.restate(self.path)[1], False)          # once is enough
        self.assertEqual(len(staff.read(os.path.join(self.s, "logs", nc.STAFF_RECORD))), 1)


class TheDeliveryScan(StaffEnv):
    def setUp(self):
        super().setUp()
        self.staff_list("jdoe")
        self.s = os.path.join(self.tmp, "S")
        os.makedirs(os.path.join(self.s, "logs"))
        os.makedirs(os.path.join(self.s, "output", "tables"))
        staff.append(os.path.join(self.s, "logs", nc.STAFF_RECORD),
                     {"event": "decide", "by": "jdoe", "account": "jdoe", "reason": TYPED})
        p = mock.patch.object(staff, "staff_identities",
                              lambda extra=(): {"jdoe": "login", "Jane": "name", "Will": "name"})
        p.start()
        self.addCleanup(p.stop)

    def put(self, name, text):
        path = os.path.join(self.s, "output", name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path, name

    def test_typed_text_is_found_by_value_and_never_quoted(self):
        files = [self.put("tables/methods.txt", f"Norm. check: Core staff chose because {TYPED}.\n"),
                 self.put("AUDIT.md", "nothing here\n"),
                 self.put("tables/de_provenance.json", json.dumps({"decision": {"reason": TYPED}}))]
        r = staff.leak_scan(self.s, files)
        self.assertEqual(sorted({h["file"] for h in r["hits"]}),
                         ["tables/de_provenance.json", "tables/methods.txt"])
        self.assertEqual(r["scanned"], 3)
        self.assertNotIn("Jane", json.dumps(r))
        self.assertNotIn("normalize them", json.dumps(r))

    def test_a_staff_name_or_login_in_a_decisions_text(self):
        files = [self.put("tables/a.json", json.dumps({"override": {"reason": "Jane asked for it"}})),
                 self.put("tables/b.json", json.dumps({"x": [{"override_note": "per jdoe"}]})),
                 self.put("tables/c.json", json.dumps({"statement": "Core staff chose raw."}))]
        r = staff.leak_scan(self.s, files)
        self.assertEqual([(h["file"], h["key"]) for h in r["hits"]],
                         [("tables/a.json", "override.reason"),
                          ("tables/b.json", "x[0].override_note")])

    def test_a_citation_of_a_staff_members_paper_is_not_a_leak(self):
        files = [self.put("tables/methods.txt", "Will J, Roe R (2024) J Proteome Res 23:1.\n"),
                 self.put("tables/d.json", json.dumps({"citation": "Will J et al. 2024",
                                                       "reason": "the default will stand",
                                                       "note": "janet's column; jdoes"}))]
        self.assertEqual(staff.leak_scan(self.s, files)["hits"], [])

    def test_an_overrides_reason_is_the_clients_too(self):
        """estimate_params.py writes --override-reason to its staff record AND to the sidecar
        the client gets: that text is no leak, a staff name in it is."""
        staff.append(os.path.join(self.s, "logs", "params.cfg.staff.json"),
                     {"event": "override", "by": "jdoe",
                      "reason": "the Orbitrap was tuned for a narrow tolerance"})
        ok = self.put("tables/params.json", json.dumps({"overrides": {"mass_acc": {
            "reason": "the Orbitrap was tuned for a narrow tolerance"}}}))
        self.assertEqual(staff.leak_scan(self.s, [ok])["hits"], [])
        bad = self.put("tables/params2.json", json.dumps({"overrides": {"mass_acc": {
            "reason": "Jane tuned the Orbitrap for a narrow tolerance"}}}))
        self.assertEqual(len(staff.leak_scan(self.s, [bad])["hits"]), 1)

    def test_a_short_typed_text_is_an_ordinary_phrase(self):
        staff.append(os.path.join(self.s, "logs", nc.STAFF_RECORD),
                     {"event": "decide", "by": "jdoe", "reason": "kept the default"})
        f = self.put("AUDIT.md", "Core staff reviewed the findings and kept the default.\n")
        self.assertEqual(staff.leak_scan(self.s, [f])["hits"], [])

    def test_an_unreadable_staff_record_is_a_problem_never_a_pass(self):
        with open(os.path.join(self.s, "logs", "broken.staff.json"), "w") as fh:
            fh.write("[1]")
        self.assertTrue(staff.leak_scan(self.s, [self.put("AUDIT.md", "x")])["problems"])

    def test_inside_a_delivered_zip_too(self):
        z = os.path.join(self.s, "output", "session.zip")
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("output/AUDIT.md", f"Normalisation choice: because {TYPED}.")
            zf.writestr("output/figure.png", b"\x89PNG")
        r = staff.leak_scan(self.s, [(z, "session.zip")])
        self.assertEqual([h["file"] for h in r["hits"]], ["session.zip!output/AUDIT.md"])

    def test_no_staff_text_and_no_staff_words_scans_nothing(self):
        os.remove(os.path.join(self.s, "logs", nc.STAFF_RECORD))
        with mock.patch.object(staff, "staff_identities", lambda extra=(): {}):
            r = staff.leak_scan(self.s, [self.put("AUDIT.md", "x")])
        self.assertEqual((r["hits"], r["scanned"]), ([], 0))


class DeliverHoldsALeak(StaffEnv):
    def test_deliver_holds_then_passes_once_the_file_is_regenerated(self):
        from test_core_submission import DeliverBase

        class Leak(DeliverBase):
            def runTest(self):
                pass
        t = Leak()
        t.setUp()
        try:
            self.staff_list("jdoe")
            with open(os.path.join(t.output, "tables", "de_provenance.json"), "w") as fh:
                json.dump({"method": "dpc"}, fh)
            nc.ack_legacy(t.session, "jdoe", "a 2.9 analysis whose quantities Jane reviewed")
            methods = os.path.join(t.output, "tables", "methods.txt")
            with open(methods, "w") as fh:
                fh.write("Norm. check: a 2.9 analysis whose quantities Jane reviewed\n")
            rc, out, p = t.deliver()
            self.assertNotEqual(rc, 0, p.stdout)
            self.assertIn("typed for the Core", out["error"])
            self.assertIn("tables/methods.txt", out["error"])
            self.assertIn("no one needs asking", out["hint"])
            self.assertNotIn("Jane", json.dumps(out["leak_scan"]))
            with open(methods, "w") as fh:
                fh.write("Norm. check: Core staff acknowledged this DE.\n")
            rc, out, p = t.deliver()
            self.assertEqual(rc, 0, p.stdout + p.stderr)
            self.assertEqual(out["leak_scan"]["hits"], [])
        finally:
            t.tearDown()


if __name__ == "__main__":
    unittest.main()
