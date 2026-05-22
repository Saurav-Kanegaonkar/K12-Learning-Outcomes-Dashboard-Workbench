import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "analysis" / "outputs"
ANALYSIS = ROOT / "analysis"

random.seed(42)


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def clamp(value, low, high):
    return max(low, min(high, value))


districts = [
    {
        "district_id": "DST001",
        "district_name": "North Valley Unified",
        "region": "West",
        "sis": "PowerSchool",
        "enrollment": 41200,
        "frl_rate": 0.48,
        "ell_rate": 0.17,
    },
    {
        "district_id": "DST002",
        "district_name": "Lakefront Public Schools",
        "region": "Midwest",
        "sis": "Infinite Campus",
        "enrollment": 27600,
        "frl_rate": 0.39,
        "ell_rate": 0.11,
    },
    {
        "district_id": "DST003",
        "district_name": "Pine County Schools",
        "region": "Southeast",
        "sis": "Skyward",
        "enrollment": 18900,
        "frl_rate": 0.61,
        "ell_rate": 0.08,
    },
    {
        "district_id": "DST004",
        "district_name": "Canyon Ridge USD",
        "region": "Southwest",
        "sis": "Aeries",
        "enrollment": 33200,
        "frl_rate": 0.54,
        "ell_rate": 0.24,
    },
    {
        "district_id": "DST005",
        "district_name": "Harbor City Schools",
        "region": "Northeast",
        "sis": "PowerSchool",
        "enrollment": 52100,
        "frl_rate": 0.44,
        "ell_rate": 0.19,
    },
    {
        "district_id": "DST006",
        "district_name": "Mesa Vista Public Schools",
        "region": "Mountain",
        "sis": "Infinite Campus",
        "enrollment": 14600,
        "frl_rate": 0.57,
        "ell_rate": 0.21,
    },
]

school_levels = [
    ("Elementary", [3, 4, 5]),
    ("Middle", [6, 7, 8]),
    ("High", [9, 10]),
]
subjects = ["ELA", "Math", "Science"]
weeks = [f"2026-W{week:02d}" for week in range(4, 17)]


def build_schools():
    rows = []
    school_index = 1
    for district in districts:
        for level, _grades in school_levels:
            count = {"Elementary": 4, "Middle": 2, "High": 1}[level]
            for n in range(count):
                enrollment_base = {"Elementary": 620, "Middle": 880, "High": 1560}[level]
                rows.append(
                    {
                        "school_id": f"SCH{school_index:03d}",
                        "district_id": district["district_id"],
                        "school_name": f"{district['district_name'].split()[0]} {level} {n + 1}",
                        "level": level,
                        "enrollment": int(random.normalvariate(enrollment_base, enrollment_base * 0.12)),
                        "mtss_tier2_capacity": random.randint(68, 148),
                        "mtss_tier3_capacity": random.randint(12, 38),
                    }
                )
                school_index += 1
    return rows


def build_metric_definitions():
    return [
        {
            "metric_id": "M001",
            "metric_name": "ELA proficiency",
            "domain": "Assessment",
            "grain": "school_grade_subject_week",
            "business_definition": "Percent of students at or above expected performance band.",
            "source_system": "Formative assessment platform",
            "sql_check": "valid_score_band",
        },
        {
            "metric_id": "M002",
            "metric_name": "Math proficiency",
            "domain": "Assessment",
            "grain": "school_grade_subject_week",
            "business_definition": "Percent of students at or above expected performance band.",
            "source_system": "Formative assessment platform",
            "sql_check": "valid_score_band",
        },
        {
            "metric_id": "M003",
            "metric_name": "Chronic absenteeism",
            "domain": "Attendance",
            "grain": "school_grade_week",
            "business_definition": "Share of students on pace to miss 10 percent or more of school days.",
            "source_system": "Student information system",
            "sql_check": "attendance_day_completeness",
        },
        {
            "metric_id": "M004",
            "metric_name": "Assignment engagement",
            "domain": "Instruction",
            "grain": "school_grade_subject_week",
            "business_definition": "Share of assigned activities completed by active students.",
            "source_system": "Instructional content platform",
            "sql_check": "assignment_event_completeness",
        },
        {
            "metric_id": "M005",
            "metric_name": "Intervention response",
            "domain": "MTSS",
            "grain": "school_grade_intervention_cycle",
            "business_definition": "Percent of active intervention groups showing expected progress.",
            "source_system": "Intervention tracking system",
            "sql_check": "active_roster_alignment",
        },
    ]


def build_outcomes(schools):
    rows = []
    district_lookup = {d["district_id"]: d for d in districts}
    for school in schools:
        district = district_lookup[school["district_id"]]
        level_grades = dict(school_levels)[school["level"]]
        for week_index, week in enumerate(weeks):
            for grade in level_grades:
                for subject in subjects:
                    equity_pressure = district["frl_rate"] * 10 + district["ell_rate"] * 6
                    level_drag = {"Elementary": -0.01, "Middle": 0.03, "High": 0.06}[school["level"]]
                    subject_drag = {"ELA": 0.00, "Math": 0.045, "Science": 0.025}[subject]
                    weekly_recovery = week_index * random.uniform(0.002, 0.006)
                    baseline = 0.69 - level_drag - subject_drag - equity_pressure / 100 + weekly_recovery
                    proficiency = clamp(random.normalvariate(baseline, 0.055), 0.28, 0.91)
                    growth = clamp(random.normalvariate(0.54 + weekly_recovery * 2, 0.09), 0.20, 0.86)
                    chronic_absence = clamp(
                        random.normalvariate(0.17 + district["frl_rate"] * 0.12 + level_drag, 0.045),
                        0.035,
                        0.44,
                    )
                    assignment_completion = clamp(
                        random.normalvariate(0.76 - chronic_absence * 0.42 - subject_drag, 0.07),
                        0.36,
                        0.96,
                    )
                    roster_count = max(22, int(random.normalvariate(school["enrollment"] / len(level_grades) / 3, 16)))
                    rows.append(
                        {
                            "week": week,
                            "district_id": school["district_id"],
                            "school_id": school["school_id"],
                            "grade": grade,
                            "subject": subject,
                            "student_count": roster_count,
                            "proficiency_rate": round(proficiency, 3),
                            "growth_rate": round(growth, 3),
                            "chronic_absence_rate": round(chronic_absence, 3),
                            "assignment_completion_rate": round(assignment_completion, 3),
                        }
                    )
    return rows


def build_interventions(schools):
    focus_options = ["Reading fluency", "Math foundations", "Attendance outreach", "ELL vocabulary", "Credit recovery"]
    rows = []
    for cycle in range(1, 5):
        for school in schools:
            for grade in dict(school_levels)[school["level"]]:
                for lane in random.sample(focus_options, 2):
                    enrolled = random.randint(12, 54)
                    response = clamp(random.normalvariate(0.55 + (cycle * 0.025), 0.13), 0.18, 0.88)
                    rows.append(
                        {
                            "cycle": f"2026-C{cycle}",
                            "district_id": school["district_id"],
                            "school_id": school["school_id"],
                            "grade": grade,
                            "focus_area": lane,
                            "students_enrolled": enrolled,
                            "response_rate": round(response, 3),
                            "owner_role": random.choice(["Director of MTSS", "Principal", "Instructional coach", "Attendance lead"]),
                            "next_review_days": random.choice([7, 14, 21, 28]),
                        }
                    )
    return rows


def build_integration_logs():
    rows = []
    systems = [
        ("SIS roster sync", "Student information system"),
        ("Assessment feed", "Formative assessment platform"),
        ("Attendance extract", "Student information system"),
        ("Assignment events", "Instructional content platform"),
        ("Intervention roster", "Intervention tracking system"),
    ]
    for district in districts:
        for week in weeks:
            for pipeline_name, system_type in systems:
                base_success = 0.965
                if district["sis"] == "Skyward" and "Attendance" in pipeline_name:
                    base_success -= 0.045
                if district["sis"] == "Aeries" and "SIS" in pipeline_name:
                    base_success -= 0.035
                status = "success" if random.random() < base_success else random.choice(["late", "failed", "partial"])
                latency = max(8, random.normalvariate(44, 18))
                if status != "success":
                    latency += random.uniform(35, 140)
                completeness = clamp(random.normalvariate(0.984, 0.018), 0.82, 1.0)
                if status in ["partial", "failed"]:
                    completeness -= random.uniform(0.05, 0.18)
                rows.append(
                    {
                        "week": week,
                        "district_id": district["district_id"],
                        "sis": district["sis"],
                        "pipeline_name": pipeline_name,
                        "system_type": system_type,
                        "refresh_status": status,
                        "latency_minutes": round(latency, 1),
                        "record_completeness": round(clamp(completeness, 0.65, 1.0), 3),
                    }
                )
    return rows


def build_quality_issues(schools):
    issue_types = [
        ("Roster mismatch", "active_roster_alignment"),
        ("Missing attendance day", "attendance_day_completeness"),
        ("Invalid score band", "valid_score_band"),
        ("Duplicate assignment event", "assignment_event_completeness"),
        ("Metric definition drift", "metric_definition_control"),
    ]
    rows = []
    for issue_id in range(1, 241):
        school = random.choice(schools)
        issue_type, sql_check = random.choice(issue_types)
        severity = random.choices(["Low", "Medium", "High", "Critical"], weights=[38, 36, 20, 6])[0]
        records = int(random.lognormvariate(4.4, 0.78))
        rows.append(
            {
                "issue_id": f"DQ{issue_id:03d}",
                "district_id": school["district_id"],
                "school_id": school["school_id"],
                "issue_type": issue_type,
                "severity": severity,
                "sql_check": sql_check,
                "records_impacted": records,
                "status": random.choices(["open", "in review", "resolved"], weights=[31, 24, 45])[0],
                "detected_week": random.choice(weeks),
                "owner_team": random.choice(["Analytics", "Data engineering", "Customer success", "District data steward"]),
            }
        )
    return rows


def build_requests():
    topics = [
        "Board-ready proficiency trend",
        "Attendance intervention list",
        "Metric definition review",
        "School comparison packet",
        "MTSS cycle impact",
        "Roster sync question",
    ]
    rows = []
    for request_id in range(1, 121):
        district = random.choice(districts)
        rows.append(
            {
                "request_id": f"REQ{request_id:03d}",
                "district_id": district["district_id"],
                "stakeholder_role": random.choice(["Assistant superintendent", "Principal", "Data director", "Curriculum lead"]),
                "topic": random.choice(topics),
                "urgency": random.choice(["routine", "this week", "board meeting", "state reporting"]),
                "status": random.choices(["new", "scoping", "delivered", "blocked"], weights=[17, 25, 47, 11])[0],
                "days_to_due": random.choice([2, 3, 5, 7, 10, 14, 21]),
            }
        )
    return rows


def score_artifact(districts, schools, outcomes, interventions, logs, issues, requests):
    school_lookup = {school["school_id"]: school for school in schools}
    district_lookup = {district["district_id"]: district for district in districts}
    by_segment = defaultdict(list)
    for row in outcomes:
        key = (row["district_id"], row["school_id"], row["grade"], row["subject"])
        by_segment[key].append(row)

    intervention_lookup = defaultdict(list)
    for row in interventions:
        key = (row["district_id"], row["school_id"], row["grade"])
        intervention_lookup[key].append(row)

    issue_lookup = defaultdict(list)
    for row in issues:
        issue_lookup[(row["district_id"], row["school_id"])].append(row)

    pipeline_health = defaultdict(lambda: {"runs": 0, "success": 0, "complete": 0.0, "latency": 0.0, "failures": 0})
    for row in logs:
        bucket = pipeline_health[(row["district_id"], row["pipeline_name"])]
        bucket["runs"] += 1
        bucket["success"] += 1 if row["refresh_status"] == "success" else 0
        bucket["failures"] += 0 if row["refresh_status"] == "success" else 1
        bucket["complete"] += row["record_completeness"]
        bucket["latency"] += row["latency_minutes"]

    queue = []
    for key, rows in by_segment.items():
        district_id, school_id, grade, subject = key
        student_count = sum(row["student_count"] for row in rows) / len(rows)
        proficiency = sum(row["proficiency_rate"] for row in rows) / len(rows)
        growth = sum(row["growth_rate"] for row in rows) / len(rows)
        absence = sum(row["chronic_absence_rate"] for row in rows) / len(rows)
        completion = sum(row["assignment_completion_rate"] for row in rows) / len(rows)
        active_interventions = intervention_lookup[(district_id, school_id, grade)]
        avg_response = (
            sum(row["response_rate"] for row in active_interventions) / len(active_interventions)
            if active_interventions
            else 0.0
        )
        open_issues = [issue for issue in issue_lookup[(district_id, school_id)] if issue["status"] != "resolved"]
        issue_penalty = sum({"Low": 1, "Medium": 2, "High": 4, "Critical": 7}[issue["severity"]] for issue in open_issues)
        readiness = clamp(100 - issue_penalty * 1.8 - absence * 42 + avg_response * 18, 5, 100)
        need_score = (
            (1 - proficiency) * 34
            + (1 - growth) * 18
            + absence * 24
            + (1 - completion) * 14
            + math.log(student_count + 1) * 2
        )
        priority_score = need_score * 1.6 + (100 - readiness) * 0.42
        if avg_response < 0.47:
            recommended_action = "Rebuild intervention group and confirm owner"
        elif absence > 0.24:
            recommended_action = "Launch attendance outreach with weekly monitoring"
        elif proficiency < 0.55:
            recommended_action = "Schedule district metric review and intervention plan"
        elif open_issues:
            recommended_action = "Run SQL validation before publishing"
        else:
            recommended_action = "Keep in standard dashboard review"
        queue.append(
            {
                "district_id": district_id,
                "district_name": district_lookup[district_id]["district_name"],
                "sis": district_lookup[district_id]["sis"],
                "school_id": school_id,
                "school_name": school_lookup[school_id]["school_name"],
                "level": school_lookup[school_id]["level"],
                "grade": grade,
                "subject": subject,
                "student_count": round(student_count),
                "proficiency_rate": round(proficiency, 3),
                "growth_rate": round(growth, 3),
                "chronic_absence_rate": round(absence, 3),
                "assignment_completion_rate": round(completion, 3),
                "intervention_response_rate": round(avg_response, 3),
                "open_quality_issues": len(open_issues),
                "readiness_score": round(readiness, 1),
                "priority_score": round(priority_score, 1),
                "recommended_action": recommended_action,
            }
        )

    queue.sort(key=lambda row: row["priority_score"], reverse=True)

    integration_rows = []
    for (district_id, pipeline_name), bucket in pipeline_health.items():
        success_rate = bucket["success"] / bucket["runs"]
        completeness = bucket["complete"] / bucket["runs"]
        latency = bucket["latency"] / bucket["runs"]
        health_score = clamp(success_rate * 58 + completeness * 32 + max(0, 1 - latency / 180) * 10, 0, 100)
        integration_rows.append(
            {
                "district_id": district_id,
                "district_name": district_lookup[district_id]["district_name"],
                "sis": district_lookup[district_id]["sis"],
                "pipeline_name": pipeline_name,
                "success_rate": round(success_rate, 3),
                "avg_record_completeness": round(completeness, 3),
                "avg_latency_minutes": round(latency, 1),
                "failed_or_late_runs": bucket["failures"],
                "health_score": round(health_score, 1),
            }
        )
    integration_rows.sort(key=lambda row: row["health_score"])

    district_rollup = []
    for district in districts:
        district_segments = [row for row in queue if row["district_id"] == district["district_id"]]
        district_logs = [row for row in logs if row["district_id"] == district["district_id"]]
        district_issues = [row for row in issues if row["district_id"] == district["district_id"] and row["status"] != "resolved"]
        requests_open = [row for row in requests if row["district_id"] == district["district_id"] and row["status"] != "delivered"]
        district_rollup.append(
            {
                "district_id": district["district_id"],
                "district_name": district["district_name"],
                "sis": district["sis"],
                "enrollment": district["enrollment"],
                "avg_proficiency_rate": round(sum(row["proficiency_rate"] for row in district_segments) / len(district_segments), 3),
                "avg_growth_rate": round(sum(row["growth_rate"] for row in district_segments) / len(district_segments), 3),
                "chronic_absence_rate": round(sum(row["chronic_absence_rate"] for row in district_segments) / len(district_segments), 3),
                "avg_readiness_score": round(sum(row["readiness_score"] for row in district_segments) / len(district_segments), 1),
                "critical_segments": len([row for row in district_segments if row["priority_score"] >= 78]),
                "open_quality_issues": len(district_issues),
                "refresh_success_rate": round(
                    len([row for row in district_logs if row["refresh_status"] == "success"]) / len(district_logs), 3
                ),
                "open_stakeholder_requests": len(requests_open),
            }
        )
    district_rollup.sort(key=lambda row: (row["critical_segments"], row["open_quality_issues"]), reverse=True)

    total_students = sum(district["enrollment"] for district in districts)
    summary = {
        "generated_at": "2026-05-22",
        "portfolio": {
            "districts": len(districts),
            "schools": len(schools),
            "students_modeled": total_students,
            "segments_scored": len(queue),
            "weekly_outcome_rows": len(outcomes),
            "active_intervention_groups": len(interventions),
            "integration_runs": len(logs),
            "quality_issues": len(issues),
            "open_quality_issues": len([row for row in issues if row["status"] != "resolved"]),
            "stakeholder_requests": len(requests),
            "refresh_success_rate": round(len([row for row in logs if row["refresh_status"] == "success"]) / len(logs), 3),
            "avg_readiness_score": round(sum(row["readiness_score"] for row in queue) / len(queue), 1),
            "avg_proficiency_rate": round(sum(row["proficiency_rate"] for row in queue) / len(queue), 3),
            "chronic_absence_rate": round(sum(row["chronic_absence_rate"] for row in queue) / len(queue), 3),
        },
        "district_rollup": district_rollup,
        "priority_queue": queue[:24],
        "integration_health": integration_rows[:18],
        "quality_issue_mix": issue_mix(issues),
        "request_mix": request_mix(requests),
        "top_actions": action_mix(queue),
        "method_note": "Synthetic district, SIS, assessment, attendance, intervention, and quality-control data modeled on common K-12 reporting workflows.",
    }
    return queue, integration_rows, district_rollup, summary


def issue_mix(issues):
    grouped = defaultdict(lambda: {"count": 0, "records": 0, "open": 0})
    for row in issues:
        bucket = grouped[row["issue_type"]]
        bucket["count"] += 1
        bucket["records"] += row["records_impacted"]
        bucket["open"] += 1 if row["status"] != "resolved" else 0
    return [
        {"issue_type": issue_type, "count": values["count"], "records_impacted": values["records"], "open": values["open"]}
        for issue_type, values in sorted(grouped.items(), key=lambda item: item[1]["open"], reverse=True)
    ]


def request_mix(requests):
    grouped = defaultdict(int)
    for row in requests:
        grouped[row["topic"]] += 1
    return [{"topic": topic, "requests": count} for topic, count in sorted(grouped.items(), key=lambda item: item[1], reverse=True)]


def action_mix(queue):
    grouped = defaultdict(lambda: {"count": 0, "avg_priority": 0.0})
    for row in queue:
        bucket = grouped[row["recommended_action"]]
        bucket["count"] += 1
        bucket["avg_priority"] += row["priority_score"]
    return [
        {"recommended_action": action, "segments": values["count"], "avg_priority": round(values["avg_priority"] / values["count"], 1)}
        for action, values in sorted(grouped.items(), key=lambda item: item[1]["avg_priority"] / item[1]["count"], reverse=True)
    ]


def write_analysis_files(summary):
    portfolio = summary["portfolio"]
    top = summary["priority_queue"][0]
    weakest_pipeline = summary["integration_health"][0]
    findings = f"""# Executive Findings

## What I Analyzed

I modeled {portfolio['students_modeled']:,} students across {portfolio['districts']} synthetic districts, {portfolio['schools']} schools, {portfolio['segments_scored']} school-grade-subject outcome segments, {portfolio['integration_runs']} integration runs, and {portfolio['quality_issues']} data-quality issues.

## Findings

- The highest-priority segment is {top['school_name']} grade {top['grade']} {top['subject']} with a priority score of {top['priority_score']}.
- The portfolio average proficiency rate is {portfolio['avg_proficiency_rate']:.1%}, chronic absenteeism is {portfolio['chronic_absence_rate']:.1%}, and dashboard readiness is {portfolio['avg_readiness_score']:.1f} out of 100.
- The weakest integration lane is {weakest_pipeline['pipeline_name']} for {weakest_pipeline['district_name']}, with {weakest_pipeline['success_rate']:.1%} refresh success and {weakest_pipeline['avg_record_completeness']:.1%} record completeness.

## Recommendation

Use the priority queue for district review, then run the integration-health checks before publishing any metric that has open quality issues. This keeps the artifact centered on decisions that district leaders can act on and data issues that analytics teams can fix.
"""
    (ANALYSIS / "executive_findings.md").write_text(findings)

    plan = """# Analysis Plan

1. Model district, school, SIS, assessment, attendance, assignment, intervention, and support-request tables.
2. Aggregate weekly outcomes at school, grade, and subject grain.
3. Score each segment on proficiency, growth, attendance, engagement, intervention response, student count, and data readiness.
4. Score integration pipelines on refresh success, latency, and record completeness.
5. Publish a district-facing workbench with executive outcomes, MTSS priority queue, and data-quality controls.
"""
    (ANALYSIS / "analysis_plan.md").write_text(plan)

    methodology = """# Methodology

The artifact uses synthetic but workflow-shaped K-12 data because granular SIS, assessment, attendance, and intervention data is sensitive and not public.

## Synthetic Data Design

- Districts use common K-12 SIS patterns: PowerSchool, Infinite Campus, Skyward, and Aeries.
- Schools are modeled across elementary, middle, and high school levels.
- Outcomes are generated weekly at school, grade, and subject grain, with proficiency, growth, chronic absenteeism, and assignment completion rates.
- Intervention groups are generated by cycle and focus area to resemble MTSS review workflows.
- Integration logs model common dashboard reliability checks: refresh status, latency, and record completeness.
- Data-quality issues model the checks an analyst would troubleshoot before a metric is trusted by district administrators.

## Scoring

The priority score weights low proficiency, low growth, chronic absenteeism, low assignment completion, scale of student impact, intervention response, and unresolved quality issues. The integration-health score weights refresh success, record completeness, and latency. These are deterministic rules designed for interview explainability, not a black-box prediction.
"""
    (ANALYSIS / "methodology.md").write_text(methodology)

    sql = """-- District learning outcomes workbench SQL checks

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
"""
    (ANALYSIS / "sql_checks.sql").write_text(sql)


def write_docs(summary):
    dictionary = """# Data Dictionary

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
"""
    (ROOT / "data_dictionary.md").write_text(dictionary)

    data_readme = """# Data Notes

This folder contains synthetic K-12 operating data for a district learning outcomes analytics workbench. The data is not real student, school, district, or company performance data.

The synthetic structure is modeled on common dashboard inputs for district administrators: SIS rosters, attendance extracts, assessment feeds, assignment events, intervention rosters, stakeholder requests, and SQL-based quality checks.
"""
    (DATA / "README.md").write_text(data_readme)

    status = """# Status

- Status: upgraded through the Portfolio Artifact Upgrade Workflow.
- Artifact: district learning outcomes data operations workbench.
- Surfaces: executive outcomes cockpit, MTSS priority queue, integration and data-quality command center.
- Verification: run `npm run analyze`, then `npm run capture`.
"""
    (ROOT / "STATUS.md").write_text(status)


def main():
    DATA.mkdir(exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    schools = build_schools()
    metric_definitions = build_metric_definitions()
    outcomes = build_outcomes(schools)
    interventions = build_interventions(schools)
    logs = build_integration_logs()
    issues = build_quality_issues(schools)
    requests = build_requests()

    queue, integration_rows, district_rollup, summary = score_artifact(
        districts, schools, outcomes, interventions, logs, issues, requests
    )

    write_csv(DATA / "districts.csv", districts, list(districts[0].keys()))
    write_csv(DATA / "schools.csv", schools, list(schools[0].keys()))
    write_csv(DATA / "metric_definitions.csv", metric_definitions, list(metric_definitions[0].keys()))
    write_csv(DATA / "student_outcomes.csv", outcomes, list(outcomes[0].keys()))
    write_csv(DATA / "interventions.csv", interventions, list(interventions[0].keys()))
    write_csv(DATA / "integration_refresh_log.csv", logs, list(logs[0].keys()))
    write_csv(DATA / "data_quality_issues.csv", issues, list(issues[0].keys()))
    write_csv(DATA / "stakeholder_requests.csv", requests, list(requests[0].keys()))
    write_csv(OUTPUTS / "priority_queue.csv", queue, list(queue[0].keys()))
    write_csv(OUTPUTS / "integration_health.csv", integration_rows, list(integration_rows[0].keys()))
    write_csv(OUTPUTS / "district_rollup.csv", district_rollup, list(district_rollup[0].keys()))
    (OUTPUTS / "summary.json").write_text(json.dumps(summary, indent=2))

    write_analysis_files(summary)
    write_docs(summary)

    print(f"Scored {len(queue)} school-grade-subject segments")
    print(f"Average readiness: {summary['portfolio']['avg_readiness_score']}")
    print(f"Refresh success: {summary['portfolio']['refresh_success_rate']:.1%}")
    print(f"Top segment: {queue[0]['school_name']} grade {queue[0]['grade']} {queue[0]['subject']}")


if __name__ == "__main__":
    main()
