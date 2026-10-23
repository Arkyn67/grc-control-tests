import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_access_key_age as c

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "sample_data")


class TestKeyAge(unittest.TestCase):
    def test_pass_at_boundary(self):
        r = c.evaluate([{"user": "u", "key_id": "k", "status": "Active", "age_days": 90}])
        self.assertEqual(r["result"], "PASS")

    def test_fail_one_day_over(self):
        r = c.evaluate([{"user": "u", "key_id": "k", "status": "Active", "age_days": 91}])
        self.assertEqual(r["result"], "FAIL")
        self.assertEqual(r["exceptions"][0]["age_days"], 91)

    def test_inactive_keys_are_out_of_scope(self):
        r = c.evaluate([{"user": "u", "key_id": "k", "status": "Inactive", "age_days": 999}])
        self.assertEqual(r["result"], "PASS")
        self.assertEqual(r["population_in_scope"], 0)

    def test_custom_threshold(self):
        r = c.evaluate([{"user": "u", "key_id": "k", "status": "Active", "age_days": 45}], max_age_days=30)
        self.assertEqual(r["result"], "FAIL")

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "e.json")
            self.assertEqual(c.main(["--sample", os.path.join(SAMPLES, "access_keys_pass.json"), "--out", out]), 0)
            self.assertEqual(c.main(["--sample", os.path.join(SAMPLES, "access_keys_fail.json"), "--out", out]), 1)
            self.assertEqual(c.main(["--sample", os.path.join(d, "missing.json"), "--out", out]), 2)


if __name__ == "__main__":
    unittest.main()
