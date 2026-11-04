import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECK = ROOT / "bench_v2" / "check_results.py"


def row(**kw):
    d = {
        "run_id": "run-1",
        "i": 0,
        "case": "case-a",
        "mode": "model",
        "ok": True,
        "status": 200,
        "ms": 10,
        "ttft_ms": 5,
        "false_success": False,
        "text_len": 7,
    }
    d.update(kw)
    return d


class CheckResultsTests(unittest.TestCase):
    def run_check(self, rows, *extra):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = pathlib.Path(tmp.name) / "run.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        out = pathlib.Path(tmp.name) / "summary.json"
        cmd = [sys.executable, str(CHECK), "--jsonl", str(p), "--json-out", str(out), *extra]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        summary = json.loads(out.read_text(encoding="utf-8"))
        return proc, summary

    def test_pass(self):
        proc, s = self.run_check([row()], "--expect-n", "1", "--strict")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(s["verdict"], "PASS")
        self.assertEqual(s["rows"], 1)
        self.assertEqual(s["false_success_rate"], 0.0)

    def test_false_success_fails_strict(self):
        proc, s = self.run_check([row(false_success=True)], "--strict")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(s["verdict"], "FAIL")
        self.assertIn("false_success: 1", s["fails"])

    def test_duplicate_key_fails(self):
        proc, s = self.run_check([row(), row()], "--strict")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("duplicate (run_id,i): 1", s["fails"])

    def test_empty_ok_text_fails(self):
        proc, s = self.run_check([row(text_len=0)], "--strict")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ok but empty text: 1", s["fails"])

    def test_expect_n_mismatch_fails(self):
        proc, s = self.run_check([row()], "--expect-n", "2", "--strict")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("count 1 != expect 2", s["fails"])


if __name__ == "__main__":
    unittest.main()
