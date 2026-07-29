Act as adjudicator for two independent Ancient Greek-to-English fidelity reviews
of *Odyssey* 8.1-195.

Read the rubric, reviewer calibration, all files under audit-production/batches/odyssey-08-001-195/sample/,
and audit-production/batches/odyssey-08-001-195/reviews/reviewer-1.md plus reviewer-2.md. Check every
proposal directly against the Greek. Merge duplicates and classify each as
sustained, modified, uncertain, or rejected. Agreement is not proof.
Reject proposals based only on fixed-register wording because the automated
formula audit records those separately.

Return an overall assessment; a findings table using stable IDs
O08-001-195-A-001 onward; rejected/unresolved proposals; severity totals;
Jaccard agreement; findings per 100 records; three successful renderings; and
any calibration implications. After the Markdown, return a fenced JSON object
with schema_version, batch_id, record_count, unresolved_count, a findings array
containing each stable id, severity, and category, and reviewer_proposals maps
for reviewer_1 and reviewer_2. Each proposal entry must contain its review_id
and a shared proposal_key that is identical when the reviews identify the same
issue. Do not supply Jaccard; completion derives it. Do not modify files.
