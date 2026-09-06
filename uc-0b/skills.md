# skills.md

skills:
  - name: retrieve_policy
    description: Loads the Employee Leave Policy text file from disk and parses it into structured clause sections keyed by clause ID, preserving each clause's full normative text.
    input: policy_path (str) — path to the policy text file, e.g. ../data/policy-documents/policy_hr_leave.txt.
    output: A dict mapping each clause ID (e.g. "2.3") to a dict with 'section' (the schema heading, e.g. "ANNUAL LEAVE") and 'text' (the clause's normalized full text with line-wrapping collapsed).
    error_handling: If the file is missing, unreadable, or yields no numbered clauses, raises an error immediately and returns nothing — it never returns a silently partial clause set.

  - name: summarize_policy
    description: Takes the parsed clauses, applies active-voice condensation (~50% length reduction target) to every clause 1.1–8.2, enforces all ground-truth multi-condition rules (14-day notice, Form HR-L1; dual approvers for LWP; 48-hour certificate window; 31 December forfeiture, etc.), and writes the compliant summary to uc-0b/summary_hr_leave.txt.
    input: clauses (dict from retrieve_policy), digests (dict of clause ID -> (active-voice digest text, list of condition keywords that MUST survive)), banned_phrases (list of out-of-scope phrases that MUST NOT appear), output_path (str — destination file).
    output: Writes uc-0b/summary_hr_leave.txt containing a short header plus one line per clause ID with its condensed active-voice digest; returns the list of clauses flagged [QUOTED] verbatim.
    error_handling: Runs a self-check pass BEFORE writing — verifies all 29 clause IDs present, every condition keyword survives in both digest and source, no banned phrase appears, and compression meets the ~30%+ reduction floor. Any failure raises an EnforcementError listing exact violations and writes NO output file, so a non-compliant summary can never be produced.