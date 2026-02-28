# EZTIME – Time Attendance & Payroll Demo

## Project Structure

```
eztime/
├── main.py              ← FastAPI app (all business logic + v1 API)
├── requirements.txt
├── EZTIME_DATA.xlsx     ← Place your Excel file here
├── eztime.db            ← Created automatically on first run
├── test_payroll.py      ← Unit tests (no server required)
└── templates/
    └── index.html       ← Full UI (single-page, no JS framework)
```

---

## Run Instructions

### 1. Create virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Place Excel file
Copy `EZTIME_DATA.xlsx` into the same folder as `main.py`.

### 4. Start the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open browser at: **http://localhost:8000**

### 5. First-run seeding
On first run the app automatically creates `eztime.db` and imports all data
from the Excel file.  If the DB already has rows, seeding is skipped.

**To force re-seed:** delete `eztime.db` and restart.

### 6. Environment variables
```bash
EZTIME_EXCEL=path/to/EZTIME_DATA.xlsx   # default: EZTIME_DATA.xlsx
EZTIME_DB=path/to/eztime.db             # default: eztime.db
EZTIME_API_TOKEN=my-secret-token        # default: demo-token
```

---

## Authentication (v1 API)

All `/v1/` endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

| Environment variable | Default value | Notes |
|---------------------|---------------|-------|
| `EZTIME_API_TOKEN`  | `demo-token`  | Change in production! |

If the variable is not set, the server starts with the default token **`demo-token`**
and prints `[AUTH] Token: 'demo-token' (default)` to the console.

---

## API Endpoints

### Legacy (UI) endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/employees` | List all employees |
| GET | `/allowed/{employee_id}` | Allowed subsidiaries/roles + rates |
| POST | `/shifts` | Add a shift |
| DELETE | `/shifts/{id}` | Delete a shift |
| GET | `/daily/{employee_id}/{date}` | Compute daily payroll |
| GET | `/shifts_list/{employee_id}/{date}` | List raw shifts for a day |

### v1 API
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/v1/payroll/daily` | Bearer token | Daily payroll analysis |

#### `/v1/payroll/daily` — Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `employee_id` | string | ✅ | — | e.g. `E1022` |
| `date` | string | ✅ | — | Format `YYYY-MM-DD` |
| `include_shifts` | boolean | ❌ | `true` | Include shift details array |
| `include_breakdown` | boolean | ❌ | `true` | Include hours_by_subsidiary / hours_by_role |

---

## Business Rules

- **Overtime buckets**: ≤threshold → 100%, threshold–threshold+2h → 125%, above → 150%
- **Night rule**: If ≥2h worked in 22:00–06:00 window → threshold = 7h (else 8h)
- **Split-shift rule**: All shifts on the same day are summed first, then buckets applied
- **Max-rate rule**: When multiple (subsidiary, role) combos in one day, use MAX rate for full day
- **Daily deficit**: `max(0, daily_standard − total_hours)`
- **Midnight crossing**: shifts ending past midnight (e.g. 23:00–03:00) handled correctly

### Bug fixed in this version
The original `_night_overlap_hours` function was missing the `[00:00, 06:00]` segment for
same-day early-morning shifts (e.g. `04:00–08:00`). It only had two windows:
`[22:00–24:00]` and `[24:00–30:00]` (next-day). The fix adds `[00:00–06:00]` as a third
window so a shift like `04:00–08:00` correctly gets `2h` of night credit.

---

## Running Unit Tests

```bash
python test_payroll.py           # stdlib unittest, no server needed
python -m pytest test_payroll.py -v
```

Tests cover: overtime buckets (3 required cases), night window detection (including the
fixed early-morning bug), token auth logic, and Asia/Jerusalem timestamp format.

---

## Postman Configuration

### Setup — Token
In Postman, set a collection-level variable or use per-request:
- **Key**: `Authorization`
- **Value**: `Bearer demo-token`

Or set `EZTIME_API_TOKEN=my-secret-token` when starting the server and use that token.

---

### Example 1 — SUCCESS (200 OK)

**Purpose**: Get daily payroll for employee `E1022` on `2026-01-19`
(this shift exists in the seeded sample data).

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL | `http://localhost:8000/v1/payroll/daily` |
| Query param `employee_id` | `E1022` |
| Query param `date` | `2026-01-19` |
| Header `Authorization` | `Bearer demo-token` |
| Header `Content-Type` | `application/json` |

**Full URL with params:**
```
http://localhost:8000/v1/payroll/daily?employee_id=E1022&date=2026-01-19
```

**Postman steps for screenshot:**
1. Open Postman → New Request → `GET`
2. Paste the URL above
3. Go to **Headers** tab → add `Authorization: Bearer demo-token`
4. Click **Send**
5. Expected status: **200 OK**

**Expected response body (example):**
```json
{
  "employee_id": "E1022",
  "employee_name": "...",
  "date": "2026-01-19",
  "overtime_threshold": 8,
  "night_hours_in_window": 0.0,
  "night_rule_active": false,
  "total_hours": 8.75,
  "hours_100": 8.0,
  "hours_125": 0.75,
  "hours_150": 0.0,
  "daily_standard": 9.0,
  "daily_deficit": 0.25,
  "max_rate": 62.0,
  "salary_simulation": 554.13,
  "hours_by_subsidiary": { "חברת בת ה": 8.75 },
  "hours_by_role": { "מלקט": 8.75 },
  "shifts": [
    {
      "shift_id": 1,
      "subsidiary": "חברת בת ה",
      "role": "מלקט",
      "start_time": "07:45",
      "end_time": "16:30",
      "hours": 8.75,
      "hourly_rate": 62.0,
      "cross_midnight": false
    }
  ],
  "calculated_at": "2026-01-19T10:00:00+02:00"
}
```

**Screenshot instructions:**
- The response panel should show `200 OK` in green (top right)
- Screenshot should include: URL bar, Headers tab, response body, status code

---

### Example 2a — FAILURE: Invalid/Missing Token (401 Unauthorized)

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL | `http://localhost:8000/v1/payroll/daily?employee_id=E1022&date=2026-01-19` |
| Header `Authorization` | `Bearer wrong-token` |

**Expected response (401):**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API token"
  }
}
```

**Screenshot instructions:**
- Status code should show `401 Unauthorized` in red
- Include the `Authorization` header and the response body in the screenshot

---

### Example 2b — FAILURE: Employee Not Found (404)

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL | `http://localhost:8000/v1/payroll/daily?employee_id=NOTREAL&date=2026-01-19` |
| Header `Authorization` | `Bearer demo-token` |

**Expected response (404):**
```json
{
  "error": {
    "code": "EMPLOYEE_NOT_FOUND",
    "message": "Employee not found"
  }
}
```

---

### Example 2c — FAILURE: No Shifts for Date (404)

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL | `http://localhost:8000/v1/payroll/daily?employee_id=E1022&date=2000-01-01` |
| Header `Authorization` | `Bearer demo-token` |

**Expected response (404):**
```json
{
  "error": {
    "code": "NO_SHIFTS_FOR_DATE",
    "message": "No shifts found for this employee on the requested date"
  }
}
```

---

### Example 2d — FAILURE: Missing Required Parameter (400)

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL | `http://localhost:8000/v1/payroll/daily?employee_id=E1022` |
| Header `Authorization` | `Bearer demo-token` |
| Note | `date` param is omitted |

**Expected response (400):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required parameter: date"
  }
}
```

---

### Optional: include_shifts and include_breakdown

**Minimal response (no shifts, no breakdown):**
```
GET /v1/payroll/daily?employee_id=E1022&date=2026-01-19&include_shifts=false&include_breakdown=false
Authorization: Bearer demo-token
```
The response will omit the `shifts`, `hours_by_subsidiary`, and `hours_by_role` fields entirely.

---
**Direct QR/NFC Scan Input (Mobile/Device Integration)**

To accept direct QR/NFC scans (instead of manual selection) and update the employee’s working data automatically, the system needs a real scan-capable client (mobile app or kiosk) and a backend endpoint that translates a scan payload into an existing (subsidiary, role) combination and creates the corresponding record in the current database schema. 
In practice, QR/NFC scanning happens on the device level (camera for QR, NFC reader for tags), so the React UI alone cannot “receive scans” unless it runs inside a mobile container (e.g., React Native / Expo) or a device/kiosk environment with scanner APIs. 
The minimal integration approach is: 
(1) encode each QR/NFC tag with a payload that identifies the target assignment, e.g. subsidiary=<name>;role=<name> or a JSON payload
(2) the scan client parses this payload and auto-fills subsidiary and role (and optionally the employee)
(3) the client then calls the existing POST /shifts endpoint with the same fields already supported by the backend (employee_id, date, subsidiary, role, start_time, end_time) 

If you want the system to behave like true “clock-in/clock-out” from a scan (instead of entering start/end times) you must add a small server feature: store scan events (IN/OUT) and then derive shifts from them. Concretely, this requires adding a new table (e.g., RawEvents) with fields like employee_id, timestamp, event_type (IN/OUT), and scan_payload (or resolved subsidiary/role), plus a new endpoint (e.g., POST /events/scan) that receives { employee_id, event_type, scanned_payload }, validates it against AllowedRoles, stores the event, and optionally auto-generates a shift row in RawShifts when it can pair an IN event with the next OUT event. 
This keeps the current payroll logic intact (it already computes daily results from RawShifts) while enabling real scan-driven updates and removing the need for manual entry in the UI 

