import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_root_mfa as c

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "sample_data")


class TestRootMfa(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(c.evaluate({"AccountMFAEnabled": 1})["result"], "PASS")

    def test_fail(self):
        self.assertEqual(c.evaluate({"AccountMFAEnabled": 0})["result"], "FAIL")

    def test_missing_field_is_an_error_not_a_pass(self):
        with self.assertRaises(ValueError):
            c.evaluate({})

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "e.json")
            self.assertEqual(c.main(["--sample", os.path.join(SAMPLES, "root_summary_pass.json"), "--out", out]), 0)
            self.assertEqual(c.main(["--sample", os.path.join(SAMPLES, "root_summary_fail.json"), "--out", out]), 1)
            self.assertEqual(c.main(["--sample", os.path.join(d, "missing.json"), "--out", out]), 2)


if __name__ == "__main__":
    unittest.main()
