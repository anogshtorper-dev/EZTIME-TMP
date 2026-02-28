import React, { useState, useEffect, useMemo } from 'react';

/**
 * Core fields to match the data in the back-end:
 * employee_id, timestamp_utc, event_type(IN/OUT), subsidiary_id, role_id, site_id,
 * proof_type(GPS/GEOFENCE/QR/NFC), device_id, attestation_status
 */

// =============================
// Sample data (replace with API calls)
// =============================
const DEMO_EMPLOYEES = [
  { employee_id: "E1001", full_name: "Dana Alon", status: "active", allowed_roles: ["Security", "Warehouse"] },
  { employee_id: "E1002", full_name: "Amit Edri", status: "active", allowed_roles: ["Security"] },
];

const DEMO_SITES = [
  { site_id: "S1", site_name: "Site A", allowed_roles: ["Security", "Warehouse"] },
  { site_id: "S2", site_name: "Site B", allowed_roles: ["Warehouse"] },
];

// =============================
// App.js
// =============================

export default function App() {
  // State
  const [employeeId, setEmployeeId] = useState("");
  const [eventType, setEventType] = useState("IN");  // IN / OUT
  const [subsidiary, setSubsidiary] = useState("");
  const [role, setRole] = useState("");
  const [scanPayload, setScanPayload] = useState("");
  const [manualReason, setManualReason] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [qrError, setQrError] = useState("");
  const [nfcError, setNfcError] = useState("");

  const [employees, setEmployees] = useState(DEMO_EMPLOYEES);
  const [sites, setSites] = useState(DEMO_SITES);

  const activeEmployee = useMemo(() => employees.find(e => e.employee_id === employeeId), [employeeId]);
  const allowedRolesForSite = useMemo(() => {
    if (subsidiary) {
      const site = sites.find(s => s.site_name === subsidiary);
      return site ? site.allowed_roles : [];
    }
    return [];
  }, [subsidiary, sites]);

  // ============================
  // Helper functions
  // ============================

  const handleScan = (payload) => {
    // This is a simulation of how the backend would process the scan payload.
    // You will replace this with an actual API request to resolve the scan.
    const parsed = parseScanPayload(payload);
    if (parsed.error) {
      setQrError(parsed.error);
    } else {
      setSubsidiary(parsed.subsidiary);
      setRole(parsed.role);
      setStatusMessage(`Scan successful! Subsidiary: ${parsed.subsidiary}, Role: ${parsed.role}`);
    }
  };

  const parseScanPayload = (payload) => {
    const text = (payload || "").trim();
    if (text.includes("=")) {
      const parts = text.split(";").map(part => part.trim());
      const kv = {};
      parts.forEach(p => {
        const [key, value] = p.split("=");
        if (key && value) kv[key] = value;
      });
      const subsidiary = kv["subsidiary"];
      const role = kv["role"];
      if (!subsidiary || !role) {
        return { subsidiary: "", role: "", error: "Invalid payload: missing subsidiary or role" };
      }
      return { subsidiary, role, error: "" };
    }
    return { subsidiary: "", role: "", error: "Unsupported scan payload format." };
  };

  const handleManualSubmit = () => {
    if (!employeeId || !subsidiary || !role) {
      setStatusMessage("Please fill in employee, subsidiary, and role manually.");
      return;
    }

    // Here you would submit the data to your backend API (or simulate it)
    const payload = {
      employee_id: employeeId,
      event_type: eventType,
      subsidiary,
      role,
      manual_reason: manualReason,
    };

    setStatusMessage(`Manual entry saved: ${JSON.stringify(payload)}`);
  };

  // ============================
  // Rendering
  // ============================

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif", maxWidth: "900px", margin: "auto", background: "#f9f9f9", borderRadius: "8px" }}>
      <h1>EZTIME - Clock-in/out System</h1>

      <div style={{ marginBottom: "20px", borderBottom: "1px solid #ccc", paddingBottom: "20px" }}>
        <label>Select Employee</label>
        <select
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          style={{ width: "100%", padding: "8px", margin: "10px 0", fontSize: "14px" }}
        >
          <option value="">Select Employee</option>
          {employees.map((e) => (
            <option key={e.employee_id} value={e.employee_id}>{e.full_name} ({e.status})</option>
          ))}
        </select>
      </div>

      {activeEmployee && (
        <>
          <div style={{ marginBottom: "20px" }}>
            <label>Event Type</label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              style={{ width: "100%", padding: "8px", margin: "10px 0", fontSize: "14px" }}
            >
              <option value="IN">Clock-in</option>
              <option value="OUT">Clock-out</option>
            </select>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label>Scan Payload (QR/NFC)</label>
            <textarea
              value={scanPayload}
              onChange={(e) => setScanPayload(e.target.value)}
              placeholder="Scan the QR code or enter the payload manually"
              style={{ width: "100%", padding: "8px", fontSize: "14px", height: "80px" }}
            ></textarea>
            <button
              onClick={() => handleScan(scanPayload)}
              style={{ marginTop: "10px", padding: "10px", background: "#4CAF50", color: "#fff", border: "none", cursor: "pointer" }}
            >
              Resolve Scan
            </button>
          </div>

          {qrError && (
            <div style={{ color: "red", fontSize: "14px" }}>
              <strong>Error: </strong>{qrError}
            </div>
          )}

          <div style={{ marginBottom: "20px" }}>
            <label>Subsidiary</label>
            <select
              value={subsidiary}
              onChange={(e) => setSubsidiary(e.target.value)}
              style={{ width: "100%", padding: "8px", margin: "10px 0", fontSize: "14px" }}
            >
              <option value="">Select Subsidiary</option>
              {Object.keys(allowedRolesForSite).map((subsidiaryOption) => (
                <option key={subsidiaryOption} value={subsidiaryOption}>{subsidiaryOption}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label>Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              style={{ width: "100%", padding: "8px", margin: "10px 0", fontSize: "14px" }}
              disabled={!subsidiary}
            >
              <option value="">Select Role</option>
              {allowedRolesForSite.map((roleOption) => (
                <option key={roleOption} value={roleOption}>{roleOption}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label>Manual Reason (if applicable)</label>
            <textarea
              value={manualReason}
              onChange={(e) => setManualReason(e.target.value)}
              placeholder="Provide a reason for manual entry (if any)"
              style={{ width: "100%", padding: "8px", fontSize: "14px", height: "80px" }}
            ></textarea>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <button
              onClick={handleManualSubmit}
              style={{ padding: "10px", background: "#ff5722", color: "#fff", border: "none", cursor: "pointer" }}
            >
              Save Event (Manual Entry)
            </button>
          </div>

          {statusMessage && (
            <div style={{ marginTop: "20px", padding: "10px", backgroundColor: "#e8f5e9", borderRadius: "5px", fontSize: "14px", color: "#4CAF50" }}>
              {statusMessage}
            </div>
          )}
        </>
      )}
    </div>
  );
}
