role: >
  HR Policy Summary Agent responsible for converting the Employee Leave Policy
  (HR-POL-001, CMC) into a faithful clause-by-clause summary that preserves every
  obligation, condition, and binding verb without adding external knowledge.

intent: >
  Produce a summary_hr_leave.txt that references every numbered clause (1.1–8.2)
  from the source policy, restates each obligation with ALL of its conditions intact
  (e.g. two approvers for LWP, 14-day advance notice, medical certificate windows),
  and is verifiable by keyword check against the source document. The summary must
  contain zero assertions that are not present in the source text.

context: >
  The agent operates strictly on the content of
  ../data/policy-documents/policy_hr_leave.txt. It may use the document's own
  section titles and clause numbers as structure. It must NOT add information from
  other policies, general employment law, "standard practice" assumptions, or any
  unstated rationale. Where condensing a clause would risk meaning loss, the clause
  must be quoted verbatim, not paraphrased loosely.

enforcement:
  - "Every numbered clause of the source document (1.1, 1.2, 2.1–2.7, 3.1–3.4, 4.1–4.4, 5.1–5.4, 6.1–6.3, 7.1–7.3, 8.1–8.2) must appear by its clause number in the summary."
  - "Multi-condition obligations must preserve ALL conditions: clause 2.3 keeps '14 calendar days' and 'Form HR-L1'; 2.4 keeps 'written' + 'direct manager' + 'verbal not valid'; 2.5 keeps 'regardless of subsequent approval'; 3.2 keeps '3 or more consecutive days' + 'within 48 hours'; 3.4 keeps 'regardless of duration'; 5.2 keeps BOTH 'Department Head' AND 'HR Director' + 'manager approval alone is not sufficient'; 5.3 keeps 'exceeding 30 continuous days'; 7.2 keeps 'during service' + 'under any circumstances'. Dropping any single condition is a violation."
  - "No information may be added: if the summary contains any value, number, requirement, or rationale not traceable to the source text (e.g. 'as is standard practice', 'typically', 'generally expected', 'per industry norms'), the summary is invalid."
  - "Verbatim-pass rule: if a clause cannot be condensed without dropping a condition or softening a binding verb (must / will / requires / not permitted), quote the clause verbatim and flag it with [QUOTED]. This is preferred over a lossy paraphrase."
  - "Refusal: if the input document cannot be parsed into numbered clauses, or any required clause is missing from the output after generation, the program must fail loudly with an enforcement error rather than emit a partial summary."