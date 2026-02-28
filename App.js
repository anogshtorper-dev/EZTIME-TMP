/**
 * I did not use this React file in the UI demo because my current demo UI is a server-rendered HTML (Jinja) page,
 * and I did not sync it to end-user mobile devices. This file demonstrates the full scanning + shift submission
 * logic that would be required, but it is not wired into the current demo deployment.
 */

import React, { useEffect, useMemo, useState } from "react";

/**
 * This App.js is intentionally aligned with the EXISTING backend contract:
 * - POST   /shifts                       expects: employee_id, date, subsidiary, role, start_time, end_time
 * - GET    /employees                    returns: id, name, daily_standard
 * - GET    /allowed/{employee_id}        returns: role, subsidiary, hourly_rate
 * - GET    /shifts_list/{employee_id}/{work_date} returns: id, subsidiary, role, start_time, end_time, hours
 * - DELETE /shifts/{shift_id}
 * - GET    /v1/payroll/daily             (bonus API) with Authorization: Bearer <token>
 *
 * Source of truth for field names:
 * - ShiftIn schema in main.py: employee_id/date/subsidiary/role/start_time/end_time
 */

function todayYYYYMMDD() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

/**
 * I support a few QR payload formats to keep the demo flexible:
 * 1) JSON: {"subsidiary":"Subsidiary A","role":"Security"}
 * 2) KV:   subsidiary=Subsidiary A;role=Security
 * 3) CSV:  Subsidiary A,Security
 *
 * I intentionally map ONLY to existing backend fields (subsidiary, role).
 * Any proof/device attestation fields are not persisted by the current backend.
 */
function parseScanPayload(raw) {
  const text = (raw || "").trim();
  if (!text) return { subsidiary: "", role: "", error: "Empty scan payload." };

  // Try JSON
  if (text.startsWith("{") && text.endsWith("}")) {
    try {
      const obj = JSON.parse(text);
      const subsidiary = String(obj.subsidiary || obj.company || "").trim();
      const role = String(obj.role || "").trim();
      if (!subsidiary || !role) {
        return { subsidiary: "", role: "", error: "JSON is missing 'subsidiary' or 'role'." };
      }
      return { subsidiary, role, error: "" };
    } catch {
      return { subsidiary: "", role: "", error: "Invalid JSON payload." };
    }
  }

  // Try key=value pairs separated by ; or &
  if (text.includes("=")) {
    const parts = text.split(/[;&]/).map((p) => p.trim()).filter(Boolean);
    const kv = {};
    for (const p of parts) {
      const [k, ...rest] = p.split("=");
      if (!k || rest.length === 0) continue;
      kv[k.trim().toLowerCase()] = rest.join("=").trim();
    }
    const subsidiary = String(kv.subsidiary || kv.company || "").trim();
    const role = String(kv.role || "").trim();
    if (!subsidiary || !role) {
      return { subsidiary: "", role: "", error: "KV payload is missing subsidiary/role." };
    }
    return { subsidiary, role, error: "" };
  }

  // Try CSV: "Subsidiary,Role"
  if (text.includes(",")) {
    const [a, b] = text.split(",").map((x) => x.trim());
    if (!a || !b) return { subsidiary: "", role: "", error: "CSV payload must be 'Subsidiary,Role'." };
    return { subsidiary: a, role: b, error: "" };
  }

  return {
    subsidiary: "",
    role: "",
    error: "Unsupported payload format. Use JSON or 'subsidiary=...;role=...' or 'Subsidiary,Role'.",
  };
}

export default function App() {
  // ------------------------------------------------------------
  // State: auth (bonus API), employees, allowed roles, form fields
  // ------------------------------------------------------------
  const [apiToken, setApiToken] = useState(process.env.REACT_APP_EZTIME_TOKEN || "demo-token");

  const [employees, setEmployees] = useState([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [selectedDate, setSelectedDate] = useState(todayYYYYMMDD());

  const [allowed, setAllowed] = useState([]); // [{role, subsidiary, hourly_rate}]
  const subsidiaries = useMemo(() => {
    const s = new Set(allowed.map((x) => x.subsidiary));
    return Array.from(s).sort();
  }, [allowed]);

  const [subsidiary, setSubsidiary] = useState("");
  const rolesForSubsidiary = useMemo(() => {
    return allowed.filter((x) => x.subsidiary === subsidiary).map((x) => x.role).sort();
  }, [allowed, subsidiary]);

  const [role, setRole] = useState("");

  const [startTime, setStartTime] = useState("08:00");
  const [endTime, setEndTime] = useState("17:00");

  // Scan simulation inputs
  const [scanText, setScanText] = useState("");
  const [scanError, setScanError] = useState("");

  // UI feedback & results
  const [message, setMessage] = useState({ type: "", text: "" });
  const [payroll, setPayroll] = useState(null);
  const [shiftsList, setShiftsList] = useState([]);

  // ------------------------------------------------------------
  // Helpers: UI messaging
  // ------------------------------------------------------------
  function showMessage(type, text) {
    setMessage({ type, text });
    // I keep it simple: auto-clear after 5 seconds
    window.setTimeout(() => setMessage({ type: "", text: "" }), 5000);
  }

  // ------------------------------------------------------------
  // Data loading: employees and allowed roles
  // ------------------------------------------------------------
  async function loadEmployees() {
    // This aligns with GET /employees in main.py
    const res = await fetch("/employees");
    const data = await res.json();
    if (!res.ok) throw new Error("Failed to load employees.");
    setEmployees(data);
  }

  async function loadAllowed(employeeId) {
    // This aligns with GET /allowed/{employee_id} in main.py
    const res = await fetch(`/allowed/${encodeURIComponent(employeeId)}`);
    const data = await res.json();
    if (!res.ok) throw new Error("Failed to load allowed roles.");
    setAllowed(data || []);
  }

  useEffect(() => {
    // I fetch employees once when the app loads.
    loadEmployees().catch((e) => showMessage("err", e.message));
  }, []);

  useEffect(() => {
    // When employee changes, I refresh allowed roles and reset dependent selections.
    if (!selectedEmployeeId) {
      setAllowed([]);
      setSubsidiary("");
      setRole("");
      return;
    }
    loadAllowed(selectedEmployeeId)
      .then(() => {
        setSubsidiary("");
        setRole("");
      })
      .catch((e) => showMessage("err", e.message));
  }, [selectedEmployeeId]);

  // ------------------------------------------------------------
  // Scan actions (QR/NFC simulation)
  // ------------------------------------------------------------
  function applyScan() {
    // I parse the scan payload and map it ONLY to existing fields: subsidiary + role.
    const parsed = parseScanPayload(scanText);
    if (parsed.error) {
      setScanError(parsed.error);
      return;
    }
    setScanError("");
    setSubsidiary(parsed.subsidiary);
    setRole(parsed.role);

    // I also show a friendly success message.
    showMessage("ok", `Scan applied: subsidiary='${parsed.subsidiary}', role='${parsed.role}'`);
  }

  function simulateNfcTap() {
    // In real mobile apps, NFC delivers a tag payload.
    // Here I simulate a typical payload string.
    const simulated = `subsidiary=${subsidiaries[0] || "Subsidiary A"};role=${rolesForSubsidiary[0] || "Role A"}`;
    setScanText(simulated);
    setScanError("");
    showMessage("warn", "NFC simulated. Click 'Apply Scan' to use it.");
  }

  // ------------------------------------------------------------
  // Shift CRUD aligned with backend
  // ------------------------------------------------------------
  async function addShift() {
    // Validate client-side before calling POST /shifts
    if (!selectedEmployeeId || !selectedDate || !subsidiary || !role || !startTime || !endTime) {
      showMessage("err", "Please fill in: employee, date, subsidiary, role, start & end time.");
      return;
    }

    const payload = {
      employee_id: selectedEmployeeId,
      date: selectedDate,
      subsidiary,
      role,
      start_time: startTime,
      end_time: endTime,
    };

    const res = await fetch("/shifts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      // Backend uses HTTPException detail or JSONResponse in different places
      showMessage("err", data?.detail || "Error adding shift.");
      return;
    }

    if (data?.warning) showMessage("warn", data.warning);
    else showMessage("ok", "Shift added successfully.");

    // After adding a shift, I refresh payroll + shifts list to reflect latest DB state.
    await calculateDaily();
  }

  async function loadShiftsList() {
    if (!selectedEmployeeId || !selectedDate) return;
    const res = await fetch(`/shifts_list/${encodeURIComponent(selectedEmployeeId)}/${encodeURIComponent(selectedDate)}`);
    const rows = await res.json();
    if (!res.ok) throw new Error("Failed to load shifts list.");
    setShiftsList(rows || []);
  }

  async function deleteShift(shiftId) {
    const ok = window.confirm("Delete this shift?");
    if (!ok) return;

    await fetch(`/shifts/${shiftId}`, { method: "DELETE" });
    await calculateDaily();
  }

  // ------------------------------------------------------------
  // Bonus API: /v1/payroll/daily with Bearer token
  // ------------------------------------------------------------
  async function calculateDaily() {
    if (!selectedEmployeeId || !selectedDate) {
      showMessage("err", "Select employee and date first.");
      return;
    }

    const qs = new URLSearchParams({
      employee_id: selectedEmployeeId,
      date: selectedDate,
      include_shifts: "true",
      include_breakdown: "true",
    });

    const res = await fetch(`/v1/payroll/daily?${qs.toString()}`, {
      headers: {
        Authorization: `Bearer ${apiToken}`,
      },
    });

    const body = await res.json();

    if (!res.ok) {
      // Spec-compliant shape: { error: { code, message } }
      const msg = body?.error?.message || "Failed to calculate daily payroll.";
      showMessage("err", msg);
      setPayroll(null);
      setShiftsList([]);
      return;
    }

    setPayroll(body);
    await loadShiftsList();
    showMessage("ok", "Daily payroll calculated.");
  }

  // ------------------------------------------------------------
  // Rendering helpers
  // ------------------------------------------------------------
  const selectedEmployee = useMemo(
    () => employees.find((e) => String(e.id) === String(selectedEmployeeId)),
    [employees, selectedEmployeeId]
  );

  function formatILS(amount) {
    const n = Number(amount || 0);
    return n.toLocaleString("en-IL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  return (
    <div style={{ fontFamily: "system-ui, Segoe UI, Arial", padding: 20, maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 6 }}>EZTIME – Demo (React Logic)</h1>
      <div style={{ color: "#555", marginBottom: 18 }}>
        I aligned all entity names and payload fields to the current backend: subsidiary/role/shift times and the bonus /v1 API.
      </div>

      {/* Message banner */}
      {message.text ? (
        <div
          style={{
            marginBottom: 14,
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid #ddd",
            background:
              message.type === "err" ? "#ffebee" : message.type === "warn" ? "#fff8e1" : "#e8f5e9",
          }}
        >
          {message.text}
        </div>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 18 }}>
        {/* Left panel */}
        <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 14 }}>
          <h3 style={{ marginTop: 0 }}>Shift Input (Aligned with /shifts)</h3>

          <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>API Token (Bonus /v1)</label>
          <input
            value={apiToken}
            onChange={(e) => setApiToken(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
            placeholder="Bearer token value (default: demo-token)"
          />

          <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>Employee</label>
          <select
            value={selectedEmployeeId}
            onChange={(e) => setSelectedEmployeeId(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
          >
            <option value="">— select —</option>
            {employees.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.id})
              </option>
            ))}
          </select>

          <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
          />

          <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>Subsidiary</label>
          <select
            value={subsidiary}
            onChange={(e) => {
              setSubsidiary(e.target.value);
              setRole("");
            }}
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
            disabled={!selectedEmployeeId}
          >
            <option value="">{selectedEmployeeId ? "— select —" : "— select employee first —"}</option>
            {subsidiaries.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>Role</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
            disabled={!subsidiary}
          >
            <option value="">{subsidiary ? "— select —" : "— select subsidiary first —"}</option>
            {rolesForSubsidiary.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div>
              <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>Start Time</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontWeight: 700, fontSize: 13 }}>End Time</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={addShift} style={{ padding: "10px 12px", cursor: "pointer" }}>
              Add Shift
            </button>
            <button onClick={calculateDaily} style={{ padding: "10px 12px", cursor: "pointer" }}>
              Calculate (Bonus /v1)
            </button>
          </div>

          <hr style={{ margin: "16px 0" }} />

          <h3 style={{ marginTop: 0 }}>Scan (QR/NFC) – Demo Mapping</h3>
          <div style={{ fontSize: 13, color: "#555", marginBottom: 8 }}>
            I only map scan results to <b>subsidiary</b> and <b>role</b>, because those are the only fields the current backend persists.
          </div>

          <textarea
            value={scanText}
            onChange={(e) => setScanText(e.target.value)}
            placeholder={`Example JSON:\n{"subsidiary":"Subsidiary A","role":"Security"}\n\nOr KV:\nsubsidiary=Subsidiary A;role=Security`}
            style={{ width: "100%", minHeight: 110, padding: 8 }}
          />

          {scanError ? <div style={{ color: "#b71c1c", marginTop: 6 }}>{scanError}</div> : null}

          <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
            <button onClick={applyScan} style={{ padding: "10px 12px", cursor: "pointer" }}>
              Apply Scan
            </button>
            <button onClick={simulateNfcTap} style={{ padding: "10px 12px", cursor: "pointer" }}>
              Simulate NFC Tap
            </button>
          </div>
        </div>

        {/* Right panel */}
        <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 14 }}>
          <h3 style={{ marginTop: 0 }}>Daily Payroll Result (Bonus API)</h3>

          {!payroll ? (
            <div style={{ color: "#777" }}>No results yet. Select employee/date and click Calculate.</div>
          ) : (
            <>
              <div style={{ marginBottom: 10 }}>
                <b>{payroll.employee_name}</b> · {payroll.date}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 12 }}>
                <Stat label="Total Hours" value={Number(payroll.total_hours).toFixed(2)} />
                <Stat label="Hours @100%" value={Number(payroll.hours_100).toFixed(2)} />
                <Stat label="Hours @125%" value={Number(payroll.hours_125).toFixed(2)} />
                <Stat label="Hours @150%" value={Number(payroll.hours_150).toFixed(2)} />
                <Stat label="Daily Deficit" value={Number(payroll.daily_deficit).toFixed(2)} />
                <Stat label="OT Threshold (h)" value={payroll.overtime_threshold} />
              </div>

              <div style={{ padding: 12, borderRadius: 10, background: "#e8f5e9", marginBottom: 12 }}>
                <div style={{ fontSize: 26, fontWeight: 800 }}>₪{formatILS(payroll.salary_simulation)}</div>
                <div style={{ color: "#333" }}>
                  Salary Simulation (max_rate: ₪{payroll.max_rate}/h)
                </div>
                <div style={{ marginTop: 6, fontSize: 13, color: "#555" }}>
                  Night rule active: <b>{payroll.night_rule_active ? "true" : "false"}</b> · night_hours_in_window:{" "}
                  <b>{Number(payroll.night_hours_in_window).toFixed(2)}</b>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <Breakdown title="Hours by Subsidiary" obj={payroll.hours_by_subsidiary} />
                <Breakdown title="Hours by Role" obj={payroll.hours_by_role} />
              </div>

              <hr style={{ margin: "16px 0" }} />

              <h3 style={{ marginTop: 0 }}>Shifts (DB View)</h3>
              {!shiftsList.length ? (
                <div style={{ color: "#777" }}>No shifts in DB for this employee/date.</div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ textAlign: "left" }}>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 8 }}>Subsidiary</th>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 8 }}>Role</th>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 8 }}>Start</th>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 8 }}>End</th>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 8 }}>Hours</th>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 8 }} />
                    </tr>
                  </thead>
                  <tbody>
                    {shiftsList.map((s) => (
                      <tr key={s.id}>
                        <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>{s.subsidiary}</td>
                        <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>{s.role}</td>
                        <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>{s.start_time}</td>
                        <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>{s.end_time}</td>
                        <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>
                          {Number(s.hours).toFixed(2)}
                        </td>
                        <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>
                          <button onClick={() => deleteShift(s.id)} style={{ cursor: "pointer" }}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      </div>

      <footer style={{ marginTop: 16, color: "#777", fontSize: 12 }}>
        Note: The scan demo maps to existing persisted fields only (subsidiary/role). The current backend does not store proof_type/device attestation.
      </footer>
    </div>
  );
}

/**
 * Small stat card for numeric KPIs.
 */
function Stat({ label, value }) {
  return (
    <div style={{ padding: 12, borderRadius: 10, border: "1px solid #eee", background: "#fafafa" }}>
      <div style={{ fontSize: 22, fontWeight: 800 }}>{value}</div>
      <div style={{ fontSize: 12, color: "#666" }}>{label}</div>
    </div>
  );
}

/**
 * Renders a key-value breakdown object: { "Subsidiary A": 6.0, ... }
 */
function Breakdown({ title, obj }) {
  const entries = Object.entries(obj || {});
  return (
    <div style={{ padding: 12, borderRadius: 10, border: "1px solid #eee", background: "#fafafa" }}>
      <div style={{ fontWeight: 800, marginBottom: 8 }}>{title}</div>
      {!entries.length ? (
        <div style={{ color: "#777" }}>—</div>
      ) : (
        entries.map(([k, v]) => (
          <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0" }}>
            <span>{k}</span>
            <b>{Number(v).toFixed(2)}h</b>
          </div>
        ))
      )}
    </div>
  );
}
