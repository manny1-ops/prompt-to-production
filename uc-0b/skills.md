skills:
  - name: retrieve_policy
    description: Loads a .txt policy document and parses it into structured numbered sections keyed by clause id, preserving each clause's full normative text.
    input: policy_path (str: absolute or repo-relative path to a .txt policy file, e.g. ../data/policy-documents/policy_hr_leave.txt).
    output: A dict mapping clause ids (e.g. "2.3") to dicts with 'section' (schema heading, e.g. "ANNUAL LEAVE") and 'text' (normalized full clause text, line-wrapping collapsed).
    error_handling: If the file is missing, unreadable, or contains no clause-numbered lines, raises a parsing error; it never returns a silently empty or partial clause set.

  - name: summarize_policy
    description: Builds a compliant clause-by-clause summary from retrieved policy clauses, applying RICE enforcement checks (all clauses present, all conditions preserved, no invented content), and writes it to a target output file.
    input: clauses (dict from retrieve_policy), required_conditions (dict of clause id -> list of condition keywords that MUST appear), banned_phrases (list of out-of-scope phrases that MUST NOT appear), and output_path (str: destination file path).
    output: Writes summary_hr_leave.txt containing a short scope note followed by every clause id with its condition-preserving digest; returns the list of clauses that were quoted verbatim.
    error_handling: Runs a self-check pass against required_conditions and banned_phrases before writing; if any check fails, raises an EnforcementError listing the exact violations and writes nothing, so a non-compliant summary can never be produced.