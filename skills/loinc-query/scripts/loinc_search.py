#!/usr/bin/env python3
"""AI-friendly CLI for querying the LOINC database via Regenstrief Search API.

Outputs pretty-printed JSON to stdout. Errors go to stderr as JSON.
Reads credentials from ~/.loincrc first, then falls back to env vars.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Literal

import httpx

BASE_URL = "https://loinc.regenstrief.org/searchapi"
EndpointType = Literal["loincs", "parts", "answerlists", "groups"]

DETAIL_FIELDS = {
    "loincs": {
        "brief": {
            "LOINC_NUM", "COMPONENT", "PROPERTY", "TIME_ASPCT", "SYSTEM",
            "SCALE_TYP", "METHOD_TYP", "LONG_COMMON_NAME", "STATUS", "CLASS",
        },
        "moderate": {
            "LOINC_NUM", "COMPONENT", "PROPERTY", "TIME_ASPCT", "SYSTEM",
            "SCALE_TYP", "METHOD_TYP", "LONG_COMMON_NAME", "STATUS", "CLASS",
            "SHORTNAME", "DisplayName", "FORMULA", "EXAMPLE_UNITS",
            "EXAMPLE_UCUM_UNITS", "DefinitionDescription", "VersionLastChanged",
            "VersionFirstReleased", "ORDER_OBS", "CLASSTYPE", "Link",
        },
    },
    "parts": {
        "brief": {"PartNumber", "PartTypeName", "PartName", "Status"},
        "moderate": {
            "PartNumber", "PartTypeName", "PartName", "Status",
            "PartDisplayName", "Classlist", "Link",
        },
    },
    "answerlists": {
        "brief": {"AnswerListId", "Name", "ExtDefinedYN", "Link"},
        "moderate": {
            "AnswerListId", "Name", "ExtDefinedYN", "Link",
            "Description", "LoincAnswerListOid", "Answers",
        },
    },
    "groups": {
        "brief": {"GroupId", "Group", "Archetype", "STATUS", "Category", "Link"},
        "moderate": {
            "GroupId", "Group", "Archetype", "STATUS", "Category", "Link",
            "ParentGroupId", "ParentGroup", "VersionFirstReleased",
            "UsageNotes", "Loincs",
        },
    },
}


class LoincApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _load_credentials() -> tuple[str, str]:
    """Load credentials from ~/.loincrc, falling back to env vars."""
    rc_path = os.path.expanduser("~/.loincrc")
    if os.path.isfile(rc_path):
        creds: dict[str, str] = {}
        with open(rc_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip()
        user = creds.get("username", "")
        passwd = creds.get("password", "")
        if user and passwd:
            return user, passwd

    user = os.environ.get("LOINC_USERNAME", "")
    passwd = os.environ.get("LOINC_PASSWORD", "")
    if user and passwd:
        return user, passwd

    raise LoincApiError(
        "No credentials found. Set ~/.loincrc (username=..., password=...) or "
        "environment variables LOINC_USERNAME / LOINC_PASSWORD."
    )

def _filter_result_fields(
    results: list[dict[str, Any]], keep_fields: set[str]
) -> list[dict[str, Any]]:
    filtered = []
    for item in results:
        new_item = {k: v for k, v in item.items() if k in keep_fields}
        filtered.append(new_item)
    return filtered


async def _make_request(
    client: httpx.AsyncClient, endpoint: str, params: dict[str, Any]
) -> dict[str, Any]:
    str_params = {k: str(v) for k, v in params.items() if v is not None}
    try:
        response = await client.get(endpoint, params=str_params)
    except httpx.TimeoutException:
        raise LoincApiError("Request timed out. Try again later.")
    except httpx.ConnectError:
        raise LoincApiError("Cannot connect to LOINC API. Check your network.")

    if response.status_code == 401:
        raise LoincApiError(
            "Authentication failed. Check your LOINC credentials.", status_code=401
        )
    if response.status_code == 403:
        raise LoincApiError(
            "Access denied. Your LOINC account may not have API access.",
            status_code=403,
        )
    if response.status_code >= 500:
        raise LoincApiError(
            "LOINC API server error. Try again later.",
            status_code=response.status_code,
        )
    if response.status_code != 200:
        raise LoincApiError(
            f"Unexpected error (HTTP {response.status_code}).",
            status_code=response.status_code,
        )

    try:
        data = response.json()
    except Exception:
        raise LoincApiError("Invalid JSON response from LOINC API.")

    return data


async def search(
    query: str,
    endpoint: EndpointType = "loincs",
    rows: int = 20,
    offset: int = 0,
    sort: str | None = None,
) -> dict[str, Any]:
    user, passwd = _load_credentials()
    async with httpx.AsyncClient(
        auth=(user, passwd),
        headers={"Accept": "application/json"},
        base_url=BASE_URL,
        timeout=60.0,
    ) as client:
        params: dict[str, Any] = {"query": query, "rows": rows}
        if offset:
            params["offset"] = offset
        if sort:
            params["sortorder"] = sort

        return await _make_request(client, endpoint, params)


def _error_json(message: str, status_code: int | None = None) -> None:
    err: dict[str, Any] = {"error": message}
    if status_code:
        err["status_code"] = status_code
    print(json.dumps(err, ensure_ascii=False), file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loinc_search",
        description="Search LOINC database via Regenstrief API. "
        "Outputs pretty-printed JSON to stdout.",
    )
    parser.add_argument(
        "command",
        choices=["search", "parts", "answers", "groups", "details"],
        help="Command to execute",
    )
    parser.add_argument(
        "query",
        help="Search query or LOINC code (quote if contains spaces)",
    )
    parser.add_argument(
        "--rows",
        "-n",
        type=int,
        default=20,
        help="Number of results to return (default: 20)",
    )
    parser.add_argument(
        "--offset", type=int, default=0, help="Result offset for pagination"
    )
    parser.add_argument(
        "--sort",
        help="Sort field and order, e.g. 'loinc_num desc'",
    )
    parser.add_argument(
        "--detail",
        "-d",
        choices=["brief", "moderate", "full"],
        default="full",
        help="Detail level of results: brief, moderate, or full (default: full)",
    )
    return parser


def _run_async(coro):
    return asyncio.run(coro)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    endpoint_map: dict[str, EndpointType] = {
        "search": "loincs",
        "parts": "parts",
        "answers": "answerlists",
        "groups": "groups",
    }

    try:
        if args.command == "details":
            result = _run_async(
                search(args.query, endpoint="loincs", rows=1, offset=0, sort=args.sort)
            )
            if not result.get("Results"):
                _error_json(f"No results found for code '{args.query}'.")
                return 1
            ep = "loincs"
        else:
            ep = endpoint_map[args.command]
            result = _run_async(
                search(
                    args.query,
                    endpoint=ep,
                    rows=args.rows,
                    offset=args.offset,
                    sort=args.sort,
                )
            )

        if args.detail != "full" and "Results" in result:
            keep = DETAIL_FIELDS[ep][args.detail]
            result["Results"] = _filter_result_fields(result["Results"], keep)

        print(json.dumps(result, indent=2, ensure_ascii=False))
    except LoincApiError as e:
        _error_json(e.message, e.status_code)
        return 1
    except Exception as e:
        _error_json(str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
