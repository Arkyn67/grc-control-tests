#!/usr/bin/env python3
"""
Control test: the AWS root account has MFA enabled.

Reads either a sample JSON file (no AWS needed) or a live AWS account
(one read-only IAM call), evaluates the control and writes an evidence file.

Exit code: 0 = pass, 1 = fail, 2 = could not run the test.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

CONTROL_ID = "IAM-ROOT-01"
CONTROL_TEXT = "The AWS root account must have MFA enabled."


def load_sample(path):
    """Sample file: {"AccountMFAEnabled": 1}"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_aws(profile=None):
    """Needs iam:GetAccountSummary (read-only)."""
    import boto3  # imported here so sample mode works without boto3

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("iam").get_account_summary()["SummaryMap"]


def evaluate(summary):
    # A missing field is a collection problem, not a pass.
    if "AccountMFAEnabled" not in summary:
        raise ValueError("AccountMFAEnabled not found in account summary")
    enabled = summary["AccountMFAEnabled"] == 1
    return {
        "control_id": CONTROL_ID,
        "control": CONTROL_TEXT,
        "tested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root_mfa_enabled": enabled,
        "result": "PASS" if enabled else "FAIL",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sample", help="path to a sample JSON file")
    src.add_argument("--aws", action="store_true", help="test a live AWS account")
    p.add_argument("--profile", help="AWS profile name (with --aws)")
    p.add_argument("--out", default="evidence_root_mfa.json")
    args = p.parse_args(argv)

    try:
        summary = load_sample(args.sample) if args.sample else load_aws(args.profile)
        evidence = evaluate(summary)
    except Exception as e:
        print(f"ERROR: could not run test: {e}", file=sys.stderr)
        return 2

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print(f"{evidence['control_id']}: {evidence['result']}")
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
