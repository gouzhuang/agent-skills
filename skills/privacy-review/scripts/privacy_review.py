#!/usr/bin/env python3
"""Scan a codebase for potential privacy data leakage risks.

Outputs JSON or plain text to stdout. Warnings go to stderr.
Exit code 1 if any high-severity issues are found, 0 otherwise.
"""

import argparse
import fnmatch
import json
import os
import re
import sys

DEFAULT_EXCLUDE_PATTERNS = [
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".pytest_cache",
    "build",
    "dist",
    "target",
    "vendor",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.bin",
    "*.o",
    "*.a",
    "*.min.js",
    "*.lock",
    "*.sum",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.bmp",
    "*.ico",
    "*.mp3",
    "*.mp4",
    "*.avi",
    "*.mov",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
    "*.7z",
    "*.pdf",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
]

MAX_FILE_SIZE = 10 * 1024 * 1024

RULES = [
    {
        "name": "Private Key",
        "severity": "high",
        "pattern": re.compile(
            r"-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"
        ),
        "description": "检测到私钥文件内容",
    },
    {
        "name": "AWS Access Key ID",
        "severity": "high",
        "pattern": re.compile(r"AKIA[0-9A-Z]{16}"),
        "description": "检测到 AWS Access Key ID",
    },
    {
        "name": "AWS Secret Access Key",
        "severity": "high",
        "pattern": re.compile(
            r"aws[_\-.]?(?:secret[_\-.]?access[_\-.]?key|secret)\s*[=:]\s*['\"]?"
            r"[A-Za-z0-9/+=]{40}['\"]?",
            re.IGNORECASE,
        ),
        "description": "检测到 AWS Secret Access Key",
    },
    {
        "name": "Generic API Key",
        "severity": "high",
        "pattern": re.compile(
            r"(?:api[_\-.]?key|apikey)\s*[=:]\s*['\"]?"
            r"[A-Za-z0-9_\-]{16,}['\"]?",
            re.IGNORECASE,
        ),
        "description": "检测到硬编码 API Key",
    },
    {
        "name": "Generic Secret Token",
        "severity": "high",
        "pattern": re.compile(
            r"(?:secret[_\-.]?token|auth[_\-.]?token|access[_\-.]?token|bearer)\s*"
            r"[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?",
            re.IGNORECASE,
        ),
        "description": "检测到硬编码 Secret / Access Token",
    },
    {
        "name": "Hardcoded Password",
        "severity": "high",
        "pattern": re.compile(
            r"(?:password|passwd|pwd)\s*[=:]\s*['\"]"
            r"[^'\"\s]{4,}['\"]",
            re.IGNORECASE,
        ),
        "description": "检测到硬编码密码",
    },
    {
        "name": "Database Connection String",
        "severity": "high",
        "pattern": re.compile(
            r"(?:mongodb|mysql|postgresql|postgres|redis|amqp|mssql|oracle)"
            r"://[^:]+:[^@]+@[^/\s\"']+",
            re.IGNORECASE,
        ),
        "description": "检测到含密码的数据库连接字符串",
    },
    {
        "name": "GitHub Token",
        "severity": "high",
        "pattern": re.compile(
            r"gh[pousr]_[A-Za-z0-9_]{36,}"
        ),
        "description": "检测到 GitHub Personal / OAuth Token",
    },
    {
        "name": "Slack Token",
        "severity": "high",
        "pattern": re.compile(
            r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"
        ),
        "description": "检测到 Slack Token",
    },
    {
        "name": "JWT Token",
        "severity": "medium",
        "pattern": re.compile(
            r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"
        ),
        "description": "检测到 JWT Token",
    },
    {
        "name": "Email Address",
        "severity": "medium",
        "pattern": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "description": "检测到邮箱地址",
    },
    {
        "name": "Chinese Mobile Number",
        "severity": "low",
        "pattern": re.compile(
            r"(?<![0-9])1[3-9]\d{9}(?![0-9])"
        ),
        "description": "检测到中国大陆手机号",
    },
    {
        "name": "Chinese ID Card",
        "severity": "low",
        "pattern": re.compile(
            r"\b\d{17}[\dXx]|\d{15}\b"
        ),
        "description": "检测到身份证号",
    },
    {
        "name": "IPv4 Address",
        "severity": "low",
        "pattern": re.compile(
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        ),
        "description": "检测到 IPv4 地址",
    },
]


def _should_skip(path, exclude_patterns):
    """Check if a path should be skipped based on exclude patterns."""
    parts = path.split(os.sep)
    for part in parts:
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(part, pattern):
                return True
            if fnmatch.fnmatch(path, pattern):
                return True
    return False


def _is_binary(filepath):
    """Detect if a file is binary by checking for null bytes in first 8KB."""
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except Exception:
        return True


SEVERITY_PRIORITY = {"high": 0, "medium": 1, "low": 2}


def _scan_file(filepath, rules, severity_filter):
    """Scan a single file and return matched issues."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                raw_matches = []
                for rule in rules:
                    if severity_filter and rule["severity"] != severity_filter:
                        continue
                    for match in rule["pattern"].finditer(line):
                        matched_text = match.group(0)
                        # Skip common false positives for passwords
                        if rule["name"] == "Hardcoded Password":
                            lower = matched_text.lower()
                            if any(
                                fake in lower
                                for fake in [
                                    'password=""',
                                    "password=''",
                                    "password = \"\"",
                                    "password='no",
                                    "password='your",
                                    'password="your',
                                    "password='pass",
                                    'password="pass',
                                    "password='123",
                                    'password="123',
                                ]
                            ):
                                continue
                        # Skip private IP addresses
                        if rule["name"] == "IPv4 Address":
                            ip = matched_text
                            if ip.startswith("127.") or ip.startswith("10."):
                                continue
                            if ip.startswith("192.168."):
                                continue
                            parts = ip.split(".")
                            if len(parts) == 4 and parts[0] == "172":
                                second = int(parts[1])
                                if 16 <= second <= 31:
                                    continue

                        raw_matches.append({
                            "rule": rule["name"],
                            "severity": rule["severity"],
                            "text": matched_text,
                            "start": match.start(),
                            "end": match.end(),
                            "description": rule["description"],
                        })

                # Remove matches that are fully contained within a higher-priority match
                kept = []
                for i, m in enumerate(raw_matches):
                    contained = False
                    for j, other in enumerate(raw_matches):
                        if i == j:
                            continue
                        if m["start"] >= other["start"] and m["end"] <= other["end"]:
                            if (SEVERITY_PRIORITY[other["severity"]]
                                    < SEVERITY_PRIORITY[m["severity"]]):
                                contained = True
                                break
                    if not contained:
                        kept.append(m)

                for m in kept:
                    display = m["text"]
                    if len(display) > 120:
                        display = display[:117] + "..."
                    issues.append({
                        "file": filepath,
                        "line": line_no,
                        "rule": m["rule"],
                        "severity": m["severity"],
                        "match": display,
                        "description": m["description"],
                    })
    except Exception as e:
        print(
            json.dumps(
                {"warning": f"Could not read {filepath}: {e}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
    return issues


def _scan_directory(target_path, rules, severity_filter, exclude_patterns):
    """Recursively scan directory and return all issues."""
    all_issues = []
    files_scanned = 0

    for root, dirs, files in os.walk(target_path):
        # Filter out excluded directories in-place
        dirs[:] = [
            d for d in dirs
            if not _should_skip(os.path.join(root, d), exclude_patterns)
        ]

        for filename in files:
            filepath = os.path.join(root, filename)
            if _should_skip(filepath, exclude_patterns):
                continue

            try:
                size = os.path.getsize(filepath)
            except OSError:
                continue

            if size > MAX_FILE_SIZE:
                print(
                    json.dumps(
                        {"warning": f"Skipping large file: {filepath}"},
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                continue

            if _is_binary(filepath):
                continue

            files_scanned += 1
            issues = _scan_file(filepath, rules, severity_filter)
            all_issues.extend(issues)

    return all_issues, files_scanned


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="privacy_review",
        description="Scan codebase for privacy data leakage risks. "
        "Outputs JSON or text to stdout.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["high", "medium", "low", "all"],
        default="all",
        help="Filter by severity level (default: all)",
    )
    parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        default=[],
        help="Additional exclude pattern (can be used multiple times)",
    )
    return parser


def _output_json(issues, files_scanned, target_path):
    high = sum(1 for i in issues if i["severity"] == "high")
    medium = sum(1 for i in issues if i["severity"] == "medium")
    low = sum(1 for i in issues if i["severity"] == "low")

    output = {
        "scan_summary": {
            "target_path": target_path,
            "files_scanned": files_scanned,
            "issues_found": len(issues),
            "high": high,
            "medium": medium,
            "low": low,
        },
        "results": issues,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def _output_text(issues, files_scanned, target_path):
    print(f"Privacy Review Scan Results")
    print(f"Target: {target_path}")
    print(f"Files scanned: {files_scanned}")
    print(f"Issues found: {len(issues)}")
    print()

    if not issues:
        print("No privacy leakage risks detected.")
        return

    severity_order = ["high", "medium", "low"]
    for sev in severity_order:
        sev_issues = [i for i in issues if i["severity"] == sev]
        if not sev_issues:
            continue
        sev_label = sev.upper()
        print(f"[{sev_label}] ({len(sev_issues)} issues)")
        print("-" * 60)
        for issue in sev_issues:
            print(
                f"  {issue['file']}:{issue['line']}  "
                f"[{issue['rule']}] {issue['description']}"
            )
            print(f"    Match: {issue['match']}")
        print()


def main():
    parser = _build_parser()
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(
            json.dumps(
                {"error": f"Path does not exist: {target_path}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    severity_filter = None if args.severity == "all" else args.severity

    exclude_patterns = DEFAULT_EXCLUDE_PATTERNS + args.exclude

    issues, files_scanned = _scan_directory(
        target_path, RULES, severity_filter, exclude_patterns
    )

    if args.format == "json":
        _output_json(issues, files_scanned, target_path)
    else:
        _output_text(issues, files_scanned, target_path)

    has_high = any(i["severity"] == "high" for i in issues)
    return 1 if has_high else 0


if __name__ == "__main__":
    sys.exit(main())
