let currentSessionData = null;
let qualityChartInstance = null;
let columnBarChartInstance = null;
let previewModalInstance = null;

document.addEventListener("DOMContentLoaded", function () {
  initNavigation();
  initUpload();
  checkHealth();
  refreshRecentSessions();

  const modalEl = document.getElementById("previewModal");
  if (modalEl) {
    previewModalInstance = new bootstrap.Modal(modalEl);
  }
});

// ----------------- NAVIGATION -----------------

function initNavigation() {
  const links = document.querySelectorAll(".sidebar-nav .nav-link");
  links.forEach(link => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const tab = this.getAttribute("data-tab");
      switchTab(tab);
    });
  });

  document.getElementById("btnQuickUpload").addEventListener("click", () => switchTab("upload"));
}

function switchTab(tabName) {
  // Update sidebar active class
  document.querySelectorAll(".sidebar-nav .nav-link").forEach(link => {
    if (link.getAttribute("data-tab") === tabName) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });

  // Hide all sections
  document.querySelectorAll(".content-section").forEach(sec => sec.classList.add("d-none"));

  // Show target section
  const target = document.getElementById(`section-${tabName}`);
  if (target) {
    target.classList.remove("d-none");
  }

  // Update Page Title
  const titles = {
    "dashboard": "Dashboard Overview",
    "upload": "Upload Dataset for Inspection",
    "profile": "Dataset Profile & Type Inference",
    "quality": "Data Quality Scoring Overview",
    "issues": "Detected Quality Issues & Anomalies",
    "ai-insights": "Gemini AI Dataset Insights",
    "cleaning": "Interactive Data Cleaning Console",
    "reports": "Audit Reports & Cleaned Data Export"
  };
  document.getElementById("pageTitle").textContent = titles[tabName] || "Dashboard";
}

// ----------------- HEALTH & SESSIONS -----------------

function checkHealth() {
  fetch("/api/health")
    .then(r => r.json())
    .then(data => {
      const dot = document.getElementById("geminiStatusDot");
      if (data.gemini_connected) {
        dot.textContent = "Online (" + data.gemini_model.replace("models/", "") + ")";
        dot.className = "badge bg-success";
      } else {
        dot.textContent = "Heuristic Mode";
        dot.className = "badge bg-warning text-dark";
      }
    })
    .catch(() => {
      const dot = document.getElementById("geminiStatusDot");
      dot.textContent = "Offline";
      dot.className = "badge bg-danger";
    });
}

function refreshRecentSessions() {
  fetch("/api/sessions")
    .then(r => r.json())
    .then(data => {
      const tbody = document.getElementById("recentSessionsTableBody");
      tbody.innerHTML = "";
      const sessions = data.sessions || [];

      if (sessions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No analysis sessions yet. Upload a dataset or load a demo sample below!</td></tr>`;
        return;
      }

      sessions.forEach(s => {
        const tr = document.createElement("tr");
        const dateStr = new Date(s.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const scoreVal = s.overall_score !== null ? `${s.overall_score}%` : "In Progress";
        tr.innerHTML = `
          <td><b>${escapeHtml(s.filename)}</b></td>
          <td>${dateStr}</td>
          <td>${s.row_count.toLocaleString()}</td>
          <td>${s.column_count}</td>
          <td><span class="badge bg-primary fs-6">${scoreVal}</span></td>
          <td><span class="badge ${s.overall_score >= 80 ? 'bg-success' : 'bg-warning'}">${s.health}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-primary" onclick="loadSessionData('${s.session_id}')">
              <i class="bi bi-eye"></i> View
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    })
    .catch(err => console.error("Could not fetch sessions:", err));
}

function loadSessionData(sessionId) {
  showLoading("Loading Session", "Retrieving historical analysis cache...");
  fetch(`/api/session/${sessionId}`)
    .then(r => r.json())
    .then(res => {
      hideLoading();
      if (res.success) {
        renderAnalysisResults(res.data);
        switchTab("dashboard");
      } else {
        showAlert("danger", res.error || "Failed to load session.");
      }
    })
    .catch(err => {
      hideLoading();
      showAlert("danger", "Failed to retrieve session: " + err);
    });
}

// ----------------- UPLOAD & SAMPLE LOADING -----------------

function initUpload() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const selectedFileName = document.getElementById("selectedFileName");

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", e => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", e => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected();
    }
  });

  fileInput.addEventListener("change", handleFileSelected);

  function handleFileSelected() {
    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];
      selectedFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      selectedFileName.classList.remove("d-none");
      btnAnalyze.disabled = false;
    }
  }

  btnAnalyze.addEventListener("click", uploadAndAnalyze);
}

function uploadAndAnalyze() {
  const fileInput = document.getElementById("fileInput");
  const userContext = document.getElementById("userContext").value.trim();

  if (!fileInput.files || fileInput.files.length === 0) {
    showAlert("warning", "Please select a file to upload.");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_context", userContext);

  showLoading("Analyzing Dataset", "Running automated ingestion, type profiling, issue detection, and Gemini insights...");

  fetch("/api/upload", {
    method: "POST",
    body: formData
  })
    .then(r => r.json())
    .then(res => {
      hideLoading();
      if (res.success) {
        showAlert("success", `Dataset '${file.name}' successfully analyzed!`);
        try {
          renderAnalysisResults(res.data);
        } catch (renderErr) {
          console.error("Error rendering results:", renderErr);
        }
        switchTab("dashboard");
      } else {
        showAlert("danger", res.error || "Analysis failed.");
      }
    })
    .catch(err => {
      hideLoading();
      showAlert("danger", "Error communicating with server: " + err);
    });
}

function loadSampleDataset(sampleName) {
  showLoading("Loading Demo Dataset", `Ingesting '${sampleName}' across profiling & Gemini agent...`);

  fetch("/api/load-sample", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sample_name: sampleName })
  })
    .then(r => r.json())
    .then(res => {
      hideLoading();
      if (res.success) {
        showAlert("success", `Demo dataset '${sampleName}' loaded and analyzed!`);
        try {
          renderAnalysisResults(res.data);
        } catch (renderErr) {
          console.error("Error rendering results:", renderErr);
        }
        switchTab("dashboard");
      } else {
        showAlert("danger", res.error || "Failed to load sample dataset.");
      }
    })
    .catch(err => {
      hideLoading();
      showAlert("danger", "Network error: " + err);
    });
}

// ----------------- RENDER ANALYSIS RESULTS -----------------

function renderAnalysisResults(data) {
  currentSessionData = data;

  // Active dataset badge
  const badge = document.getElementById("activeDatasetBadge");
  badge.classList.remove("d-none");
  document.getElementById("activeDatasetName").textContent = data.filename;

  // Export button on top
  document.getElementById("btnExportTop").classList.remove("d-none");
  document.getElementById("btnExportTop").onclick = () => switchTab("reports");

  const overview = data.overview || {};
  const scores = data.scores || {};
  const issues = data.issues || [];
  const confirmedIssues = issues.filter(i => !i.is_anomaly_only);
  const anomalies = issues.filter(i => i.is_anomaly_only);

  // 1. KPIs
  document.getElementById("kpiScore").textContent = `${scores.overall_score || 0}%`;
  document.getElementById("kpiRowsCols").textContent = `${overview.row_count || 0} × ${overview.column_count || 0}`;
  document.getElementById("kpiIssues").textContent = confirmedIssues.length;
  document.getElementById("kpiAnomalies").textContent = anomalies.length;

  // Sidebar badge
  const sbBadge = document.getElementById("sidebarIssuesBadge");
  sbBadge.textContent = issues.length;
  sbBadge.classList.remove("d-none");

  // 2. Donut Chart & Dimension breakdown
  const dim = scores.dimensions || {};
  document.getElementById("dimCompVal").textContent = `${dim.completeness || 100}%`;
  document.getElementById("dimUniqVal").textContent = `${dim.uniqueness || 100}%`;
  document.getElementById("dimValVal").textContent = `${dim.validity || 100}%`;
  document.getElementById("dimConsVal").textContent = `${dim.consistency || 100}%`;

  document.getElementById("cardCompVal").textContent = `${dim.completeness || 100}%`;
  document.getElementById("cardUniqVal").textContent = `${dim.uniqueness || 100}%`;
  document.getElementById("cardValVal").textContent = `${dim.validity || 100}%`;
  document.getElementById("cardConsVal").textContent = `${dim.consistency || 100}%`;

  document.getElementById("donutScoreVal").textContent = `${scores.overall_score || 0}%`;
  document.getElementById("donutRatingText").textContent = scores.health || "Analyzed";

  renderDonutChart(scores.overall_score || 0, scores.health_color || "#0d6efd");
  renderColumnBarChart(scores.column_scores || {});

  // 3. Render Profile Table
  renderProfileTable(data.columns || {});

  // 4. Render Column Scores Table
  renderColumnScoresTable(scores.column_scores || {});

  // 5. Render Issues & Anomalies
  renderIssuesCards(issues);

  // 6. Render AI Insights
  renderAiInsights(data.ai_understanding, data.ai_plan, data.ai_explanations);

  // 7. Render Cleaning Console
  renderCleaningConsole(issues);

  // Refresh recent sessions list
  refreshRecentSessions();
}

// ----------------- CHARTS -----------------

function renderDonutChart(score, color) {
  const ctx = document.getElementById("qualityDonutChart").getContext("2d");
  if (qualityChartInstance) {
    qualityChartInstance.destroy();
  }

  qualityChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [color, "#e2e8f0"],
        borderWidth: 0,
        circumference: 360,
        cutout: "78%"
      }]
    },
    options: {
      responsive: false,
      plugins: {
        tooltip: { enabled: false }
      }
    }
  });
}

function renderColumnBarChart(columnScores) {
  const ctx = document.getElementById("columnHealthBarChart").getContext("2d");
  if (columnBarChartInstance) {
    columnBarChartInstance.destroy();
  }

  const labels = Object.keys(columnScores).slice(0, 15);
  const values = labels.map(c => columnScores[c].score);
  const colors = values.map(v => v >= 80 ? "#10b981" : (v >= 60 ? "#0284c7" : "#ef4444"));

  columnBarChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Quality Score (%)",
        data: values,
        backgroundColor: colors,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { callback: v => v + "%" },
          grid: { color: "#f1f5f9" }
        },
        x: {
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// ----------------- PROFILE TABLE -----------------

function renderProfileTable(columns) {
  const tbody = document.getElementById("profileTableBody");
  tbody.innerHTML = "";

  Object.entries(columns).forEach(([colName, info]) => {
    const tr = document.createElement("tr");

    let statsSummary = "--";
    if (info.statistics && Object.keys(info.statistics).length > 0) {
      const s = info.statistics;
      statsSummary = `Min: ${s.min} | Max: ${s.max} | Mean: ${s.mean}`;
    } else if (info.top_categories && info.top_categories.length > 0) {
      statsSummary = `Top: ${info.top_categories.slice(0, 3).map(c => c.value).join(", ")}`;
    }

    const sampleBadges = (info.sample_values || []).slice(0, 3).map(v => `<span class="badge bg-light text-dark border me-1">${escapeHtml(v)}</span>`).join("");

    tr.innerHTML = `
      <td><b>${escapeHtml(colName)}</b></td>
      <td><span class="badge bg-secondary">${info.physical_type}</span></td>
      <td><span class="badge bg-info text-dark">${info.semantic_type.replace('_', ' ')}</span></td>
      <td>${info.total_missing} (${info.missing_pct}%)</td>
      <td>${info.distinct_count} (${info.uniqueness_pct}%)</td>
      <td><small class="text-muted">${statsSummary}</small></td>
      <td>${sampleBadges || '--'}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------- COLUMN SCORES TABLE -----------------

function renderColumnScoresTable(columnScores) {
  const tbody = document.getElementById("columnScoresTableBody");
  tbody.innerHTML = "";

  Object.entries(columnScores).forEach(([colName, scoreData]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><b>${escapeHtml(colName)}</b></td>
      <td><span class="badge bg-primary fs-6">${scoreData.score}%</span></td>
      <td>${scoreData.completeness}%</td>
      <td>${scoreData.uniqueness}%</td>
      <td>${scoreData.validity}%</td>
      <td>${scoreData.consistency}%</td>
      <td><span class="badge bg-${scoreData.badge_class}">${scoreData.health}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------- ISSUES & ANOMALIES -----------------

function renderIssuesCards(issues) {
  const container = document.getElementById("issuesContainer");
  container.innerHTML = "";

  if (issues.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5 text-muted">
        <i class="bi bi-patch-check-fill fs-1 text-success mb-2"></i>
        <h5>Pristine Dataset Health!</h5>
        <p>No confirmed quality errors or anomalies detected across any columns.</p>
      </div>
    `;
    document.getElementById("issuesCountStatus").textContent = "Showing 0 Issues";
    return;
  }

  document.getElementById("issuesCountStatus").textContent = `Showing ${issues.length} Issue(s)`;

  issues.forEach(iss => {
    const card = document.createElement("div");
    card.className = "card-custom p-3 mb-3 issue-card";
    card.setAttribute("data-category", iss.category);
    card.setAttribute("data-severity", iss.severity);

    const sevBadge = iss.severity === "high" ? "badge-high" : (iss.severity === "medium" ? "badge-medium" : "badge-low");
    const isAnomaly = iss.is_anomaly_only ? `<span class="badge bg-info text-dark me-2">Statistical Anomaly</span>` : `<span class="badge bg-danger me-2">Confirmed Quality Defect</span>`;

    const sampleBadges = (iss.problematic_samples || []).slice(0, 4).map(s => `<span class="badge bg-light text-dark border me-1">${escapeHtml(String(s))}</span>`).join("");

    const affectedRows = iss.affected_rows || [];
    let rowBadges = '<span class="text-muted">None</span>';
    if (affectedRows.length > 0) {
      const displayRows = affectedRows.slice(0, 12).map(r => `<span class="badge bg-light text-danger border fw-bold me-1">Row #${r}</span>`).join("");
      const moreCount = affectedRows.length > 12 ? `<span class="badge bg-secondary">+${affectedRows.length - 12} more</span>` : "";
      rowBadges = displayRows + moreCount;
    }

    card.innerHTML = `
      <div class="d-flex justify-content-between align-items-start mb-2">
        <div>
          <span class="badge-custom ${sevBadge} me-2">${iss.severity.toUpperCase()}</span>
          ${isAnomaly}
          <span class="badge bg-secondary">${iss.category.toUpperCase()}</span>
          <h5 class="fw-bold text-primary mt-2 mb-1">${escapeHtml(iss.title)}</h5>
        </div>
        <button class="btn btn-sm btn-outline-primary" onclick="showPreviewModal('${iss.id}')">
          <i class="bi bi-eye me-1"></i> Preview Fix
        </button>
      </div>

      <p class="text-muted mb-2">${escapeHtml(iss.description)}</p>

      <div class="row g-2 align-items-center text-muted small mb-2">
        <div class="col-auto"><b>Target Column:</b> ${escapeHtml(iss.column || "Full Dataset")}</div>
        <div class="col-auto">|</div>
        <div class="col-auto"><b>Affected Records:</b> ${iss.affected_count} (${iss.affected_pct || 0}%)</div>
        <div class="col-auto">|</div>
        <div class="col-auto"><b>Sample Problem Values:</b> ${sampleBadges || 'N/A'}</div>
      </div>

      <div class="pt-2 border-top small d-flex align-items-center flex-wrap gap-1">
        <b class="text-dark me-1"><i class="bi bi-geo-alt-fill text-danger me-1"></i>Affected Row Numbers:</b>
        ${rowBadges}
      </div>
    `;
    container.appendChild(card);
  });
}

function filterIssuesList() {
  const cat = document.getElementById("issueCategoryFilter").value;
  const sev = document.getElementById("issueSeverityFilter").value;
  const cards = document.querySelectorAll(".issue-card");
  let visibleCount = 0;

  cards.forEach(c => {
    const cardCat = c.getAttribute("data-category");
    const cardSev = c.getAttribute("data-severity");
    const catMatch = (cat === "all" || cardCat === cat);
    const sevMatch = (sev === "all" || cardSev === sev);

    if (catMatch && sevMatch) {
      c.classList.remove("d-none");
      visibleCount++;
    } else {
      c.classList.add("d-none");
    }
  });

  document.getElementById("issuesCountStatus").textContent = `Showing ${visibleCount} Issue(s)`;
}

// ----------------- AI INSIGHTS -----------------

function renderAiInsights(understanding, plan, explanations) {
  if (understanding) {
    document.getElementById("aiDomainName").textContent = understanding.probable_domain || "General Data";
    document.getElementById("aiDomainConfidence").textContent = `Confidence: ${(understanding.confidence_level * 100).toFixed(0)}%`;
    document.getElementById("aiDomainDesc").textContent = understanding.domain_description || "";

    const rolesList = document.getElementById("aiColumnRolesList");
    rolesList.innerHTML = "";
    (understanding.columns_understanding || []).forEach(col => {
      const item = document.createElement("div");
      item.className = "mb-2 pb-2 border-bottom";
      item.innerHTML = `
        <div class="d-flex justify-content-between">
          <b>${escapeHtml(col.column_name)}</b>
          <span class="badge bg-light text-primary border">${col.semantic_role}</span>
        </div>
        <div>${escapeHtml(col.inferred_meaning)}</div>
      `;
      rolesList.appendChild(item);
    });
  }

  if (plan) {
    document.getElementById("aiPlanSummary").textContent = plan.domain_tailored_summary || "";
    const planList = document.getElementById("aiPlanChecksList");
    planList.innerHTML = "";
    (plan.recommended_checks || []).forEach(chk => {
      const p = document.createElement("div");
      p.className = "list-group-item list-group-item-action py-2";
      p.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
          <h6 class="mb-1 text-primary fw-bold">${chk.check_name} (${chk.category})</h6>
          <small class="badge bg-${chk.priority === 'high' ? 'danger' : 'info'}">${chk.priority.toUpperCase()}</small>
        </div>
        <p class="mb-1 small text-muted">${escapeHtml(chk.rationale)}</p>
      `;
      planList.appendChild(p);
    });
  }

  if (explanations) {
    document.getElementById("aiExecutiveSummary").textContent = explanations.overall_summary || "";
    const actionList = document.getElementById("aiActionItemsList");
    actionList.innerHTML = "";
    (explanations.immediate_action_items || []).forEach(item => {
      const li = document.createElement("li");
      li.className = "mb-1";
      li.textContent = item;
      actionList.appendChild(li);
    });
  }
}

// ----------------- DATA CLEANING CONSOLE (HUMAN APPROVAL INTERVENTION) -----------------

let currentApprovedIssueIds = new Set();
let activePreviewIssueId = null;

function renderCleaningConsole(issues) {
  const tbody = document.getElementById("cleaningOperationsTableBody");
  tbody.innerHTML = "";

  // Require explicit human approval: do not pre-approve by default
  currentApprovedIssueIds.clear();

  if (!issues || issues.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No cleaning operations needed. Dataset is already clean!</td></tr>`;
    updateCleaningApprovalStats(0, 0);
    return;
  }

  issues.forEach(iss => {
    const affectedRows = iss.affected_rows || [];
    const rowsSnippet = affectedRows.length > 0
      ? `<br/><span class="text-danger fw-semibold" style="font-size:0.75rem;"><i class="bi bi-geo-alt me-1"></i>Rows: ${affectedRows.slice(0, 5).map(r => '#' + r).join(', ')}${affectedRows.length > 5 ? ' (+' + (affectedRows.length - 5) + ')' : ''}</span>`
      : '';

    const suggestedDesc = iss.suggested_value_desc || `Apply ${iss.cleaning_rule || 'rule'}`;

    const tr = document.createElement("tr");
    tr.id = `cleaning-row-${iss.id}`;
    tr.innerHTML = `
      <td>
        <input type="checkbox" class="cleaning-checkbox form-check-input" data-id="${iss.id}" onchange="toggleIssueCheckbox('${iss.id}', this.checked)" title="Approve / Reject">
      </td>
      <td>
        <b>${escapeHtml(iss.title)}</b>${rowsSnippet}
        <br/><small class="text-muted">Target: <code>${escapeHtml(iss.column || "Full Dataset")}</code></small>
      </td>
      <td>
        <div class="fw-semibold text-primary" style="font-size: 0.88rem;">
          <i class="bi bi-lightbulb-fill text-warning me-1"></i>${escapeHtml(suggestedDesc)}
        </div>
        <small class="text-muted">Operation: <code>${escapeHtml(iss.cleaning_rule || 'inspect')}</code></small>
      </td>
      <td>
        <div class="d-flex flex-column gap-1">
          <span id="status-badge-${iss.id}" class="badge bg-warning text-dark py-1">
            <i class="bi bi-clock me-1"></i>Pending Review
          </span>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-success btn-sm py-0 px-2" style="font-size: 0.72rem;" onclick="setIssueApproval('${iss.id}', true)">Approve</button>
            <button type="button" class="btn btn-outline-secondary btn-sm py-0 px-2" style="font-size: 0.72rem;" onclick="setIssueApproval('${iss.id}', false)">Reject</button>
          </div>
        </div>
      </td>
      <td><b>${iss.affected_count}</b></td>
      <td>
        <button class="btn btn-sm btn-outline-primary w-100" onclick="showPreviewModal('${iss.id}')">
          <i class="bi bi-eye me-1"></i> Preview & Approve
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  updateCleaningApprovalStats(0, issues.length);
}

function setIssueApproval(issueId, approved) {
  if (approved) {
    currentApprovedIssueIds.add(issueId);
  } else {
    currentApprovedIssueIds.delete(issueId);
  }

  // Update row checkbox
  const cb = document.querySelector(`.cleaning-checkbox[data-id="${issueId}"]`);
  if (cb) cb.checked = approved;

  // Update status badge
  const badge = document.getElementById(`status-badge-${issueId}`);
  if (badge) {
    if (approved) {
      badge.className = "badge bg-success py-1";
      badge.innerHTML = `<i class="bi bi-check-circle me-1"></i>Approved`;
    } else {
      badge.className = "badge bg-secondary py-1";
      badge.innerHTML = `<i class="bi bi-x-circle me-1"></i>Rejected`;
    }
  }

  // Update row background
  const row = document.getElementById(`cleaning-row-${issueId}`);
  if (row) {
    if (approved) {
      row.classList.add("table-success");
    } else {
      row.classList.remove("table-success");
    }
  }

  // If this issue is currently open in the preview modal, update modal badge too
  if (activePreviewIssueId === issueId) {
    updateModalApprovalBadge(approved);
  }

  const total = (currentSessionData && currentSessionData.issues) ? currentSessionData.issues.length : 0;
  updateCleaningApprovalStats(currentApprovedIssueIds.size, total);
}

function toggleIssueCheckbox(issueId, checked) {
  setIssueApproval(issueId, checked);
}

function approveAllCleaning(approve) {
  if (!currentSessionData || !currentSessionData.issues) return;

  currentSessionData.issues.forEach(iss => {
    setIssueApproval(iss.id, approve);
  });

  const selectAll = document.getElementById("selectAllCheckbox");
  if (selectAll) selectAll.checked = approve;
}

function toggleSelectAllCleaning(checked) {
  approveAllCleaning(checked);
}

function updateCleaningApprovalStats(approvedCount, total) {
  const summaryText = document.getElementById("humanApprovalSummaryText");
  if (summaryText) {
    if (approvedCount === 0) {
      summaryText.textContent = `0 of ${total} suggested cleaning operations approved. Human approval is required: review suggested values and approve operations before cleaning.`;
    } else {
      summaryText.innerHTML = `<b>${approvedCount} of ${total} operations approved by user.</b> Ready to apply approved transformations to a sanitized dataset.`;
    }
  }

  const counterBadge = document.getElementById("approvalCounterBadge");
  if (counterBadge) {
    counterBadge.textContent = `${approvedCount} Approved`;
    counterBadge.className = approvedCount > 0 ? "badge bg-success fs-6 px-3 py-2" : "badge bg-warning text-dark fs-6 px-3 py-2";
  }

  const selCount = document.getElementById("cleaningSelectedCount");
  if (selCount) {
    selCount.textContent = `${approvedCount} Approved`;
    selCount.className = approvedCount > 0 ? "badge bg-success" : "badge bg-secondary";
  }

  const btnCount = document.getElementById("btnApplyApprovedCount");
  if (btnCount) btnCount.textContent = approvedCount;

  const selectAll = document.getElementById("selectAllCheckbox");
  if (selectAll) {
    selectAll.checked = (approvedCount === total && total > 0);
  }
}

function updateModalApprovalBadge(isApproved) {
  const badge = document.getElementById("modalApprovalBadge");
  if (!badge) return;
  if (isApproved) {
    badge.className = "badge bg-success px-3 py-2";
    badge.innerHTML = `<i class="bi bi-check-circle me-1"></i>Status: Approved by User`;
  } else {
    badge.className = "badge bg-warning text-dark px-3 py-2";
    badge.innerHTML = `<i class="bi bi-clock me-1"></i>Status: Pending Human Review`;
  }
}

function modalApproveCurrentIssue() {
  if (!activePreviewIssueId) return;
  setIssueApproval(activePreviewIssueId, true);
  showAlert("success", `Approved suggested fix for this operation.`);
}

function modalRejectCurrentIssue() {
  if (!activePreviewIssueId) return;
  setIssueApproval(activePreviewIssueId, false);
  showAlert("secondary", `Rejected fix for this operation.`);
}

function showPreviewModal(issueId) {
  if (!currentSessionData) return;
  const issue = currentSessionData.issues.find(i => i.id === issueId);
  if (!issue) return;

  activePreviewIssueId = issueId;
  const isApproved = currentApprovedIssueIds.has(issueId);

  // Set suggested value in callout box
  const suggestedVal = issue.suggested_value_desc || `Apply ${issue.cleaning_rule || 'rule'}`;
  const modalSugText = document.getElementById("modalSuggestedValueText");
  if (modalSugText) modalSugText.textContent = suggestedVal;

  updateModalApprovalBadge(isApproved);

  const affectedRows = issue.affected_rows || [];
  const affectedList = affectedRows.slice(0, 10).map(r => '#' + r).join(', ') + (affectedRows.length > 10 ? ` (+${affectedRows.length - 10} more)` : '');
  let rowPillsHtml = '<span class="text-muted small">None</span>';
  if (affectedRows.length > 0) {
    const maxPills = 15;
    const pills = affectedRows.slice(0, maxPills).map(r => 
      `<span class="badge bg-danger text-white me-1 mb-1" style="font-size: 0.78rem; font-weight: 500;">Row #${r}</span>`
    ).join('');
    const morePill = affectedRows.length > maxPills ? 
      `<span class="badge bg-secondary text-white mb-1" style="font-size: 0.78rem;">+${affectedRows.length - maxPills} more</span>` : '';
    rowPillsHtml = pills + morePill;
  }

  document.getElementById("previewModalTitle").textContent = `Preview & Approve Fix: ${issue.title}`;
  document.getElementById("previewModalDesc").innerHTML = `
    <div class="mb-2">
      <b>Transformation Rule:</b> <code>${escapeHtml(issue.cleaning_rule)}</code> 
      <span class="mx-2 text-muted">|</span> 
      <b>Target Column:</b> <code>${escapeHtml(issue.column || "Full Dataset")}</code>
    </div>
    <div class="p-2 rounded bg-light border mb-2">
      <div class="fw-semibold text-dark small mb-1">
        <i class="bi bi-geo-alt-fill text-danger me-1"></i>Identified Defect Row Numbers (${affectedRows.length} total):
      </div>
      <div class="d-flex flex-wrap gap-1 align-items-center" style="max-height: 90px; overflow-y: auto; word-break: break-word;">
        ${rowPillsHtml}
      </div>
    </div>
  `;

  const tbody = document.getElementById("previewModalTableBody");
  tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3">Generating sample preview...</td></tr>`;

  if (previewModalInstance) previewModalInstance.show();

  fetch(`/api/preview-cleaning/${currentSessionData.session_id}/${issueId}`)
    .then(r => r.json())
    .then(res => {
      tbody.innerHTML = "";
      if (res.success && res.preview.preview_samples.length > 0) {
        if (res.preview.suggested_value && modalSugText) {
          modalSugText.textContent = res.preview.suggested_value;
        }
        res.preview.preview_samples.forEach(s => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><span class="badge bg-primary fs-6">Row #${s.row}</span></td>
            <td><code>${escapeHtml(s.column)}</code></td>
            <td><span class="diff-del">${escapeHtml(s.before)}</span></td>
            <td><span class="diff-add">${escapeHtml(s.after)}</span></td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">No sample row changes generated or row dropped. Identified affected rows: <b>${affectedList}</b></td></tr>`;
      }
    })
    .catch(err => {
      tbody.innerHTML = `<tr><td colspan="4" class="text-danger py-3">Error fetching preview: ${err}</td></tr>`;
    });
}

function applyApprovedCleaning() {
  if (!currentSessionData) {
    showAlert("warning", "No active dataset loaded.");
    return;
  }

  const approvedIds = Array.from(currentApprovedIssueIds);

  if (approvedIds.length === 0) {
    showAlert("warning", "<b>Human Approval Required:</b> No operations have been approved. Please review the suggested values and approve at least one fix before applying cleaning.");
    return;
  }

  if (!confirm(`Confirm Human Approval: You have approved ${approvedIds.length} cleaning transformation(s). Do you want to apply them now to produce a sanitized dataset?`)) {
    return;
  }

  showLoading("Applying Approved Transformations", "Executing approved operations on a fresh dataset copy and re-scoring quality...");

  fetch(`/api/apply-cleaning/${currentSessionData.session_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved_issue_ids: approvedIds })
  })
    .then(r => r.json())
    .then(res => {
      hideLoading();
      if (res.success) {
        showAlert("success", `Sanitization complete! Applied ${res.cleaning_result.actions_applied} human-approved cleaning action(s). Quality Score improved from ${res.cleaning_result.initial_score}% to ${res.cleaning_result.new_score}%!`);

        // Show cleaning audit card
        const auditCard = document.getElementById("cleaningAuditCard");
        auditCard.classList.remove("d-none");
        document.getElementById("cleaningScoreDelta").textContent = `Score: ${res.cleaning_result.initial_score}% ➔ ${res.cleaning_result.new_score}%`;

        const auditList = document.getElementById("cleaningAuditList");
        auditList.innerHTML = "";
        (res.cleaning_result.audit_log || []).forEach(log => {
          const li = document.createElement("li");
          li.className = "list-group-item d-flex justify-content-between align-items-center py-2";
          li.innerHTML = `
            <div><b>${escapeHtml(log.operation)}</b> on column <code>${escapeHtml(log.column)}</code></div>
            <span class="badge bg-success rounded-pill">${log.modified_rows} records</span>
          `;
          auditList.appendChild(li);
        });

        // Update dashboard with new scores
        renderAnalysisResults(res.updated_data);
      } else {
        showAlert("danger", res.error || "Failed to apply cleanings.");
      }
    })
    .catch(err => {
      hideLoading();
      showAlert("danger", "Failed to communicate with cleaning engine: " + err);
    });
}

// ----------------- REPORTS & ARTIFACTS -----------------

function generateReports(preferredType) {
  if (!currentSessionData) {
    showAlert("warning", "Please analyze a dataset first before generating reports.");
    return;
  }

  showLoading("Generating Executive Audit Reports", "Building PDF document with ReportLab and multi-sheet Excel with openpyxl...");

  fetch(`/api/generate-reports/${currentSessionData.session_id}`, {
    method: "POST"
  })
    .then(r => r.json())
    .then(res => {
      hideLoading();
      if (res.success) {
        showAlert("success", "Reports generated successfully! Your download will begin shortly.");
        const artifacts = res.artifacts;

        if (preferredType === "pdf") {
          downloadArtifactFile(artifacts.pdf_report);
        } else if (preferredType === "excel") {
          downloadArtifactFile(artifacts.excel_summary);
        } else if (preferredType === "cleaned_csv") {
          downloadArtifactFile(artifacts.cleaned_csv);
        } else if (preferredType === "cleaned_xlsx") {
          downloadArtifactFile(artifacts.cleaned_xlsx);
        }
      } else {
        showAlert("danger", res.error || "Report generation failed.");
      }
    })
    .catch(err => {
      hideLoading();
      showAlert("danger", "Failed to generate report: " + err);
    });
}

function downloadCleanedData(format) {
  if (!currentSessionData) {
    showAlert("warning", "No dataset analyzed or cleaned yet. Please analyze a dataset first.");
    return;
  }
  generateReports(format === "xlsx" ? "cleaned_xlsx" : "cleaned_csv");
}

function downloadArtifact(arg1, arg2) {
  const format = (arg2 || arg1 || "csv");
  downloadCleanedData(format);
}

function downloadArtifactFile(filename) {
  if (!filename) return;
  const url = `/api/download/${encodeURIComponent(filename)}`;
  
  // Create clickable link
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
  }, 300);

  showAlert("success", `Download ready: <b>${escapeHtml(filename)}</b>! If it didn't start automatically, <a href="${url}" download="${filename}" class="alert-link fw-bold text-decoration-underline">click here to download directly</a>.`);
}

// Expose globally for inline onclick handlers
window.downloadCleanedData = downloadCleanedData;
window.downloadArtifact = downloadArtifact;
window.setIssueApproval = setIssueApproval;
window.toggleIssueCheckbox = toggleIssueCheckbox;
window.approveAllCleaning = approveAllCleaning;
window.toggleSelectAllCleaning = toggleSelectAllCleaning;
window.modalApproveCurrentIssue = modalApproveCurrentIssue;
window.modalRejectCurrentIssue = modalRejectCurrentIssue;
window.showPreviewModal = showPreviewModal;
window.applyApprovedCleaning = applyApprovedCleaning;

// ----------------- UTILITIES -----------------

function showLoading(title, sub) {
  // Never cover the webpage with the full-screen overlay; keep the UI normal and responsive
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) overlay.style.display = "none";

  // Show small loading symbol in the upload dataset section (left side)
  const inlineLoader = document.getElementById("uploadInlineLoader");
  const inlineText = document.getElementById("uploadInlineText");
  if (inlineLoader) {
    inlineLoader.classList.remove("d-none");
    inlineLoader.classList.add("d-flex");
    if (inlineText) inlineText.textContent = title || "Analyzing dataset...";
  }

  const inlineBanner = document.getElementById("uploadInlineBanner");
  const inlineTitle = document.getElementById("uploadInlineBannerTitle");
  const inlineSub = document.getElementById("uploadInlineBannerSub");
  if (inlineBanner) {
    inlineBanner.classList.remove("d-none");
    inlineBanner.classList.add("d-flex");
    if (inlineTitle) inlineTitle.textContent = title || "Analyzing Dataset";
    if (inlineSub) inlineSub.textContent = sub || "Running profiling, issue detection, and Gemini insights...";
  }

  // Small spinner on the left sidebar navigation
  const sidebarSpinner = document.getElementById("sidebarUploadSpinner");
  if (sidebarSpinner) {
    sidebarSpinner.classList.remove("d-none");
  }

  // Small spinner on the Analyze button
  const btnSpinner = document.getElementById("btnAnalyzeSpinner");
  const btnText = document.getElementById("btnAnalyzeText");
  const btnAnalyze = document.getElementById("btnAnalyze");
  if (btnSpinner && btnText && btnAnalyze) {
    btnSpinner.classList.remove("d-none");
    btnText.textContent = " Analyzing...";
    btnAnalyze.disabled = true;
  }
}

function hideLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) overlay.style.display = "none";

  // Hide small loading symbols in the upload dataset section
  const inlineLoader = document.getElementById("uploadInlineLoader");
  if (inlineLoader) {
    inlineLoader.classList.remove("d-flex");
    inlineLoader.classList.add("d-none");
  }

  const inlineBanner = document.getElementById("uploadInlineBanner");
  if (inlineBanner) {
    inlineBanner.classList.remove("d-flex");
    inlineBanner.classList.add("d-none");
  }

  const sidebarSpinner = document.getElementById("sidebarUploadSpinner");
  if (sidebarSpinner) {
    sidebarSpinner.classList.add("d-none");
  }

  const btnSpinner = document.getElementById("btnAnalyzeSpinner");
  const btnText = document.getElementById("btnAnalyzeText");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const fileInput = document.getElementById("fileInput");
  if (btnSpinner && btnText && btnAnalyze) {
    btnSpinner.classList.add("d-none");
    btnText.innerHTML = '<i class="bi bi-play-circle me-2"></i>Start Autonomous Analysis';
    const hasFile = Boolean(fileInput && fileInput.files && fileInput.files.length > 0);
    btnAnalyze.disabled = !hasFile;
  }
}

function showAlert(type, message) {
  const alertContainer = document.getElementById("alertContainer");
  const alert = document.createElement("div");
  alert.className = `alert alert-${type} alert-dismissible fade show shadow-sm`;
  alert.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  alertContainer.appendChild(alert);
  setTimeout(() => {
    alert.classList.remove("show");
    setTimeout(() => alert.remove(), 200);
  }, 5000);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
