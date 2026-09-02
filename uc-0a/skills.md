skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint into a standardized municipal category, evaluates severity triggers for priority, provides an evidence-based reason quoting description words, and flags ambiguity.
    input: A dictionary representing a single CSV row with keys 'complaint_id', 'description', and optional metadata fields ('city', 'ward', 'location', 'reported_by', 'days_open').
    output: A dictionary with keys 'complaint_id' (str), 'category' (str: one of 10 allowed categories), 'priority' (str: Urgent, Standard, or Low), 'reason' (str: single sentence citing description words), and 'flag' (str: 'NEEDS_REVIEW' or empty string).
    error_handling: When the description is empty, corrupted, or genuinely ambiguous, sets category to 'Other', priority to 'Standard', reason citing missing/unclear data, and flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads an input CSV file of municipal complaints, applies classify_complaint to each row, validates output consistency against the taxonomy schema, and writes the results to a target CSV file.
    input: input_path (str: path to input CSV file) and output_path (str: path to write results CSV file).
    output: Writes a structured CSV file with columns [complaint_id, category, priority, reason, flag] and prints completion status.
    error_handling: Handles missing input files, missing columns, and bad rows gracefully without terminating the execution loop, logging errors and ensuring output CSV generation for all valid records.
