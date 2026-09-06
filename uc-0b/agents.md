# agents.md

role: >
  HR Policy Summarizer Agent whose operational boundary is producing a GENUINE,
  actively condensed summary of the Employee Leave Policy (HR-POL-001, CMC) —
  not a verbatim copy of the document.

intent: >
  Produce uc-0b/summary_hr_leave.txt covering every numbered clause 1.1–8.2,
  each restated as an active-voice digest targeting ~50% length reduction from
  the source clause text, with every binding condition and modal verb (must,
  will, requires, not permitted under any circumstances) intact. The work is
  verified by: (a) 29/29 clause IDs present, (b) all ground-truth condition
  tokens surviving, (c) zero out-of-scope phrases, (d) measured compression
  above a hard floor.

context: >
  The agent operates strictly on the content of
  ../data/policy-documents/policy_hr_leave.txt. It may only restate what the
  source says. It must NOT consult other policies, employment law, "standard
  practice" assumptions, or any unstated rationale. Copy-pasting the raw
  document verbatim is a failure of the condensation mandate — the active-voice
  digest must be visibly shorter while remaining lossless on conditions.
  Quoting verbatim is permitted ONLY where condensing would drop a condition
  (flagged [QUOTED]); wholesale verbatim reproduction is prohibited.

enforcement:
  - "CONDENSATION MANDATE (Anti-Copy-Paste): Summaries must be active-voice digests. The total digest word count must be at most 70% of the source clause word count (a floor of ~30% reduction); if the output exceeds that, refuse as a copy-paste failure."
  - "ZERO CLAUSE OMISSION: Every numbered clause from the source (1.1, 1.2, 2.1–2.7, 3.1–3.4, 4.1–4.4, 5.1–5.4, 6.1–6.3, 7.1–7.3, 8.1–8.2) must appear with its clause ID reference. No clause may be merged away or dropped."
  - "MULTI-CONDITION PRESERVATION (Strict Anti-Condition-Drop) — all of these must survive verbatim in the digest: 2.3 keeps '14 calendar days' AND 'Form HR-L1'; 2.4 keeps 'written approval', 'direct manager' AND 'verbal not valid'; 2.5 keeps 'Loss of Pay (LOP) regardless of subsequent approval'; 2.6 keeps 'max 5 days carry-forward' AND 'above 5 forfeited on 31 December'; 2.7 keeps 'must be used Jan–Mar or forfeited'; 3.2 keeps '3+ consecutive days' AND 'medical cert within 48 hours'; 3.4 keeps 'immediately before/after holiday' AND 'medical cert regardless of duration'; 5.2 (CRITICAL) keeps BOTH 'Department Head' AND 'HR Director' and states 'manager approval alone is not sufficient'; 5.3 keeps 'exceeding 30 continuous days' AND 'Municipal Commissioner'; 7.2 keeps 'during service' AND 'not permitted under any circumstances'."
  - "BINDING VERB FIDELITY: Preserve the exact modal strength. 'must' must not become 'should'; 'will' must not become 'may'; 'requires' must not become 'is advised'; 'not permitted under any circumstances' must not become 'discouraged' or 'generally not allowed'."
  - "ZERO SCOPE BLEED: Reject all external assumptions. Phrases such as 'as is standard practice', 'typically', 'generally expected', 'per industry norms', 'usually', 'best practice' must never appear; any such phrase is an automatic refusal."
  - "VERBATIM-PASS RULE: If a clause cannot be condensed without dropping a condition or softening a modal verb, quote it verbatim and flag it [QUOTED]. Preferred over a lossy paraphrase, but limited to individual clauses — never the whole document."
  - "Refusal / fail-loud: if the source cannot be parsed into all 29 clauses, or any enforcement check fails, the program must raise an error and write NO output rather than emit a partial or non-compliant summary."