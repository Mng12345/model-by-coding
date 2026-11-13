#!/usr/bin/env python
"""Print a readable pass/fail summary of a HyperFrames `check` report.

The report is the JSON written by `hyperframes check` either to stdout
(`check --json`) or to the project's artifact directory
`<project>/.hyperframes/artifacts/checks/<uuid>.json`. Both carry the same
schema: a top-level `ok` plus one bucket per pass (`lint`, `runtime`, `layout`,
`motion`, `contrast`, `craft`, `audio`, ...), each with `findings` and
`errorCount` / `warningCount` / `infoCount`. Older CLI versions wrote a flat
`issues` array instead; that shape is accepted too.

Usage:
    python hf_read_check.py video/.hyperframes/artifacts/checks/<uuid>.json
    python hf_read_check.py check.json --max 5
    python hf_read_check.py check.json --fail-on-error   # CI guard

Exit codes: 0 = summary printed (regardless of findings, unless --fail-on-error),
1 = --fail-on-error and the report is not ok, 2 = unreadable/invalid JSON.

Stdlib only. Accepts UTF-8, UTF-8-with-BOM and UTF-16LE/BE (PowerShell's `>`
redirect produces UTF-16, so reports captured that way still parse).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

SECTION_ORDER = [
    "lint",
    "runtime",
    "layout",
    "motion",
    "contrast",
    "craft",
    "audio",
    "hdr",
    "snapshots",
]
SEVERITY_ERRORS = {"error", "fatal"}
SEVERITY_WARNINGS = {"warning", "warn"}
SEVERITY_INFO = {"info", "information"}


def read_json_any_encoding(path):
    """Decode the JSON file regardless of the encoding the shell used."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    elif raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
    return json.loads(text)


def severity_of(finding):
    return str(finding.get("severity", "")).strip().lower()


def collect_flat_issues(report):
    """Old format: one flat list of issues with severity fields."""
    issues = report.get("issues")
    if not isinstance(issues, list):
        return None
    errors = sum(1 for item in issues if severity_of(item) in SEVERITY_ERRORS)
    warnings = sum(1 for item in issues if severity_of(item) in SEVERITY_WARNINGS)
    infos = sum(1 for item in issues if severity_of(item) in SEVERITY_INFO)
    return {
        "sections": [],
        "findings": issues,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "shown": len(issues),
    }


def collect_sections(report):
    sections = []
    findings = []
    for key in SECTION_ORDER + [k for k in report.keys() if k not in SECTION_ORDER]:
        node = report.get(key)
        if not isinstance(node, dict) or ("findings" not in node and "errorCount" not in node):
            continue
        listed = node.get("findings") if isinstance(node.get("findings"), list) else []
        findings.extend(listed)
        sections.append(
            {
                "name": key,
                "ok": node.get("ok"),
                "errors": int(node.get("errorCount") or 0),
                "warnings": int(node.get("warningCount") or 0),
                "infos": int(node.get("infoCount") or 0),
                "findings": len(listed),
                "enabled": node.get("enabled"),
            }
        )
    errors = sum(item["errors"] for item in sections)
    warnings = sum(item["warnings"] for item in sections)
    infos = sum(item["infos"] for item in sections)
    return {
        "sections": sections,
        "findings": findings,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "shown": len(findings),
    }


def truncate(text, limit):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Summarise a HyperFrames check report (ok flag, per-pass issue counts, worst findings).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("report", help="path to the check JSON (artifact or redirected stdout)")
    ap.add_argument("--max", type=int, default=8, help="how many findings to print")
    ap.add_argument("--json", action="store_true", help="print the summary itself as JSON")
    ap.add_argument(
        "--fail-on-error",
        action="store_true",
        help="exit 1 when the report is not ok or contains errors (CI gate)",
    )
    args = ap.parse_args(argv)

    if not os.path.isfile(args.report):
        print("hf_read_check.py: no such file: %s" % args.report, file=sys.stderr)
        return 2
    try:
        report = read_json_any_encoding(args.report)
    except (OSError, ValueError) as err:
        print("hf_read_check.py: not a JSON check report: %s (%s)" % (args.report, err), file=sys.stderr)
        return 2
    if not isinstance(report, dict):
        print("hf_read_check.py: report root is not an object", file=sys.stderr)
        return 2

    summary = collect_flat_issues(report) or collect_sections(report)
    ok = report.get("ok")
    if ok is None:
        ok = summary["errors"] == 0
    duration = None
    layout = report.get("layout")
    if isinstance(layout, dict):
        duration = layout.get("duration")

    if args.json:
        print(
            json.dumps(
                {
                    "ok": bool(ok),
                    "duration": duration,
                    "errors": summary["errors"],
                    "warnings": summary["warnings"],
                    "infos": summary["infos"],
                    "sections": summary["sections"],
                },
                indent=2,
            )
        )
        return 0 if (ok or not args.fail_on_error) else 1

    print("report: %s" % args.report)
    if duration is not None:
        print("duration: %ss" % duration)
    print(
        "ok: %s | errors: %d | warnings: %d | info: %d | findings: %d"
        % (
            "true" if ok else "false",
            summary["errors"],
            summary["warnings"],
            summary["infos"],
            summary["shown"],
        )
    )
    for section in summary["sections"]:
        flags = []
        if section["ok"] is not None:
            flags.append("ok" if section["ok"] else "FAIL")
        if section.get("enabled") is False:
            flags.append("disabled")
        print(
            "  %-9s errors=%-3d warnings=%-3d info=%-3d findings=%-3d %s"
            % (
                section["name"],
                section["errors"],
                section["warnings"],
                section["infos"],
                section["findings"],
                " ".join(flags),
            )
        )

    ranked = sorted(
        summary["findings"],
        key=lambda f: (
            0
            if severity_of(f) in SEVERITY_ERRORS
            else 1
            if severity_of(f) in SEVERITY_WARNINGS
            else 2
        ),
    )
    if ranked and args.max > 0:
        print("findings (worst first):")
        for finding in ranked[: args.max]:
            severity = severity_of(finding) or "?"
            code = finding.get("code") or finding.get("rule") or "-"
            message = truncate(finding.get("message", ""), 150)
            print("  [%s] %s: %s" % (severity, code, message))
        if len(ranked) > args.max:
            print("  ... %d more (raise --max to see them)" % (len(ranked) - args.max))

    if args.fail_on_error and (not ok or summary["errors"] > 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
