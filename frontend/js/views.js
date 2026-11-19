const Views = {

  loginPage(errorMsg = "") {
    return `
      <div class="login-wrap">
        <div class="card login-card">
          <h2>Federated Health Analytics</h2>
          <p class="demo-hint">
            Demo accounts (run <code>python seed.py</code> in backend/ first):<br/>
            Admin: admin@fedhealth.demo / AdminPass123!<br/>
            Clinician: clinician1@fedhealth.demo / ClinicianPass123!
          </p>
          ${errorMsg ? `<div class="error">${errorMsg}</div>` : ""}
          <form id="login-form">
            <label>Email</label>
            <input type="email" id="login-email" required />
            <label>Password</label>
            <input type="password" id="login-password" required />
            <button type="submit" class="primary" style="width:100%">Sign in</button>
          </form>
          <p style="text-align:center;margin-top:14px;">
            <button class="link-btn" id="show-register">Need an account? Register</button>
          </p>
        </div>
      </div>`;
  },

  registerPage(institutions = [], errorMsg = "") {
    const options = institutions.map(i => `<option value="${i.id}">${i.name}</option>`).join("");
    return `
      <div class="login-wrap">
        <div class="card login-card">
          <h2>Create Account</h2>
          ${errorMsg ? `<div class="error">${errorMsg}</div>` : ""}
          <form id="register-form">
            <label>Full name</label>
            <input type="text" id="reg-name" />
            <label>Email</label>
            <input type="email" id="reg-email" required />
            <label>Password (min 8 characters)</label>
            <input type="password" id="reg-password" required minlength="8" />
            <label>Institution</label>
            <select id="reg-institution">
              <option value="">— none (admin only) —</option>
              ${options}
            </select>
            <label>Role</label>
            <select id="reg-role">
              <option value="clinician">Clinician</option>
              <option value="admin">Admin</option>
            </select>
            <button type="submit" class="primary" style="width:100%">Register</button>
          </form>
          <p style="text-align:center;margin-top:14px;">
            <button class="link-btn" id="show-login">Back to sign in</button>
          </p>
        </div>
      </div>`;
  },

  shell(user, activeTab, innerHtml) {
    const tabs = [
      ["dashboard", "Dashboard"],
      ["patients", "Patients"],
      ["predict", "Predict Risk"],
      ["federated", "Federated Training"],
    ];
    if (user.role === "admin") tabs.push(["institutions", "Institutions"]);

    const navButtons = tabs.map(([key, label]) =>
      `<button data-tab="${key}" class="${key === activeTab ? "active" : ""}">${label}</button>`
    ).join("");

    return `
      <div class="topbar">
        <h1>🏥 Federated Healthcare Analytics</h1>
        <div class="user-info">
          <span>${user.full_name || user.email} · ${user.role}</span>
          <button id="logout-btn">Log out</button>
        </div>
      </div>
      <div class="nav">${navButtons}</div>
      <div class="container">${innerHtml}</div>
    `;
  },

  dashboard(status, patientCount, predictionCount) {
    const last = status.last_round;
    return `
      <div class="grid-3">
        <div class="stat-box"><div class="value">${status.current_model_version}</div><div class="label">Global model version</div></div>
        <div class="stat-box"><div class="value">${status.total_rounds_completed}</div><div class="label">Training rounds completed</div></div>
        <div class="stat-box"><div class="value">${patientCount}</div><div class="label">Patients (your institution)</div></div>
      </div>
      <div class="card">
        <h2>Federation status</h2>
        <p class="muted">Institutions currently eligible to participate in the next training round:</p>
        <p>${status.eligible_institutions.length ? status.eligible_institutions.join(", ") : "None yet — seed more labeled patients."}</p>
        ${last ? `
          <h3>Last completed round</h3>
          <table>
            <tr><th>Round #</th><th>Clients</th><th>Samples</th><th>Val. accuracy</th><th>Val. loss</th></tr>
            <tr>
              <td>${last.round_number}</td>
              <td>${last.num_clients}</td>
              <td>${last.total_samples}</td>
              <td>${(last.global_val_accuracy * 100).toFixed(1)}%</td>
              <td>${last.global_val_loss.toFixed(4)}</td>
            </tr>
          </table>
        ` : `<p class="muted">No federated training rounds have run yet.</p>`}
      </div>
      <div class="card">
        <h2>Your recent predictions</h2>
        <p class="muted">${predictionCount} prediction(s) run at your institution.</p>
      </div>
    `;
  },

  patients(list) {
    const rows = list.map(p => `
      <tr>
        <td>#${p.id}</td>
        <td>${p.age}</td>
        <td>${p.bmi}</td>
        <td>${p.systolic_bp}</td>
        <td>${p.glucose}</td>
        <td>${p.cholesterol}</td>
        <td>${p.smoker ? "Yes" : "No"}</td>
        <td>${p.diagnosis_label === null ? '<span class="muted">unlabeled</span>' : (p.diagnosis_label ? '<span class="badge high">High risk</span>' : '<span class="badge low">Low risk</span>')}</td>
      </tr>
    `).join("");

    return `
      <div class="card">
        <h2>Add patient</h2>
        <p class="muted">Records are scoped to your institution only — other institutions never see this data. Setting a known diagnosis label lets this record be used in the next federated training round.</p>
        <form id="patient-form">
          <div class="grid-3">
            <div><label>Age</label><input type="number" step="0.1" id="p-age" required /></div>
            <div><label>BMI</label><input type="number" step="0.1" id="p-bmi" required /></div>
            <div><label>Systolic BP</label><input type="number" step="0.1" id="p-bp" required /></div>
          </div>
          <div class="grid-3">
            <div><label>Glucose</label><input type="number" step="0.1" id="p-glucose" required /></div>
            <div><label>Cholesterol</label><input type="number" step="0.1" id="p-cholesterol" required /></div>
            <div>
              <label>Known diagnosis</label>
              <select id="p-label">
                <option value="">Unknown</option>
                <option value="0">Low risk (0)</option>
                <option value="1">High risk (1)</option>
              </select>
            </div>
          </div>
          <div class="checkbox-row"><input type="checkbox" id="p-smoker" /><label style="margin:0">Smoker</label></div>
          <button type="submit" class="primary">Add patient</button>
        </form>
      </div>
      <div class="card">
        <h2>Patients at your institution (${list.length})</h2>
        <table>
          <tr><th>ID</th><th>Age</th><th>BMI</th><th>Sys. BP</th><th>Glucose</th><th>Cholesterol</th><th>Smoker</th><th>Label</th></tr>
          ${rows || `<tr><td colspan="8" class="muted">No patients yet.</td></tr>`}
        </table>
      </div>
    `;
  },

  predict(patients, history) {
    const options = patients.map(p => `<option value="${p.id}">#${p.id} (age ${p.age})</option>`).join("");
    const historyRows = history.map(h => `
      <tr>
        <td>${new Date(h.created_at).toLocaleString()}</td>
        <td>${h.patient_id ? "#" + h.patient_id : "manual entry"}</td>
        <td>v${h.model_version}</td>
        <td>${(h.risk_score * 100).toFixed(1)}%</td>
        <td>${h.predicted_label ? '<span class="badge high">High risk</span>' : '<span class="badge low">Low risk</span>'}</td>
      </tr>
    `).join("");

    return `
      <div class="card">
        <h2>Run a prediction</h2>
        <p class="muted">Uses the current global federated model (trained across all participating institutions without any raw data ever leaving them).</p>
        <form id="predict-form">
          <label>Link to existing patient (optional)</label>
          <select id="pred-patient"><option value="">— manual entry —</option>${options}</select>
          <div class="grid-3">
            <div><label>Age</label><input type="number" step="0.1" id="pred-age" required /></div>
            <div><label>BMI</label><input type="number" step="0.1" id="pred-bmi" required /></div>
            <div><label>Systolic BP</label><input type="number" step="0.1" id="pred-bp" required /></div>
          </div>
          <div class="grid-3">
            <div><label>Glucose</label><input type="number" step="0.1" id="pred-glucose" required /></div>
            <div><label>Cholesterol</label><input type="number" step="0.1" id="pred-cholesterol" required /></div>
            <div style="padding-top:22px"><div class="checkbox-row"><input type="checkbox" id="pred-smoker" /><label style="margin:0">Smoker</label></div></div>
          </div>
          <button type="submit" class="primary">Predict risk</button>
        </form>
        <div id="predict-result"></div>
      </div>
      <div class="card">
        <h2>Prediction history</h2>
        <table>
          <tr><th>When</th><th>Patient</th><th>Model</th><th>Risk score</th><th>Result</th></tr>
          ${historyRows || `<tr><td colspan="5" class="muted">No predictions yet.</td></tr>`}
        </table>
      </div>
    `;
  },

  predictResult(result) {
    const cls = result.predicted_label ? "high" : "low";
    const label = result.predicted_label ? "High risk" : "Low risk";
    return `
      <div class="card" style="margin-top:16px;border-color:#cfe0f2;">
        <h3 style="margin-top:0">Result</h3>
        <p style="font-size:22px;margin:4px 0;"><span class="badge ${cls}">${label}</span> &nbsp; ${(result.risk_score * 100).toFixed(1)}% predicted risk</p>
        <p class="muted">Global model version ${result.model_version}</p>
      </div>`;
  },

  federated(status, rounds, isAdmin) {
    const roundRows = rounds.map(r => `
      <tr>
        <td>${r.round_number}</td>
        <td>${r.num_clients}</td>
        <td>${r.total_samples}</td>
        <td>${r.avg_train_loss.toFixed(4)}</td>
        <td>${r.global_val_loss.toFixed(4)}</td>
        <td>${(r.global_val_accuracy * 100).toFixed(1)}%</td>
        <td>v${r.model_version}</td>
      </tr>
    `).join("");

    return `
      <div class="card">
        <h2>How federated training works here</h2>
        <p class="muted">
          Each round: every eligible institution trains the current global model locally on
          its own patients only, then sends back updated <em>weights</em> (never raw data).
          The server averages those weights (FedAvg), weighted by each institution's sample
          count, to produce the next global model — then evaluates it on a fixed internal
          benchmark set to track quality over time.
        </p>
        <p><strong>Eligible institutions this round:</strong> ${status.eligible_institutions.join(", ") || "none — need more labeled patients"}</p>
        ${isAdmin ? `
          <form id="train-form" style="display:flex;gap:10px;align-items:flex-end;">
            <div style="flex:0 0 140px"><label>Rounds to run</label><input type="number" id="train-rounds" value="3" min="1" max="20" /></div>
            <button type="submit" class="primary">Run federated training</button>
          </form>
          <div id="train-status" class="muted" style="margin-top:8px;"></div>
        ` : `<p class="muted">Only admins can trigger training rounds.</p>`}
      </div>
      <div class="card">
        <h2>Training history</h2>
        <table>
          <tr><th>Round</th><th>Clients</th><th>Samples</th><th>Train loss</th><th>Val loss</th><th>Val accuracy</th><th>Model</th></tr>
          ${roundRows || `<tr><td colspan="7" class="muted">No rounds completed yet.</td></tr>`}
        </table>
      </div>
    `;
  },

  institutions(list) {
    const rows = list.map(i => `
      <tr><td>${i.name}</td><td>${i.location || "—"}</td><td>${i.patient_count}</td></tr>
    `).join("");
    return `
      <div class="card">
        <h2>Add institution</h2>
        <form id="institution-form">
          <div class="grid-2">
            <div><label>Name</label><input type="text" id="inst-name" required /></div>
            <div><label>Location</label><input type="text" id="inst-location" /></div>
          </div>
          <button type="submit" class="primary">Add institution</button>
        </form>
      </div>
      <div class="card">
        <h2>Federation nodes</h2>
        <table>
          <tr><th>Name</th><th>Location</th><th>Patients</th></tr>
          ${rows || `<tr><td colspan="3" class="muted">No institutions yet.</td></tr>`}
        </table>
      </div>
    `;
  },
};
