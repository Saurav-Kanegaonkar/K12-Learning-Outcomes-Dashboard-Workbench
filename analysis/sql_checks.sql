-- District learning outcomes workbench SQL checks

-- 1. Priority queue foundation at school, grade, and subject grain.
with outcome_rollup as (
  select
    district_id,
    school_id,
    grade,
    subject,
    avg(proficiency_rate) as proficiency_rate,
    avg(growth_rate) as growth_rate,
    avg(chronic_absence_rate) as chronic_absence_rate,
    avg(assignment_completion_rate) as assignment_completion_rate,
    sum(student_count) as student_count
  from student_outcomes
  group by 1, 2, 3, 4
)
select *
from outcome_rollup
where proficiency_rate < 0.55
   or chronic_absence_rate > 0.24
order by chronic_absence_rate desc, proficiency_rate asc;

-- 2. Integration reliability by district and pipeline.
select
  district_id,
  pipeline_name,
  avg(case when refresh_status = 'success' then 1 else 0 end) as refresh_success_rate,
  avg(record_completeness) as record_completeness,
  avg(latency_minutes) as avg_latency_minutes
from integration_refresh_log
group by 1, 2
having refresh_success_rate < 0.95
    or record_completeness < 0.97;

-- 3. Open quality issues that should block dashboard publication.
select
  issue_type,
  sql_check,
  severity,
  count(*) as issue_count,
  sum(records_impacted) as records_impacted
from data_quality_issues
where status <> 'resolved'
group by 1, 2, 3
order by records_impacted desc;

-- 4. Stakeholder requests that require metric-definition clarification.
select
  stakeholder_role,
  topic,
  urgency,
  count(*) as request_count
from stakeholder_requests
where status in ('new', 'scoping', 'blocked')
group by 1, 2, 3
order by request_count desc;
