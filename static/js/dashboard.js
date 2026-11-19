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
        renderAnalysisResults(res.data);
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
        renderAnalysisResults(res.data);
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

      <div class="row g-2 align-items-center text-muted small">
        <div class="col-auto"><b>Target Column:</b> ${escapeHtml(iss.column || "Full Dataset")}</div>
        <div class="col-auto">|</div>
        <div class="col-auto"><b>Affected Records:</b> ${iss.affected_count} (${iss.affected_pct || 0}%)</div>
        <div class="col-auto">|</div>
        <div class="col-auto"><b>Sample Problem Values:</b> ${sampleBadges || 'N/A'}</div>
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

// ----------------- DATA CLEANING CONSOLE -----------------

function renderCleaningConsole(issues) {
  const tbody = document.getElementById("cleaningOperationsTableBody");
  tbody.innerHTML = "";

  if (issues.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No cleaning operations needed. Dataset is already clean!</td></tr>`;
    return;
  }

  issues.forEach(iss => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" class="cleaning-checkbox" data-id="${iss.id}" checked onchange="updateCleaningSelectionCount()"></td>
      <td><b>${escapeHtml(iss.title)}</b><br/><small class="text-muted">${escapeHtml(iss.column || "Full Dataset")}</small></td>
      <td><span class="badge-custom ${iss.severity === 'high' ? 'badge-high' : 'badge-medium'}">${iss.severity.toUpperCase()}</span></td>
      <td><code>${iss.cleaning_rule || 'inspect'}</code></td>
      <td>${iss.affected_count}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary" onclick="showPreviewModal('${iss.id}')">
          <i class="bi bi-eye"></i> Preview Before/After
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  updateCleaningSelectionCount();
}

function updateCleaningSelectionCount() {
  const checked = document.querySelectorAll(".cleaning-checkbox:checked");
  document.getElementById("cleaningSelectedCount").textContent = `${checked.length} Selected`;
}

function toggleSelectAllCleaning(checked) {
  document.querySelectorAll(".cleaning-checkbox").forEach(cb => cb.checked = checked);
  document.getElementById("selectAllCheckbox").checked = checked;
  updateCleaningSelectionCount();
}

function showPreviewModal(issueId) {
  if (!currentSessionData) return;
  const issue = currentSessionData.issues.find(i => i.id === issueId);
  if (!issue) return;

  document.getElementById("previewModalTitle").textContent = `Preview Fix: ${issue.title}`;
  document.getElementById("previewModalDesc").textContent = `Transformation Rule: ${issue.cleaning_rule}. Below is a sample preview comparing original values to sanitized values.`;

  const tbody = document.getElementById("previewModalTableBody");
  tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3">Generating sample preview...</td></tr>`;

  if (previewModalInstance) previewModalInstance.show();

  fetch(`/api/preview-cleaning/${currentSessionData.session_id}/${issueId}`)
    .then(r => r.json())
    .then(res => {
      tbody.innerHTML = "";
      if (res.success && res.preview.preview_samples.length > 0) {
        res.preview.preview_samples.forEach(s => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><b>#${s.row}</b></td>
            <td>${escapeHtml(s.column)}</td>
            <td><span class="diff-del">${escapeHtml(s.before)}</span></td>
            <td><span class="diff-add">${escapeHtml(s.after)}</span></td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">No sample row changes generated or row dropped.</td></tr>`;
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

  const selectedBoxes = document.querySelectorAll(".cleaning-checkbox:checked");
  const approvedIds = Array.from(selectedBoxes).map(cb => cb.getAttribute("data-id"));

  if (approvedIds.length === 0) {
    showAlert("warning", "Please select at least one cleaning operation to approve.");
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
        showAlert("success", `Sanitization complete! Applied ${res.cleaning_result.actions_applied} cleaning action(s). Quality Score improved from ${res.cleaning_result.initial_score}% to ${res.cleaning_result.new_score}%!`);

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

function downloadArtifact(sessionId, format) {
  generateReports(format === "csv" ? "cleaned_csv" : "cleaned_xlsx");
}

function downloadArtifactFile(filename) {
  const link = document.createElement("a");
  link.href = `/api/download/${filename}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ----------------- UTILITIES -----------------

function showLoading(title, sub) {
  document.getElementById("loadingTitle").textContent = title || "Processing...";
  document.getElementById("loadingSub").textContent = sub || "Please wait...";
  document.getElementById("loadingOverlay").style.display = "flex";
}

function hideLoading() {
  document.getElementById("loadingOverlay").style.display = "none";
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
