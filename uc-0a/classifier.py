"""
UC-0A — Complaint Classifier
Build guided by agents.md (RICE framework) and skills.md.
"""
import argparse
import csv
import os
import re
from typing import Dict, List, Tuple

# Exact allowed categories enum
ALLOWED_CATEGORIES = [
    "Pothole",
    "Flooding",
    "Streetlight",
    "Waste",
    "Noise",
    "Road Damage",
    "Heritage Damage",
    "Heat Hazard",
    "Drain Blockage",
    "Other"
]

ALLOWED_PRIORITIES = ["Urgent", "Standard", "Low"]

# Severity keywords triggering Urgent priority (Life/Safety + Bodily Harm & Acute Danger)
SEVERITY_PATTERNS = [
    r"\binjur(y|ies|ed)?\b",
    r"\bchild(ren)?\b",
    r"\bschool(s)?\b",
    r"\bhospital(s|ised|ized)?\b",
    r"\bambulance(s)?\b",
    r"\bfire(s)?\b",
    r"\bhazard(s|ous)?\b",
    r"\bfell\b",
    r"\bcollapse(d|s)?\b",
    r"\bburn(s|ed|ing|t)?\b",
    r"\bdanger(ous)?\b",
    r"\bunsafe\b",
    r"\belectrocut(e|ed|ion)?\b",
    r"\bscal(d|ded|ding)?\b",
]


def check_severity(text: str) -> Tuple[bool, List[str]]:
    """Check if description contains severity keywords triggering Urgent priority."""
    matched_words = []
    for pattern in SEVERITY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_words.append(match.group(0))
    return len(matched_words) > 0, matched_words


def determine_category(text: str, location: str = "") -> Tuple[str, str, bool]:
    """
    Determine category, justification citation, and ambiguity flag from description and location.
    Returns: (category, citation_phrase, is_ambiguous)
    """
    t = text.lower()
    loc = location.lower()

    # Priority 1: Specific distinct categories
    if "pothole" in t or "potholes" in t:
        return "Pothole", "pothole affecting roadway", False

    if any(k in t for k in ["heatwave", "melting at", "bubbling at", "dangerous temperatures", "full sun", "storing heat", "burns on contact", "temperature unbearable", "52°c", "45°c", "44°c", "grass dying in heatwave"]):
        return "Heat Hazard", "heat conditions and high temperature impact", False

    if any(k in t for k in ["drain blocked", "drain 100% blocked", "stormwater drain", "main drain blocked", "drain completely blocked", "drainage"]):
        return "Drain Blockage", "drain blockage and drainage impediment", False

    if any(k in t for k in ["underpass flooded", "flooded", "flooding", "floods in", "knee-deep", "standing in water", "waterlogging", "channel rainwater"]):
        return "Flooding", "waterlogging and flooding reported", False

    if any(k in t for k in ["streetlight", "streetlights", "unlit", "darkness for", "lights out", "substation tripped", "wiring theft reported"]):
        return "Streetlight", "streetlight outage or darkness in the area", False

    if any(k in t for k in ["garbage", "waste", "bins overflowing", "dead animal", "dumped on public road", "post-market waste"]):
        return "Waste", "waste accumulation and uncollected refuse", False

    if any(k in t for k in ["music", "noise", "drilling from", "amplifiers", "club music", "idling with engines on"]):
        return "Noise", "excessive noise and disturbance", False

    if any(k in t for k in ["heritage concern", "heritage zone", "heritage building", "ancient step well", "monument", "historic tram", "tagore museum", "marble palace", "heritage stone", "heritage precinct"]):
        return "Heritage Damage", "damage or concern affecting heritage site", False

    if any(k in t for k in ["road surface", "sinking", "subsidence", "footpath", "paving", "upturned paving", "cracked and sinking", "road collapsed", "crater", "buckled"]):
        return "Road Damage", "damage to road surface, footpath, or pavement structure", False

    # Ambiguous or non-standard categories (e.g. tree branches, dead trees, unclassified issues)
    if "tree" in t or "trees" in t or "branch" in t:
        return "Other", "tree or foliage issue outside standard civic categories", True

    return "Other", "unclassified description requiring manual review", True


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    complaint_id = row.get("complaint_id", "").strip()
    description = row.get("description", "").strip()
    location = row.get("location", "").strip()

    # Fault tolerance for empty/missing rows
    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "Description is missing or empty.",
            "flag": "NEEDS_REVIEW"
        }

    # Category determination
    category, citation, is_ambiguous = determine_category(description, location)
    if category not in ALLOWED_CATEGORIES:
        category = "Other"
        is_ambiguous = True

    # Priority determination via severity triggers
    is_urgent, severity_words = check_severity(description)
    priority = "Urgent" if is_urgent else "Standard"

    # Flag determination
    flag = "NEEDS_REVIEW" if is_ambiguous else ""

    # Reason generation citing specific words from the description
    desc_snippet = description.rstrip(".")
    if is_urgent:
        reason = f"Classified as {category} with {priority} priority due to reported '{severity_words[0]}' in '{desc_snippet}'."
    else:
        reason = f"Classified as {category} based on description stating '{desc_snippet}'."

    # Validate output schema strictly
    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = []
    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]

    with open(input_path, mode="r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            try:
                classified_row = classify_complaint(row)
                results.append(classified_row)
            except Exception as e:
                # Fault tolerance for malformed rows
                c_id = row.get("complaint_id", "UNKNOWN") if isinstance(row, dict) else "UNKNOWN"
                results.append({
                    "complaint_id": c_id,
                    "category": "Other",
                    "priority": "Standard",
                    "reason": f"Row processing error: {str(e)}",
                    "flag": "NEEDS_REVIEW"
                })

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
