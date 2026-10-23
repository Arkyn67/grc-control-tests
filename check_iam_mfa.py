#!/usr/bin/env python3
"""
Control test: every AWS IAM user with console access has MFA enabled.

Reads either a sample JSON file (no AWS needed) or a live AWS account
(read-only IAM calls), evaluates the control, and writes an evidence file
with the population tested, the exceptions found and a pass/fail result.

Exit code: 0 = pass, 1 = fail, 2 = could not run the test.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

CONTROL_ID = "IAM-MFA-01"
CONTROL_TEXT = "All IAM users with console access must have MFA enabled."


def load_sample(path):
    """Load users from a sample file: [{user, console_access, mfa_devices}, ...]"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_aws(profile=None):
    """Collect users from a live account. Needs iam:ListUsers,
    iam:GetLoginProfile and iam:ListMFADevices (read-only)."""
    import boto3  # imported here so sample mode works without boto3
    from botocore.exceptions import ClientError

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    iam = session.client("iam")
    users = []
    for page in iam.get_paginator("list_users").paginate():
        for u in page["Users"]:
            name = u["UserName"]
            try:
                iam.get_login_profile(UserName=name)
                console = True
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    console = False
                else:
                    raise
            mfa = iam.list_mfa_devices(UserName=name)["MFADevices"]
            users.append({"user": name, "console_access": console,
                          "mfa_devices": len(mfa)})
    return users


def evaluate(users):
    """Apply the control to the collected population."""
    in_scope = [u for u in users if u["console_access"]]
    exceptions = [u["user"] for u in in_scope if u["mfa_devices"] < 1]
    return {
        "control_id": CONTROL_ID,
        "control": CONTROL_TEXT,
        "tested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "population_total": len(users),
        "population_in_scope": len(in_scope),
        "excluded_no_console_access": len(users) - len(in_scope),
        "exceptions": exceptions,
        "result": "PASS" if not exceptions else "FAIL",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sample", help="path to a sample JSON file")
    src.add_argument("--aws", action="store_true", help="test a live AWS account")
    p.add_argument("--profile", help="AWS profile name (with --aws)")
    p.add_argument("--out", default="evidence.json", help="evidence file to write")
    args = p.parse_args(argv)

    try:
        users = load_sample(args.sample) if args.sample else load_aws(args.profile)
    except Exception as e:  # collection failure must not look like a pass
        print(f"ERROR: could not collect data: {e}", file=sys.stderr)
        return 2

    evidence = evaluate(users)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"{evidence['control_id']}: {evidence['result']}  "
          f"({len(evidence['exceptions'])} exception(s) of "
          f"{evidence['population_in_scope']} in-scope users)")
    for name in evidence["exceptions"]:
        print(f"  - {name}: console access without MFA")
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
