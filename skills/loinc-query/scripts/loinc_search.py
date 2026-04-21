#!/usr/bin/env python3
"""AI-friendly CLI for querying the LOINC database via Regenstrief Search API.

Outputs structured data (JSON/JSONL/CSV) to stdout. Errors go to stderr as JSON.
Reads credentials from ~/.loincrc first, then falls back to env vars.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

BASE_URL = "https://loinc.regenstrief.org/searchapi"
ENDPOINTS: tuple[EndpointType, ...] = ("loincs", "parts", "answerlists", "groups")
EndpointType = Literal["loincs", "parts", "answerlists", "groups"]

# Field mapping from API keys to Python snake_case
_FIELD_MAP: dict[str, str] = {
    "LOINC_NUM": "loinc_num",
    "COMPONENT": "component",
    "PROPERTY": "property",
    "TIME_ASPCT": "time_aspect",
    "SYSTEM": "system",
    "SCALE_TYP": "scale_type",
    "METHOD_TYP": "method_type",
    "CLASS": "class_name",
    "CLASS_TYPE": "class_type",
    "STATUS": "status",
    "LONG_COMMON_NAME": "long_common_name",
    "SHORTNAME": "shortname",
    "ORDER_OBS": "order_obs",
    "EXAMPLE_UNITS": "example_units",
    "EXAMPLE_UCUM_UNITS": "example_ucum_units",
    "RELATEDNAMES2": "related_names",
    "COMMON_TEST_RANK": "common_test_rank",
    "COMMON_ORDER_RANK": "common_order_rank",
    "COMMON_SI_TEST_RANK": "common_si_test_rank",
    "DefinitionDescription": "definition_description",
    "VersionFirstReleased": "version_first_released",
    "VersionLastChanged": "version_last_changed",
    "CHNG_TYPE": "change_type",
    "STATUS_TEXT": "status_text",
    "STATUS_REASON": "status_reason",
    "CHANGE_REASON_PUBLIC": "change_reason_public",
    "CONSUMER_NAME": "consumer_name",
    "CLASSTYPE": "classtype",
    "FORMULA": "formula",
    "ExampleAnswers": "example_answers",
    "SURVEY_QUEST_TEXT": "survey_quest_text",
    "SURVEY_QUEST_SRC": "survey_quest_src",
    "UNITSREQUIRED": "units_required",
    "HL7_FIELD_SUBFIELD_ID": "hl7_field_subfield_id",
    "HL7_ATTACHMENT_STRUCTURE": "hl7_attachment_structure",
    "EXTERNAL_COPYRIGHT_NOTICE": "external_copyright_notice",
    "EXTERNAL_COPYRIGHT_LINK": "external_copyright_link",
    "PanelType": "panel_type",
    "DisplayName": "display_name",
    "FormalName": "formal_name",
    "Link": "link",
    "AnswerList": "answer_list",
    "AskAtOrderEntry": "ask_at_order_entry",
    "AssociatedObservations": "associated_observations",
    "ValidHL7AttachmentRequest": "valid_hl7_attachment_request",
    "LHCForms": "lhc_forms",
    "LinguisticVariantDisplayName": "linguistic_variant_display_name",
    "PartNumber": "part_number",
    "PartTypeName": "part_type_name",
    "PartName": "part_name",
    "PartCodeSystem": "part_code_system",
    "PartDisplayName": "part_display_name",
    "PartLink": "part_link",
    "GroupId": "group_id",
    "GroupName": "group_name",
    "GroupType": "group_type",
    "AnswerString": "answer_string",
    "AnswerLOINCCode": "answer_loinc_code",
    "Sequence": "sequence",
    "TermDescriptions": "term_descriptions",
    "CodeSystems": "code_systems",
    "Tags": "tags",
}

# Complex fields that should preserve original structure (not str-converted)
_COMPLEX_FIELDS = frozenset({"term_descriptions", "code_systems", "tags"})

# Detail level field sets
_BRIEF_FIELDS = frozenset({
    "loinc_num", "component", "long_common_name", "status",
})
_MODERATE_FIELDS = _BRIEF_FIELDS | frozenset({
    "property", "time_aspect", "system", "scale_type", "method_type",
    "class_name", "order_obs", "example_units", "shortname", "link",
})


@dataclass
class LoincTerm:
    """A single LOINC term or search result item."""

    loinc_num: str = ""
    component: str = ""
    property: str = ""
    time_aspect: str = ""
    system: str = ""
    scale_type: str = ""
    method_type: str = ""
    class_name: str = ""
    class_type: str = ""
    status: str = ""
    long_common_name: str = ""
    shortname: str = ""
    order_obs: str = ""
    example_units: str = ""
    example_ucum_units: str = ""
    related_names: str = ""
    common_test_rank: str = ""
    common_order_rank: str = ""
    common_si_test_rank: str = ""
    definition_description: str = ""
    version_first_released: str = ""
    version_last_changed: str = ""
    change_type: str = ""
    status_text: str = ""
    status_reason: str = ""
    change_reason_public: str = ""
    consumer_name: str = ""
    classtype: str = ""
    formula: str = ""
    example_answers: str = ""
    survey_quest_text: str = ""
    survey_quest_src: str = ""
    units_required: str = ""
    hl7_field_subfield_id: str = ""
    hl7_attachment_structure: str = ""
    external_copyright_notice: str = ""
    external_copyright_link: str = ""
    panel_type: str = ""
    display_name: str = ""
    formal_name: str = ""
    link: str = ""
    answer_list: str = ""
    ask_at_order_entry: str = ""
    associated_observations: str = ""
    valid_hl7_attachment_request: str = ""
    lhc_forms: str = ""
    linguistic_variant_display_name: str = ""
    term_descriptions: list = field(default_factory=list)
    code_systems: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> LoincTerm:
        mapped: dict[str, Any] = {}
        extra: dict[str, str] = {}
        known = cls.__dataclass_fields__
        for key, value in data.items():
            if value is None:
                value = ""
            py_key = _FIELD_MAP.get(key)
            if py_key and py_key in known:
                if py_key in _COMPLEX_FIELDS:
                    mapped[py_key] = value if isinstance(value, list) else []
                else:
                    mapped[py_key] = str(value)
            else:
                extra[key] = str(value) if not isinstance(value, (list, dict)) else value
        return cls(**mapped, extra=extra)

    def to_dict(self, detail: str = "moderate") -> dict[str, Any]:
        if detail == "detailed":
            fields = None
        elif detail == "brief":
            fields = _BRIEF_FIELDS
        else:
            fields = _MODERATE_FIELDS
        d: dict[str, Any] = {}
        for f in self.__dataclass_fields__:
            if f == "extra":
                continue
            if fields is not None and f not in fields:
                continue
            v = getattr(self, f)
            if fields is None or v:
                d[f] = v
        if fields is None and self.extra:
            d.update(self.extra)
        return d


@dataclass
class SearchResult:
    results: list[LoincTerm]
    total_count: int = 0
    offset: int = 0
    rows: int = 20
    query: str = ""
    endpoint: str = ""

    @property
    def has_more(self) -> bool:
        return (self.offset + len(self.results)) < self.total_count


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
    language: int | None = None,
) -> SearchResult:
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
        if language:
            params["language"] = language

        result = await _make_request(client, endpoint, params)
        raw_results = result.get("results", [])
        terms = [LoincTerm.from_api(item) for item in raw_results]

        summary = result.get("responsesummary", {})
        total = summary.get("RecordsFound", len(terms))
        try:
            total = int(total)
        except (ValueError, TypeError):
            total = len(terms)

        return SearchResult(
            results=terms,
            total_count=total,
            offset=offset,
            rows=rows,
            query=query,
            endpoint=endpoint,
        )


async def search_all_endpoints(
    query: str, rows: int = 20
) -> dict[str, SearchResult]:
    tasks = [search(query, ep, rows=rows) for ep in ENDPOINTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output: dict[str, SearchResult] = {}
    for ep, result in zip(ENDPOINTS, results):
        if isinstance(result, BaseException):
            output[ep] = SearchResult(
                results=[], query=query, endpoint=ep, rows=rows
            )
        else:
            output[ep] = result
    return output


def _output_json(result: SearchResult, detail: str = "moderate") -> None:
    data = {
        "query": result.query,
        "endpoint": result.endpoint,
        "total_count": result.total_count,
        "offset": result.offset,
        "rows": result.rows,
        "has_more": result.has_more,
        "results": [t.to_dict(detail=detail) for t in result.results],
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _output_jsonl(result: SearchResult, detail: str = "moderate") -> None:
    for term in result.results:
        print(json.dumps(term.to_dict(detail=detail), ensure_ascii=False))


def _output_csv(result: SearchResult, detail: str = "moderate") -> None:
    if not result.results:
        return
    buf = io.StringIO()
    writer = csv.writer(buf)
    # Collect all unique keys across results for header
    keys: list[str] = []
    seen: set[str] = set()
    for term in result.results:
        for k in term.to_dict(detail=detail):
            if k not in seen:
                keys.append(k)
                seen.add(k)
    writer.writerow(keys)
    for term in result.results:
        d = term.to_dict(detail=detail)
        writer.writerow([d.get(k, "") for k in keys])
    sys.stdout.write(buf.getvalue())


def _display(result: SearchResult, fmt: str, detail: str = "moderate") -> None:
    if fmt == "jsonl":
        _output_jsonl(result, detail=detail)
    elif fmt == "csv":
        _output_csv(result, detail=detail)
    else:
        _output_json(result, detail=detail)


def _error_json(message: str, status_code: int | None = None) -> None:
    err: dict[str, Any] = {"error": message}
    if status_code:
        err["status_code"] = status_code
    print(json.dumps(err, ensure_ascii=False), file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loinc_search",
        description="Search LOINC database via Regenstrief API. "
        "Outputs JSON/JSONL/CSV to stdout.",
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
    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "jsonl", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--detail",
        "-d",
        choices=["brief", "moderate", "detailed"],
        default="moderate",
        help="Detail level: brief (4 fields), moderate (14 fields), detailed (all) (default: moderate)",
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
            data = {
                "query": args.query,
                "endpoints": {
                    ep: {
                        "total_count": r.total_count,
                        "offset": r.offset,
                        "rows": r.rows,
                        "has_more": r.has_more,
                        "results": [t.to_dict(detail=args.detail) for t in r.results],
                    }
                    for ep, r in results.items()
                },
            }
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif args.command == "details":
            result = _run_async(
                search(
                    args.query,
                    endpoint="loincs",
                    rows=1,
                    offset=0,
                    sort=args.sort,
                )
            )
            if not result.results:
                _error_json(f"No results found for code '{args.query}'.")
                return 1
            _display(SearchResult(
                results=result.results,
                total_count=result.total_count,
                offset=result.offset,
                rows=result.rows,
                query=args.query,
                endpoint="loincs",
            ), args.output, args.detail)
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
            _display(result, args.output, args.detail)
    except LoincApiError as e:
        _error_json(e.message, e.status_code)
        return 1
    except Exception as e:
        _error_json(str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
