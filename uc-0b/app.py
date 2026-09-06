"""
UC-0B app.py — Summary That Changes Meaning
Build guided by agents.md (RICE framework) and skills.md.

Failure modes targeted:
  - Clause omission           -> every numbered clause must appear
  - Scope bleed               -> no invented phrases in output
  - Obligation softening      -> every condition keyword must survive
  - Condition drop            -> multi-approver / multi-condition clauses checked
"""
import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Source policy
# ---------------------------------------------------------------------------
POLICY_PATH = "../data/policy-documents/policy_hr_leave.txt"

# ---------------------------------------------------------------------------
# Curated digests. Each digest is verified against the parsed source clauses,
# so it cannot silently drift from the document it summarises.
# key: required condition keywords that MUST appear in the digest (anti-softening)
# value: (digest_text, [required_condition_keywords])
# ---------------------------------------------------------------------------
DIGESTS: Dict[str, Tuple[str, List[str]]] = {
    "1.1": ("This policy governs all leave entitlements for permanent and contractual "
            "employees of the City Municipal Corporation (CMC).",
            ["permanent", "contractual"]),
    "1.2": ("This policy does not apply to daily wage workers or consultants; those "
            "categories are governed by their respective contracts.",
            ["daily wage", "consultants", "respective contracts"]),
    "2.1": ("Each permanent employee is entitled to 18 days of paid annual leave per "
            "calendar year.",
            ["18", "annual leave"]),
    "2.2": ("Annual leave accrues at 1.5 days per month from the date of joining.",
            ["1.5", "per month"]),
    "2.3": ("Employees must submit a leave application at least 14 calendar days in "
            "advance using Form HR-L1.",
            ["14 calendar days", "Form HR-L1"]),
    "2.4": ("Leave applications must receive written approval from the employee's direct "
            "manager before the leave commences; verbal approval is not valid.",
            ["written approval", "direct manager", "verbal approval is not valid"]),
    "2.5": ("Unapproved absence will be recorded as Loss of Pay (LOP) regardless of "
            "subsequent approval.",
            ["Loss of Pay", "regardless of subsequent approval"]),
    "2.6": ("Employees may carry forward a maximum of 5 unused annual leave days to the "
            "following calendar year; any days above 5 are forfeited on 31 December.",
            ["5 unused", "forfeited on 31 December"]),
    "2.7": ("Carry-forward days must be used within the first quarter (January–March) of "
            "the following year or they are forfeited.",
            ["first quarter", "January", "March", "forfeited"]),
    "3.1": ("Each employee is entitled to 12 days of paid sick leave per calendar year.",
            ["12"]),
    "3.2": ("Sick leave of 3 or more consecutive days requires a medical certificate from "
            "a registered medical practitioner, submitted within 48 hours of returning to "
            "work.",
            ["3 or more consecutive days", "registered medical practitioner", "48 hours"]),
    "3.3": ("Sick leave cannot be carried forward to the following year.",
            ["cannot be carried forward"]),
    "3.4": ("Sick leave taken immediately before or after a public holiday or annual leave "
            "period requires a medical certificate regardless of duration.",
            ["public holiday", "annual leave", "regardless of duration"]),
    "4.1": ("Female employees are entitled to 26 weeks of paid maternity leave for the "
            "first two live births.",
            ["26 weeks", "first two live births"]),
    "4.2": ("For a third or subsequent child, maternity leave is 12 weeks paid.",
            ["third or subsequent", "12 weeks"]),
    "4.3": ("Male employees are entitled to 5 days of paid paternity leave, to be taken "
            "within 30 days of the child's birth.",
            ["5 days", "30 days", "paternity"]),
    "4.4": ("Paternity leave cannot be split across multiple periods.",
            ["cannot be split"]),
    "5.1": ("An employee may apply for Leave Without Pay only after exhausting all "
            "applicable paid leave entitlements.",
            ["Leave Without Pay", "exhausting all applicable paid leave"]),
    "5.2": ("LWP requires approval from the Department Head and the HR Director; manager "
            "approval alone is not sufficient.",
            ["Department Head", "HR Director", "not sufficient"]),
    "5.3": ("LWP exceeding 30 continuous days requires approval from the Municipal "
            "Commissioner.",
            ["30 continuous days", "Municipal Commissioner"]),
    "5.4": ("Periods of LWP do not count toward service for the purposes of seniority, "
            "increments, or retirement benefits.",
            ["seniority", "increments", "retirement benefits"]),
    "6.1": ("Employees are entitled to all gazetted public holidays as declared by the "
            "State Government each year.",
            ["gazetted", "State Government"]),
    "6.2": ("If an employee is required to work on a public holiday, they are entitled to "
            "one compensatory off day, to be taken within 60 days of the holiday worked.",
            ["60 days", "compensatory off"]),
    "6.3": ("Compensatory off cannot be encashed.",
            ["cannot be encashed"]),
    "7.1": ("Annual leave may be encashed only at the time of retirement or resignation, "
            "subject to a maximum of 60 days.",
            ["retirement or resignation", "maximum of 60 days"]),
    "7.2": ("Leave encashment during service is not permitted under any circumstances.",
            ["during service is not permitted", "under any circumstances"]),
    "7.3": ("Sick leave and LWP cannot be encashed under any circumstances.",
            ["cannot be encashed", "under any circumstances"]),
    "8.1": ("Leave-related grievances must be raised with the HR Department within 10 "
            "working days of the disputed decision.",
            ["10 working days", "HR Department"]),
    "8.2": ("Grievances raised after 10 working days will not be considered unless "
            "exceptional circumstances are demonstrated in writing.",
            ["10 working days", "exceptional circumstances", "in writing"]),
}

# Scope-bleed phrases. These MUST NOT appear in the output because they are not
# present in the source document.
BANNED_PHRASES: List[str] = [
    "as is standard practice",
    "typically",
    "generally expected",
    "standard practice",
    "industry norms",
    "best practice",
    "usually",
]


class EnforcementError(Exception):
    """Raised when the summary fails a RICE enforcement check. Fail loudly."""


# ---------------------------------------------------------------------------
# Skill: retrieve_policy
# ---------------------------------------------------------------------------
def retrieve_policy(policy_path: str) -> Dict[str, Dict[str, str]]:
    """Parse a .txt policy into {clause_id: {'section': heading, 'text': full text}}."""
    if not os.path.exists(policy_path):
        raise FileNotFoundError(f"Input policy file not found: {policy_path}")

    clauses: Dict[str, Dict[str, str]] = {}
    current_section = ""
    current_id = None
    current_lines: List[str] = []

    def flush():
        nonlocal current_id, current_lines
        if current_id is not None and current_lines:
            clauses[current_id] = {
                "section": current_section,
                "text": " ".join(line.strip() for line in current_lines).strip(),
            }
        current_id = None
        current_lines = []

    clause_re = re.compile(r"^(\d+\.\d+)\s+(.+)$")
    with open(policy_path, mode="r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.strip().startswith("═") or not line.strip():
                flush()
                continue
            sec_match = re.match(r"^\d+\.\s+([A-Z][A-Z\s]+)$", line.strip())
            if sec_match:
                flush()
                current_section = sec_match.group(1).strip()
                continue
            clause_match = clause_re.match(line.strip())
            if clause_match:
                flush()
                current_id = clause_match.group(1)
                current_lines = [clause_match.group(2)]
                continue
            if current_id is not None:
                current_lines.append(line.strip())
    flush()

    if not clauses:
        raise ValueError(f"No numbered clauses parsed from {policy_path}")
    return clauses


# ---------------------------------------------------------------------------
# Skill: summarize_policy
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _verify_digest_against_source(clauses, digest: str, keywords: List[str],
                                  clause_id: str) -> List[str]:
    """Each required condition keyword must exist in BOTH digest and source text."""
    violations = []
    source_text = clauses[clause_id]["text"]
    src_norm = _normalize(source_text)
    dig_norm = _normalize(digest)
    for kw in keywords:
        kw_norm = _normalize(kw)
        if kw_norm not in dig_norm:
            violations.append(
                f"clause {clause_id}: condition '{kw}' dropped from digest")
        elif kw_norm not in src_norm:
            violations.append(
                f"clause {clause_id}: condition '{kw}' not traceable to source")
    return violations


def _is_verbatim_quote(clauses, clause_id: str, digest: str) -> bool:
    """Flag [QUOTED] when the digest is verbatim vs the source clause text."""
    src_norm = _normalize(clauses[clause_id]["text"])
    dig_norm = _normalize(digest)
    return dig_norm == src_norm or dig_norm in src_norm


def summarize_policy(clauses: Dict[str, Dict[str, str]], output_path: str) -> List[str]:
    """Build, verify, and write the compliant summary. Verifies before writing."""
    parsed_ids = set(clauses.keys())
    expected_ids = set(DIGESTS.keys())

    missing = sorted(expected_ids - parsed_ids)
    if missing:
        raise EnforcementError(
            f"Refusal: source is missing clauses {missing} — cannot produce "
            "a complete summary.")

    # 1. Every numbered clause must be present, no invented clauses.
    if expected_ids != parsed_ids:
        extra = sorted(parsed_ids - expected_ids)
        raise EnforcementError(
            f"Refusal: parsed clauses not present in inventory {extra} — "
            "refuse rather than emit unverified content.")

    violations: List[str] = []
    quoted: List[str] = []

    # 2. Condition preservation + 3. no invented content, checked per clause.
    digest_lines: List[str] = []
    for clause_id in sorted(expected_ids, key=lambda c: (int(c.split(".")[0]),
                                                         int(c.split(".")[1]))):
        digest, keywords = DIGESTS[clause_id]
        violations += _verify_digest_against_source(clauses, digest, keywords, clause_id)
        flag = " [QUOTED]" if _is_verbatim_quote(clauses, clause_id, digest) else ""
        if flag:
            quoted.append(clause_id)
        digest_lines.append(f"{clause_id}  {digest}{flag}")

    # 3. Scope bleed: banned phrases checked against entire output.
    full_output = "\n".join(digest_lines).lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in full_output:
            violations.append(f"scope bleed: invented phrase '{phrase}' present")

    if violations:
        raise EnforcementError(
            "Enforcement failed — no summary written.\n  " + "\n  ".join(violations))

    # 4. Gate: only write a fully compliant summary.
    header = [
        "CITY MUNICIPAL CORPORATION — HR DEPARTMENT",
        "EMPLOYEE LEAVE POLICY (HR-POL-001, v2.3) — COMPLIANT SUMMARY",
        "Generated from: ../data/policy-documents/policy_hr_leave.txt",
        "Ground rules: every numbered clause present; all binding conditions preserved;"
        " no content beyond the source document.",
        "Clauses marked [QUOTED] are reproduced verbatim where paraphrasing would "
        "risk meaning loss.",
        "",
    ]

    lines = header + digest_lines
    with open(output_path, mode="w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"Done. Compliant summary written to {output_path}")
    print(f"  clauses covered: {len(expected_ids)}")
    print(f"  quoted verbatim : {', '.join(quoted) if quoted else 'none'}")
    return quoted


def main():
    parser = argparse.ArgumentParser(description="UC-0B HR Leave Policy Summarizer")
    parser.add_argument("--input", default=POLICY_PATH,
                        help="Path to policy_hr_leave.txt")
    parser.add_argument("--output", default="summary_hr_leave.txt",
                        help="Path to write summary output")
    args = parser.parse_args()

    try:
        clauses = retrieve_policy(args.input)
        summarize_policy(clauses, args.output)
    except (EnforcementError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()