"""
Translation coverage report for the SamadhanSetu Flutter app.

Reads the translation maps, the citizen-flow key lists and the native-review
registry straight from the Dart sources, so the numbers always match the code:

  frontend/lib/core/localization/app_localizations.dart   (strings per language)
  frontend/lib/core/localization/citizen_flow_keys.dart   (citizen journey keys)
  frontend/lib/core/localization/translation_review.dart  (keys a native speaker signed off)

Run:
  python scripts/translation_coverage.py               # plain-text table
  python scripts/translation_coverage.py --markdown    # Markdown table (README, docs)
  python scripts/translation_coverage.py --sheets docs/translations
      # also writes one CSV review sheet per tribal language for native speakers
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
L10N_DIR = ROOT / "frontend" / "lib" / "core" / "localization"
LANGUAGES = [
    ("en", "English", "Latin"),
    ("hi", "Hindi", "Devanagari"),
    ("sat", "Santali", "Ol Chiki"),
    ("unr", "Mundari", "Devanagari"),
    ("hoc", "Ho", "Devanagari"),
    ("kru", "Kurukh", "Devanagari"),
    ("khortha", "Khortha", "Devanagari"),
]
TRIBAL = {"sat", "unr", "hoc", "kru", "khortha"}
# Consent, data-rights and privacy wording: a mistranslation here changes what
# a citizen agrees to, so these need sign-off first (DPDP Act 2023 notices).
LEGAL_KEYS = {
    "declaration_text", "data_sharing_consent_label", "data_sharing_public_aggregated",
    "data_sharing_authorized_research_only", "data_sharing_government_only",
    "request_erasure_warning", "erasure_confirmation_label", "request_erasure_desc",
    "export_my_data_desc", "correct_my_data_desc", "submit_anonymously_subtitle",
    "report_step2_sub", "dpdp_subtitle", "privacy_notice_title", "your_data_rights_title",
}

_ENTRY = re.compile(r"^      '([a-z0-9_]+)': '((?:[^'\\]|\\.)*)',", re.M)


def _unescape(value: str) -> str:
    return value.replace("\\'", "'").replace("\\$", "$").replace("\\\\", "\\")


def load_tables() -> dict:
    source = (L10N_DIR / "app_localizations.dart").read_text(encoding="utf-8")
    tables = {}
    for code, _, _ in LANGUAGES:
        start = source.index(f"    '{code}': {{\n")
        end = source.index("\n    }", start)
        tables[code] = {k: _unescape(v) for k, v in _ENTRY.findall(source[start:end])}
    return tables


def load_key_list(name: str) -> list:
    source = (L10N_DIR / "citizen_flow_keys.dart").read_text(encoding="utf-8")
    block = re.search(rf"const List<String> {name} = \[(.*?)\];", source, re.S)
    return re.findall(r"'([a-z0-9_]+)'", block.group(1))


def load_reviewed() -> dict:
    source = (L10N_DIR / "translation_review.dart").read_text(encoding="utf-8")
    block = re.search(r"kNativeReviewedKeys = \{(.*?)\n\};", source, re.S).group(1)
    return {code: set(re.findall(r"'([a-z0-9_]+)'", keys))
            for code, keys in re.findall(r"'(\w+)': \{(.*?)\}", block, re.S)}


def coverage_rows(tables, flow, core, reviewed):
    english = set(tables["en"])
    rows = []
    for code, name, script in LANGUAGES:
        keys = set(tables[code])
        rows.append({
            "code": code,
            "language": name,
            "script": script,
            "strings": len(keys),
            "of_english": len(keys & english) / len(english),
            "flow": len(keys & set(flow)),
            "core": len(keys & set(core)),
            "reviewed": len(reviewed.get(code, set()) & keys) if code in TRIBAL else None,
        })
    return rows, len(flow), len(core)


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def print_table(rows, n_flow, n_core, markdown: bool) -> None:
    headers = ["Language", "Script", "Strings", "% of English keys",
               f"Citizen flow ({n_flow} keys)", f"Core flow ({n_core} keys)", "Native-reviewed"]
    lines = []
    for r in rows:
        reviewed = "n/a (source)" if r["reviewed"] is None else f"{r['reviewed']} / {r['strings']}"
        lines.append([
            f"{r['language']} ({r['code']})", r["script"], str(r["strings"]), _pct(r["of_english"]),
            f"{r['flow']} ({_pct(r['flow'] / n_flow)})", f"{r['core']} ({_pct(r['core'] / n_core)})", reviewed,
        ])
    if markdown:
        print("| " + " | ".join(headers) + " |")
        print("|" + "|".join(["---"] * 2 + ["---:"] * 5) + "|")
        for line in lines:
            print("| " + " | ".join(line) + " |")
        return
    widths = [max(len(h), *(len(line[i]) for line in lines)) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for line in lines:
        print("  ".join(c.ljust(w) for c, w in zip(line, widths)))


def write_sheets(directory: Path, tables, flow, core, reviewed) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    order = {k: i for i, k in enumerate(flow)}
    for code, name, _ in LANGUAGES:
        if code not in TRIBAL:
            continue
        rows = []
        for key, draft in tables[code].items():
            if key in LEGAL_KEYS:
                priority = "P0 legal/consent"
            elif key in core:
                priority = "P1 core flow"
            else:
                priority = "P2 citizen flow"
            rows.append({
                "priority": priority,
                "key": key,
                "english": tables["en"].get(key, ""),
                "hindi": tables["hi"].get(key, ""),
                "draft": draft,
                "status": "reviewed" if key in reviewed.get(code, set()) else "needs native review",
                "corrected_text": "",
                "reviewer": "",
                "review_date": "",
                "comments": "",
            })
        rows.sort(key=lambda r: (r["priority"], order.get(r["key"], len(order)), r["key"]))
        path = directory / f"review_{code}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {path.relative_to(ROOT)} ({len(rows)} strings, {name})", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Translation coverage per language")
    parser.add_argument("--markdown", action="store_true", help="print a Markdown table")
    parser.add_argument("--sheets", type=Path, help="write CSV review sheets for tribal languages here")
    args = parser.parse_args()

    tables = load_tables()
    flow, core = load_key_list("kCitizenFlowKeys"), load_key_list("kCoreCitizenFlowKeys")
    reviewed = load_reviewed()
    rows, n_flow, n_core = coverage_rows(tables, flow, core, reviewed)
    print_table(rows, n_flow, n_core, args.markdown)
    if args.sheets:
        write_sheets(args.sheets if args.sheets.is_absolute() else ROOT / args.sheets, tables, flow, core, reviewed)


if __name__ == "__main__":
    main()
