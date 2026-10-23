import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_iam_mfa as c

HERE = os.path.dirname(__file__)
SAMPLES = os.path.join(HERE, "..", "sample_data")


class TestControl(unittest.TestCase):
    def test_pass_when_all_console_users_have_mfa(self):
        users = c.load_sample(os.path.join(SAMPLES, "iam_users_pass.json"))
        r = c.evaluate(users)
        self.assertEqual(r["result"], "PASS")
        self.assertEqual(r["population_in_scope"], 2)

    def test_fail_lists_the_exception(self):
        users = c.load_sample(os.path.join(SAMPLES, "iam_users_fail.json"))
        r = c.evaluate(users)
        self.assertEqual(r["result"], "FAIL")
        self.assertEqual(r["exceptions"], ["carol.example"])

    def test_users_without_console_access_are_out_of_scope(self):
        r = c.evaluate([{"user": "bot", "console_access": False, "mfa_devices": 0}])
        self.assertEqual(r["result"], "PASS")
        self.assertEqual(r["population_in_scope"], 0)

    def test_exit_codes_and_evidence_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "e.json")
            self.assertEqual(c.main(["--sample", os.path.join(SAMPLES, "iam_users_pass.json"), "--out", out]), 0)
            self.assertEqual(c.main(["--sample", os.path.join(SAMPLES, "iam_users_fail.json"), "--out", out]), 1)
            with open(out) as f:
                self.assertEqual(json.load(f)["result"], "FAIL")
            self.assertEqual(c.main(["--sample", os.path.join(d, "missing.json"), "--out", out]), 2)


if __name__ == "__main__":
    unittest.main()
