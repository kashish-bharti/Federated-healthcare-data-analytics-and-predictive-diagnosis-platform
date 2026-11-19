const App = {
  user: null,
  activeTab: "dashboard",
  page: "login", // login | register

  el() { return document.getElementById("app"); },

  async init() {
    if (Api.token) {
      try {
        this.user = await Api.me();
        await this.renderShell();
        return;
      } catch (e) {
        Api.setToken(null);
      }
    }
    this.renderLogin();
  },

  // ---------------- Auth pages ----------------
  renderLogin(errorMsg = "") {
    this.el().innerHTML = Views.loginPage(errorMsg);
    document.getElementById("login-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("login-email").value;
      const password = document.getElementById("login-password").value;
      try {
        await Api.login(email, password);
        this.user = await Api.me();
        await this.renderShell();
      } catch (err) {
        this.renderLogin(err.message);
      }
    });
    document.getElementById("show-register").addEventListener("click", async () => {
      let institutions = [];
      try { institutions = await Api.listInstitutions(); } catch { /* not authenticated yet, fine */ }
      this.renderRegister(institutions);
    });
  },

  async renderRegister(institutions = [], errorMsg = "") {
    this.el().innerHTML = Views.registerPage(institutions, errorMsg);
    document.getElementById("register-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        email: document.getElementById("reg-email").value,
        password: document.getElementById("reg-password").value,
        full_name: document.getElementById("reg-name").value || null,
        institution_id: document.getElementById("reg-institution").value || null,
        role: document.getElementById("reg-role").value,
      };
      if (payload.institution_id) payload.institution_id = parseInt(payload.institution_id, 10);
      try {
        await Api.register(payload);
        await Api.login(payload.email, payload.password);
        this.user = await Api.me();
        await this.renderShell();
      } catch (err) {
        this.renderRegister(institutions, err.message);
      }
    });
    document.getElementById("show-login").addEventListener("click", () => this.renderLogin());
  },

  logout() {
    Api.setToken(null);
    this.user = null;
    this.renderLogin();
  },

  // ---------------- Authenticated shell ----------------
  async renderShell() {
    const inner = await this.renderTabContent(this.activeTab);
    this.el().innerHTML = Views.shell(this.user, this.activeTab, inner);
    this.wireShellEvents();
  },

  wireShellEvents() {
    document.getElementById("logout-btn").addEventListener("click", () => this.logout());
    document.querySelectorAll(".nav button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        this.activeTab = btn.dataset.tab;
        await this.renderShell();
      });
    });
    this.wireTabEvents(this.activeTab);
  },

  async renderTabContent(tab) {
    try {
      if (tab === "dashboard") {
        const [status, patients, history] = await Promise.all([
          Api.federatedStatus(), Api.listPatients(), Api.predictionHistory(),
        ]);
        return Views.dashboard(status, patients.length, history.length);
      }
      if (tab === "patients") {
        const patients = await Api.listPatients();
        return Views.patients(patients);
      }
      if (tab === "predict") {
        const [patients, history] = await Promise.all([Api.listPatients(), Api.predictionHistory()]);
        return Views.predict(patients, history);
      }
      if (tab === "federated") {
        const [status, rounds] = await Promise.all([Api.federatedStatus(), Api.federatedRounds()]);
        return Views.federated(status, rounds, this.user.role === "admin");
      }
      if (tab === "institutions") {
        const list = await Api.listInstitutions();
        return Views.institutions(list);
      }
    } catch (err) {
      return `<div class="card"><p class="error">${err.message}</p></div>`;
    }
    return "";
  },

  wireTabEvents(tab) {
    if (tab === "patients") {
      const form = document.getElementById("patient-form");
      if (form) form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const labelVal = document.getElementById("p-label").value;
        const payload = {
          age: parseFloat(document.getElementById("p-age").value),
          bmi: parseFloat(document.getElementById("p-bmi").value),
          systolic_bp: parseFloat(document.getElementById("p-bp").value),
          glucose: parseFloat(document.getElementById("p-glucose").value),
          cholesterol: parseFloat(document.getElementById("p-cholesterol").value),
          smoker: document.getElementById("p-smoker").checked,
          diagnosis_label: labelVal === "" ? null : parseInt(labelVal, 10),
        };
        try {
          await Api.createPatient(payload);
          await this.renderShell();
        } catch (err) {
          alert(err.message);
        }
      });
    }

    if (tab === "predict") {
      const patientSelect = document.getElementById("pred-patient");
      const patientsCache = {};
      document.querySelectorAll("#pred-patient option").forEach(async () => {});
      if (patientSelect) {
        Api.listPatients().then(patients => {
          patients.forEach(p => patientsCache[p.id] = p);
        });
        patientSelect.addEventListener("change", () => {
          const p = patientsCache[patientSelect.value];
          if (p) {
            document.getElementById("pred-age").value = p.age;
            document.getElementById("pred-bmi").value = p.bmi;
            document.getElementById("pred-bp").value = p.systolic_bp;
            document.getElementById("pred-glucose").value = p.glucose;
            document.getElementById("pred-cholesterol").value = p.cholesterol;
            document.getElementById("pred-smoker").checked = p.smoker;
          }
        });
      }

      const form = document.getElementById("predict-form");
      if (form) form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const patientId = document.getElementById("pred-patient").value;
        const payload = {
          patient_id: patientId ? parseInt(patientId, 10) : null,
          age: parseFloat(document.getElementById("pred-age").value),
          bmi: parseFloat(document.getElementById("pred-bmi").value),
          systolic_bp: parseFloat(document.getElementById("pred-bp").value),
          glucose: parseFloat(document.getElementById("pred-glucose").value),
          cholesterol: parseFloat(document.getElementById("pred-cholesterol").value),
          smoker: document.getElementById("pred-smoker").checked,
        };
        try {
          const result = await Api.predict(payload);
          document.getElementById("predict-result").innerHTML = Views.predictResult(result);
        } catch (err) {
          document.getElementById("predict-result").innerHTML = `<p class="error">${err.message}</p>`;
        }
      });
    }

    if (tab === "federated") {
      const form = document.getElementById("train-form");
      if (form) form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const rounds = parseInt(document.getElementById("train-rounds").value, 10);
        const statusEl = document.getElementById("train-status");
        statusEl.textContent = "Training in progress — this runs local training on each eligible institution then aggregates weights...";
        try {
          await Api.federatedTrain(rounds);
          await this.renderShell();
        } catch (err) {
          statusEl.textContent = "";
          statusEl.parentElement.insertAdjacentHTML("beforeend", `<p class="error">${err.message}</p>`);
        }
      });
    }

    if (tab === "institutions") {
      const form = document.getElementById("institution-form");
      if (form) form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
          name: document.getElementById("inst-name").value,
          location: document.getElementById("inst-location").value || null,
        };
        try {
          await Api.createInstitution(payload);
          await this.renderShell();
        } catch (err) {
          alert(err.message);
        }
      });
    }
  },
};

document.addEventListener("DOMContentLoaded", () => App.init());
