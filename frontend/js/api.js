/* Thin fetch wrapper around the FastAPI backend. */
const Api = {
  token: localStorage.getItem("fedhealth_token") || null,

  setToken(token) {
    this.token = token;
    if (token) localStorage.setItem("fedhealth_token", token);
    else localStorage.removeItem("fedhealth_token");
  },

  async request(path, { method = "GET", body = null, form = false } = {}) {
    const headers = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
    let payload = body;

    if (body && !form) {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }

    const res = await fetch(`${window.API_BASE_URL}${path}`, { method, headers, body: payload });

    if (res.status === 204) return null;

    let data;
    try { data = await res.json(); } catch { data = null; }

    if (!res.ok) {
      const detail = data && data.detail ? data.detail : `Request failed (${res.status})`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  },

  // ---- Auth ----
  async login(email, password) {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const data = await this.request("/auth/login", { method: "POST", body: form, form: true });
    this.setToken(data.access_token);
    return data;
  },
  register(payload) {
    return this.request("/auth/register", { method: "POST", body: payload });
  },
  me() {
    return this.request("/auth/me");
  },

  // ---- Institutions ----
  listInstitutions() {
    return this.request("/institutions");
  },
  createInstitution(payload) {
    return this.request("/institutions", { method: "POST", body: payload });
  },

  // ---- Patients ----
  listPatients() {
    return this.request("/patients");
  },
  createPatient(payload) {
    return this.request("/patients", { method: "POST", body: payload });
  },

  // ---- Predictions ----
  predict(payload) {
    return this.request("/predictions/predict", { method: "POST", body: payload });
  },
  predictionHistory() {
    return this.request("/predictions/history");
  },

  // ---- Federated learning ----
  federatedStatus() {
    return this.request("/federated/status");
  },
  federatedRounds() {
    return this.request("/federated/rounds");
  },
  federatedTrain(rounds) {
    return this.request("/federated/train", { method: "POST", body: { rounds } });
  },
};
