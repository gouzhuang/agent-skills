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
ENDPOINTS: tuple[EndpointType, ...] = ("loincs", "parts", "answerlists", "groups")
EndpointType = Literal["loincs", "parts", "answerlists", "groups"]


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


def _normalize_response(data: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if key == "Results":
            normalized["results"] = value
        else:
            normalized[key.lower()] = value
    if "results" not in normalized:
        normalized["results"] = []
    return normalized


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

    return _normalize_response(data)


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


async def search_all_endpoints(
    query: str, rows: int = 20
) -> dict[str, dict[str, Any]]:
    tasks = [search(query, ep, rows=rows) for ep in ENDPOINTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output: dict[str, dict[str, Any]] = {}
    for ep, result in zip(ENDPOINTS, results):
        if isinstance(result, BaseException):
            output[ep] = {"results": [], "error": str(result)}
        else:
            output[ep] = result
    return output


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
        choices=["search", "parts", "answers", "groups", "details", "all"],
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
        if args.command == "all":
            results = _run_async(search_all_endpoints(args.query, rows=args.rows))
            data = {"query": args.query, "endpoints": results}
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif args.command == "details":
            result = _run_async(
                search(args.query, endpoint="loincs", rows=1, offset=0, sort=args.sort)
            )
            if not result.get("results"):
                _error_json(f"No results found for code '{args.query}'.")
                return 1
            print(json.dumps(result, indent=2, ensure_ascii=False))
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
