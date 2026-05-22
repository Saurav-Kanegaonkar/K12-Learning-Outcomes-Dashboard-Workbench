# Data Dictionary

| File | Grain | Description |
| --- | --- | --- |
| `data/districts.csv` | District | Synthetic district profile with region, SIS, enrollment, FRL rate, and ELL rate. |
| `data/schools.csv` | School | Synthetic schools by district, level, enrollment, and MTSS capacity. |
| `data/student_outcomes.csv` | School-grade-subject-week | Weekly proficiency, growth, chronic absenteeism, assignment completion, and student count. |
| `data/interventions.csv` | School-grade-cycle | MTSS intervention groups, focus areas, enrolled students, response rate, owner, and review cadence. |
| `data/integration_refresh_log.csv` | District-pipeline-week | Refresh status, latency, record completeness, source system, and SIS. |
| `data/data_quality_issues.csv` | Issue | Synthetic SQL check failures and ownership metadata. |
| `data/metric_definitions.csv` | Metric | Business definitions, metric grain, source system, and SQL check mapping. |
| `data/stakeholder_requests.csv` | Request | District stakeholder analytics requests by role, topic, urgency, and status. |
| `analysis/outputs/priority_queue.csv` | Segment | Scored MTSS and learning-outcome priority queue. |
| `analysis/outputs/integration_health.csv` | District-pipeline | Integration-health rollup used by the data-quality surface. |
| `analysis/outputs/district_rollup.csv` | District | Executive district outcomes and readiness rollup. |
| `analysis/outputs/summary.json` | Artifact | Static app payload used by the three surfaces. |
