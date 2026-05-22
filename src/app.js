const state = await fetch("analysis/outputs/summary.json").then((response) => response.json());

const pct = (value, digits = 0) => `${(value * 100).toFixed(digits)}%`;
const num = (value) => new Intl.NumberFormat("en-US").format(value);

function renderMetrics() {
  const { portfolio } = state;
  const metrics = [
    ["Students modeled", num(portfolio.students_modeled), `${portfolio.districts} districts`],
    ["Segments scored", num(portfolio.segments_scored), `${num(portfolio.weekly_outcome_rows)} weekly rows`],
    ["Refresh success", pct(portfolio.refresh_success_rate, 1), `${num(portfolio.integration_runs)} runs`],
    ["Open quality issues", num(portfolio.open_quality_issues), `${portfolio.avg_readiness_score} readiness`],
  ];

  document.querySelector("#metric-grid").innerHTML = metrics
    .map(
      ([label, value, detail]) => `
        <article class="metric-card">
          <span>${label}</span>
          <strong>${value}</strong>
          <em>${detail}</em>
        </article>
      `
    )
    .join("");
}

function renderHero() {
  const top = state.priority_queue[0];
  const weakest = state.integration_health[0];
  document.querySelector("#hero-decision").textContent =
    `${top.district_name} needs a grade ${top.grade} ${top.subject} review before the next dashboard release`;
  document.querySelector("#hero-context").textContent =
    `${top.school_name} has ${pct(top.chronic_absence_rate, 1)} chronic absenteeism, ${pct(top.proficiency_rate, 1)} proficiency, and ${top.open_quality_issues} open data-quality issues. ${weakest.pipeline_name} is the weakest integration lane.`;
  document.querySelector("#decision-tags").innerHTML = [
    `${top.sis} SIS`,
    `${pct(top.intervention_response_rate, 1)} intervention response`,
    `${weakest.failed_or_late_runs} failed or late runs`,
  ]
    .map((tag) => `<span>${tag}</span>`)
    .join("");
}

function renderDistricts() {
  document.querySelector("#district-count").textContent = `${state.district_rollup.length} districts`;
  document.querySelector("#district-list").innerHTML = state.district_rollup
    .map(
      (district) => `
        <article class="district-row">
          <div>
            <b>${district.district_name}</b>
            <span>${district.sis} SIS, ${num(district.enrollment)} students</span>
          </div>
          <div class="district-score">
            <strong>${district.avg_readiness_score}</strong>
            <span>${district.critical_segments} critical segments</span>
          </div>
          <div class="progress-track" aria-hidden="true">
            <i style="width:${district.avg_readiness_score}%"></i>
          </div>
        </article>
      `
    )
    .join("");
}

function renderRequestMix() {
  const maxRequests = Math.max(...state.request_mix.map((row) => row.requests));
  document.querySelector("#request-mix").innerHTML = state.request_mix
    .map(
      (row) => `
        <article class="bar-row">
          <div>
            <b>${row.topic}</b>
            <span>${row.requests} requests</span>
          </div>
          <div class="progress-track" aria-hidden="true">
            <i style="width:${(row.requests / maxRequests) * 100}%"></i>
          </div>
        </article>
      `
    )
    .join("");
}

function renderPriorityQueue() {
  document.querySelector("#queue-count").textContent = `${state.priority_queue.length} visible segments`;
  document.querySelector("#priority-table").innerHTML = state.priority_queue
    .slice(0, 12)
    .map(
      (row) => `
        <tr>
          <td>
            <b>${row.school_name}</b>
            <span>${row.district_name}, grade ${row.grade} ${row.subject}</span>
          </td>
          <td>
            <strong>${row.priority_score}</strong>
            <span>${pct(row.proficiency_rate, 1)} proficient</span>
          </td>
          <td>${pct(row.chronic_absence_rate, 1)}</td>
          <td>
            <div class="score-pill ${row.readiness_score < 80 ? "warn" : "ok"}">${row.readiness_score}</div>
          </td>
          <td>${row.recommended_action}</td>
        </tr>
      `
    )
    .join("");
}

function renderIntegrationHealth() {
  document.querySelector("#refresh-rate").textContent = pct(state.portfolio.refresh_success_rate, 1);
  document.querySelector("#integration-list").innerHTML = state.integration_health
    .slice(0, 8)
    .map(
      (row) => `
        <article class="integration-card">
          <div>
            <b>${row.pipeline_name}</b>
            <span>${row.district_name}, ${row.sis}</span>
          </div>
          <strong>${row.health_score}</strong>
          <dl>
            <div><dt>Success</dt><dd>${pct(row.success_rate, 1)}</dd></div>
            <div><dt>Complete</dt><dd>${pct(row.avg_record_completeness, 1)}</dd></div>
            <div><dt>Latency</dt><dd>${row.avg_latency_minutes}m</dd></div>
          </dl>
        </article>
      `
    )
    .join("");
}

function renderQualityMix() {
  document.querySelector("#open-issues").textContent = `${state.portfolio.open_quality_issues} open`;
  const maxOpen = Math.max(...state.quality_issue_mix.map((row) => row.open));
  document.querySelector("#quality-mix").innerHTML = state.quality_issue_mix
    .map(
      (row) => `
        <article class="quality-card">
          <div>
            <b>${row.issue_type}</b>
            <span>${row.records_impacted.toLocaleString()} records impacted</span>
          </div>
          <strong>${row.open}</strong>
          <div class="progress-track" aria-hidden="true">
            <i style="width:${(row.open / maxOpen) * 100}%"></i>
          </div>
        </article>
      `
    )
    .join("");
}

function bindViewButtons() {
  const sections = {
    executive: document.querySelector("#executive"),
    mtss: document.querySelector("#mtss"),
    quality: document.querySelector("#quality"),
  };
  document.querySelectorAll(".view-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".view-button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      sections[button.dataset.view].scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

renderHero();
renderMetrics();
renderDistricts();
renderRequestMix();
renderPriorityQueue();
renderIntegrationHealth();
renderQualityMix();
bindViewButtons();
