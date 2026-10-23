# grc-control-tests

Small, readable scripts that test one compliance control each and produce evidence a reviewer can check. The idea is to pull evidence from the source system instead of collecting screenshots.

All sample data in this repository is invented. Nothing here comes from any employer or client.

## Controls

| ID | Script | Control | Illustrative mapping* |
|---|---|---|---|
| IAM-MFA-01 | `check_iam_mfa.py` | All IAM users with console access have MFA enabled | SOC 2 CC6.1; ISO/IEC 27001:2022 A.8.5 |
| IAM-ROOT-01 | `check_root_mfa.py` | The AWS root account has MFA enabled | SOC 2 CC6.1; ISO/IEC 27001:2022 A.8.5 |
| IAM-KEY-01 | `check_access_key_age.py` | Active IAM access keys are rotated within 90 days (configurable) | SOC 2 CC6.1; ISO/IEC 27001:2022 A.5.17, A.8.5 |

*Mappings are illustrative. Confirm them against your own control set before using them in an audit.

## How every test behaves

1. Collects data either from a sample JSON file (`--sample`) or from a live AWS account (`--aws`, read-only calls).
2. Defines what is in scope and counts what is excluded, so the population is visible.
3. Marks the control **PASS** or **FAIL** and lists each exception.
4. Writes an evidence JSON file with the timestamp, population, exceptions and result.
5. Exits `0` on pass, `1` on fail and `2` if the data could not be collected or is malformed, so a failed collection never looks like a pass.

## Run on sample data (no AWS needed)

```bash
python3 check_iam_mfa.py --sample sample_data/iam_users_fail.json
python3 check_root_mfa.py --sample sample_data/root_summary_fail.json
python3 check_access_key_age.py --sample sample_data/access_keys_fail.json
python3 -m unittest discover -s tests -v
```

Use the `_pass.json` files to see a passing result.

## Run against an AWS account

```bash
pip install boto3
python3 check_iam_mfa.py --aws --profile my-readonly-profile
python3 check_root_mfa.py --aws --profile my-readonly-profile
python3 check_access_key_age.py --aws --profile my-readonly-profile --max-age-days 90
```

Read-only permissions needed:

- `check_iam_mfa.py`: `iam:ListUsers`, `iam:GetLoginProfile`, `iam:ListMFADevices`
- `check_root_mfa.py`: `iam:GetAccountSummary`
- `check_access_key_age.py`: `iam:ListUsers`, `iam:ListAccessKeys`

The live modes have not been tested against a production account, so try them in a sandbox account first.

## What these tests do not prove

A test should prove what the control requires, and no more. A pass here does not mean:

- **IAM-MFA-01:** that people who sign in through SSO or IAM Identity Center are covered (this test does not see them), that MFA is enforced by policy rather than just set up, or that the device is actually used.
- **IAM-ROOT-01:** that the type of MFA is strong. The account summary only says whether MFA is enabled, not which kind.
- **IAM-KEY-01:** that unused keys are removed, that keys are stored safely, or that key age is the right rotation rule for every workload. Inactive keys are excluded from scope.

## Roadmap

- Password policy check
- Unused credentials check
- Output in a format that can be loaded into a compliance platform
