#!/usr/bin/env python3
"""
Control test: active AWS IAM access keys are rotated within a set number of days.

Reads either a sample JSON file (no AWS needed) or a live AWS account
(read-only IAM calls), evaluates the control and writes an evidence file.

Exit code: 0 = pass, 1 = fail, 2 = could not run the test.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

CONTROL_ID = "IAM-KEY-01"
DEFAULT_MAX_AGE_DAYS = 90


def load_sample(path):
    """Sample file: [{user, key_id, status, age_days}, ...]"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_aws(profile=None):
    """Needs iam:ListUsers and iam:ListAccessKeys (read-only)."""
    import boto3  # imported here so sample mode works without boto3

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    iam = session.client("iam")
    now = datetime.now(timezone.utc)
    keys = []
    for page in iam.get_paginator("list_users").paginate():
        for u in page["Users"]:
            for k in iam.list_access_keys(UserName=u["UserName"])["AccessKeyMetadata"]:
                keys.append({
                    "user": u["UserName"],
                    "key_id": k["AccessKeyId"],
                    "status": k["Status"],
                    "age_days": (now - k["CreateDate"]).days,
                })
    return keys


def evaluate(keys, max_age_days=DEFAULT_MAX_AGE_DAYS):
    active = [k for k in keys if k["status"] == "Active"]
    exceptions = [
        {"user": k["user"], "key_id": k["key_id"], "age_days": k["age_days"]}
        for k in active if k["age_days"] > max_age_days
    ]
    return {
        "control_id": CONTROL_ID,
        "control": f"Active IAM access keys must be rotated within {max_age_days} days.",
        "tested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "max_age_days": max_age_days,
        "population_total": len(keys),
        "population_in_scope": len(active),
        "excluded_inactive": len(keys) - len(active),
        "exceptions": exceptions,
        "result": "PASS" if not exceptions else "FAIL",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sample", help="path to a sample JSON file")
    src.add_argument("--aws", action="store_true", help="test a live AWS account")
    p.add_argument("--profile", help="AWS profile name (with --aws)")
    p.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    p.add_argument("--out", default="evidence_access_keys.json")
    args = p.parse_args(argv)

    try:
        keys = load_sample(args.sample) if args.sample else load_aws(args.profile)
    except Exception as e:
        print(f"ERROR: could not collect data: {e}", file=sys.stderr)
        return 2

    evidence = evaluate(keys, args.max_age_days)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"{evidence['control_id']}: {evidence['result']}  "
          f"({len(evidence['exceptions'])} exception(s) of "
          f"{evidence['population_in_scope']} active keys)")
    for e in evidence["exceptions"]:
        print(f"  - {e['user']} / {e['key_id']}: {e['age_days']} days old")
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
