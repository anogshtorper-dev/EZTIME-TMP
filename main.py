"""
EZTIME – Time Attendance & Payroll Demo
Extension for holding-company multi-subsidiary scenario.

Changes in this version (v1 API addition):
  - Added /v1/payroll/daily  (GET) with Bearer-token auth
  - Added APIRouter for /v1 prefix routing (all existing routes unchanged)
  - Added _api_error() helper for spec-compliant JSON error shapes
  - Added _now_jerusalem() for ISO-8601 timestamps with Asia/Jerusalem offset
  - Enriched compute_daily() return to include shift_id, cross_midnight, daily_standard
  - No existing UI routes or business logic removed or broken
"""

import sqlite3, os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo          # stdlib ≥ 3.9

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Header, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "employee_id":        ["employee_id", "id"],
    "employee_name":      ["full_name", "name", "employee_name"],
    "daily_standard":     ["daily_standard_hours", "daily_standard"],
    "allowed_roles_csv":  ["allowed_roles_csv", "allowed_roles"],
    "allowed_companies":  ["allowed_companies_csv", "allowed_companies"],
    "role":               ["role_name", "role", "job", "position"],
    "company":            ["company_name", "company", "subsidiary", "subsidiary_name"],
    "hourly_rate":        ["rate", "hourly_rate", "wage"],
    "work_date":          ["work_date", "date"],
    "start_time":         ["start_time"],
    "end_time":           ["end_time"],
}

EXCEL_PATH = os.environ.get("EZTIME_EXCEL", "EZTIME_DATA.xlsx")
DB_PATH    = os.environ.get("EZTIME_DB",    "eztime.db")

# Auth: read from env, fall back to "demo-token"
API_TOKEN    = os.environ.get("EZTIME_API_TOKEN", "demo-token")
TZ_JERUSALEM = ZoneInfo("Asia/Jerusalem")

app       = FastAPI(title="EZTIME Demo")
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class _TokenError(Exception):
    pass

def _check_token(authorization: Optional[str]) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise _TokenError()
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_TOKEN:
        raise _TokenError()

def _api_error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})

def _now_jerusalem() -> str:
    return datetime.now(TZ_JERUSALEM).isoformat(timespec="seconds")

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.cursor().executescript("""
        CREATE TABLE IF NOT EXISTS Employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            daily_standard REAL NOT NULL DEFAULT 8.0
        );
        CREATE TABLE IF NOT EXISTS AllowedRoles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            role TEXT NOT NULL,
            subsidiary TEXT NOT NULL,
            hourly_rate REAL NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES Employees(id)
        );
        CREATE TABLE IF NOT EXISTS RawShifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            date TEXT NOT NULL,
            subsidiary TEXT NOT NULL,
            role TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES Employees(id)
        );
    """)
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Excel seeding
# ---------------------------------------------------------------------------

def _find_col(df, candidates):
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None

def seed_from_excel():
    conn = get_conn()
    if conn.execute("SELECT COUNT(*) FROM Employees").fetchone()[0] > 0:
        print("[SEED] DB already seeded – skipping.")
        conn.close()
        return

    if not os.path.exists(EXCEL_PATH):
        print(f"[SEED] Excel file '{EXCEL_PATH}' not found – skipping seed.")
        conn.close()
        return

    xl = pd.ExcelFile(EXCEL_PATH)
    print(f"[SEED] Sheet names: {xl.sheet_names}")

    sheet_emp = xl.parse(xl.sheet_names[0])
    print(f"[SEED] EmployeeData columns: {sheet_emp.columns.tolist()}")
    col_id   = _find_col(sheet_emp, COLUMN_MAP["employee_id"])
    col_name = _find_col(sheet_emp, COLUMN_MAP["employee_name"])
    col_std  = _find_col(sheet_emp, COLUMN_MAP["daily_standard"])
    print(f"[SEED] Detected emp cols → id={col_id} name={col_name} std={col_std}")

    employees = []
    for _, row in sheet_emp.iterrows():
        employees.append((
            str(row[col_id]).strip(),
            str(row[col_name]).strip(),
            float(row[col_std]) if col_std else 8.0,
        ))
    conn.executemany("INSERT OR IGNORE INTO Employees(id,name,daily_standard) VALUES(?,?,?)", employees)

    rates_sheet = None
    for sn in xl.sheet_names:
        df = xl.parse(sn)
        if _find_col(df, COLUMN_MAP["hourly_rate"]):
            rates_sheet = sn
            break

    if rates_sheet:
        df_rates = xl.parse(rates_sheet)
        print(f"[SEED] Rates sheet '{rates_sheet}' columns: {df_rates.columns.tolist()}")
        r_eid  = _find_col(df_rates, COLUMN_MAP["employee_id"])
        r_role = _find_col(df_rates, COLUMN_MAP["role"])
        r_comp = _find_col(df_rates, COLUMN_MAP["company"])
        r_rate = _find_col(df_rates, COLUMN_MAP["hourly_rate"])
        allowed = []
        for _, row in df_rates.iterrows():
            allowed.append((
                str(row[r_eid]).strip(), str(row[r_role]).strip(),
                str(row[r_comp]).strip(), float(row[r_rate]),
            ))
        conn.executemany(
            "INSERT INTO AllowedRoles(employee_id,role,subsidiary,hourly_rate) VALUES(?,?,?,?)",
            allowed,
        )

    for sn in xl.sheet_names:
        df = xl.parse(sn)
        if _find_col(df, COLUMN_MAP["start_time"]) and _find_col(df, COLUMN_MAP["end_time"]):
            print(f"[SEED] Times sheet '{sn}' columns: {df.columns.tolist()}")
            t_eid   = _find_col(df, COLUMN_MAP["employee_id"])
            t_date  = _find_col(df, COLUMN_MAP["work_date"])
            t_role  = _find_col(df, COLUMN_MAP["role"])
            t_comp  = _find_col(df, COLUMN_MAP["company"])
            t_start = _find_col(df, COLUMN_MAP["start_time"])
            t_end   = _find_col(df, COLUMN_MAP["end_time"])
            shifts = []
            for _, row in df.iterrows():
                try:
                    shifts.append((
                        str(row[t_eid]).strip(), str(row[t_date])[:10],
                        str(row[t_comp]).strip(), str(row[t_role]).strip(),
                        str(row[t_start]).strip()[:5], str(row[t_end]).strip()[:5],
                    ))
                except Exception:
                    pass
            conn.executemany(
                "INSERT INTO RawShifts(employee_id,date,subsidiary,role,start_time,end_time) VALUES(?,?,?,?,?,?)",
                shifts,
            )
            break

    conn.commit()
    conn.close()
    print("[SEED] Done.")

# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def _parse_hhmm(s: str) -> float:
    h, m = map(int, s.strip().split(":"))
    return h + m / 60.0

def _night_overlap_hours(start_h: float, end_h: float) -> float:
    """
    Count overlap of this shift with the 22:00–06:00 night window.

    Uses a 0–48h minute axis. The night window is split into two segments:
      [22:00, 24:00] → [1320, 1440]
      [00:00, 06:00] → [1440, 1800]  (next-day early morning)

    If shift crosses midnight, end is normalised by adding 24*60.
    This correctly handles all three cases:
      - evening-only shift (20:00-23:00): only first window overlaps
      - midnight-crossing  (23:00-03:00): both windows may overlap
      - early-morning only (04:00-08:00): only second window overlaps
    """
    def to_min(h):
        return int(round(h * 60))

    s = to_min(start_h)
    e = to_min(end_h)
    if e <= s:
        e += 24 * 60

    # Three segments covering the full 22:00–06:00 night window:
    #   [0,    360]  = 00:00–06:00  same-day early morning (shift does NOT cross midnight)
    #   [1320, 1440] = 22:00–24:00  evening
    #   [1440, 1800] = 00:00–06:00  next day (midnight-crossing shifts land here)
    # Without the first segment, a shift like 04:00–08:00 would wrongly get 0 night hours.
    night_windows = [(0, 6 * 60), (22 * 60, 24 * 60), (24 * 60, 30 * 60)]
    overlap = 0
    for a, b in night_windows:
        overlap += max(0, min(e, b) - max(s, a))
    return overlap / 60.0

def _shift_hours(start_str: str, end_str: str) -> float:
    s = _parse_hhmm(start_str)
    e = _parse_hhmm(end_str)
    if e <= s:
        e += 24.0
    return e - s

def compute_daily(employee_id: str, work_date: str) -> dict:
    """
    Core payroll calculation for one employee on one date.

    Business rules:
      1. Split-shift rule : sum ALL shift hours first, THEN apply buckets.
      2. Night rule       : if total night-window hours >= 2 → threshold = 7h (else 8h).
      3. Overtime buckets : 0..threshold @100%, threshold..threshold+2 @125%, rest @150%.
      4. Max-rate rule    : use highest hourly_rate among all (subsidiary,role) today.
      5. Salary formula   : h100*rate + h125*rate*1.25 + h150*rate*1.5
      6. Daily deficit    : max(0, daily_standard - total_hours)
    """
    conn = get_conn()
    emp = conn.execute("SELECT * FROM Employees WHERE id=?", (employee_id,)).fetchone()
    if not emp:
        conn.close()
        raise ValueError(f"Employee {employee_id} not found")

    shifts = conn.execute(
        "SELECT * FROM RawShifts WHERE employee_id=? AND date=? ORDER BY start_time",
        (employee_id, work_date),
    ).fetchall()
    conn.close()

    if not shifts:
        return {
            "employee_id": employee_id, "employee_name": emp["name"],
            "date": work_date, "daily_standard": emp["daily_standard"],
            "shifts": [], "total_hours": 0, "night_hours_in_window": 0,
            "overtime_threshold": 8,
            "hours_100": 0, "hours_125": 0, "hours_150": 0,
            "max_rate": 0, "salary_simulation": 0,
            "daily_deficit": round(emp["daily_standard"], 4),
            "hours_by_subsidiary": {}, "hours_by_role": {},
        }

    shift_details     = []
    hours_by_sub      = {}
    hours_by_role     = {}
    total_night_window = 0.0
    rates_used        = {}

    conn2 = get_conn()
    for sh in shifts:
        h       = _shift_hours(sh["start_time"], sh["end_time"])
        night_h = _night_overlap_hours(
            _parse_hhmm(sh["start_time"]), _parse_hhmm(sh["end_time"])
        )
        total_night_window += night_h

        sub  = sh["subsidiary"]
        role = sh["role"]
        hours_by_sub[sub]   = hours_by_sub.get(sub, 0.0)   + h
        hours_by_role[role] = hours_by_role.get(role, 0.0) + h

        cross_midnight = _parse_hhmm(sh["end_time"]) <= _parse_hhmm(sh["start_time"])

        rate_row = conn2.execute(
            "SELECT hourly_rate FROM AllowedRoles WHERE employee_id=? AND subsidiary=? AND role=?",
            (employee_id, sub, role),
        ).fetchone()
        hourly_rate = float(rate_row["hourly_rate"]) if rate_row else None
        if hourly_rate is not None:
            rates_used[(sub, role)] = hourly_rate

        shift_details.append({
            "shift_id":      sh["id"],
            "subsidiary":    sub,
            "role":          role,
            "start_time":    sh["start_time"],
            "end_time":      sh["end_time"],
            "hours":         round(h, 4),
            "hourly_rate":   hourly_rate,
            "cross_midnight": cross_midnight,
        })
    conn2.close()

    # Split-shift rule: sum first, THEN bucket
    total_hours = sum(s["hours"] for s in shift_details)

    # Night rule
    threshold = 7.0 if total_night_window >= 2.0 else 8.0

    # Overtime buckets
    h100 = min(total_hours, threshold)
    h125 = max(0.0, min(total_hours - threshold, 2.0))
    h150 = max(0.0, total_hours - threshold - 2.0)

    max_rate = max(rates_used.values()) if rates_used else 0.0
    salary   = h100 * max_rate + h125 * max_rate * 1.25 + h150 * max_rate * 1.5
    deficit  = max(0.0, emp["daily_standard"] - total_hours)

    return {
        "employee_id":         employee_id,
        "employee_name":       emp["name"],
        "date":                work_date,
        "daily_standard":      emp["daily_standard"],
        "shifts":              shift_details,
        "total_hours":         round(total_hours, 4),
        "night_hours_in_window": round(total_night_window, 4),
        "overtime_threshold":  threshold,
        "hours_100":           round(h100, 4),
        "hours_125":           round(h125, 4),
        "hours_150":           round(h150, 4),
        "max_rate":            max_rate,
        "salary_simulation":   round(salary, 2),
        "daily_deficit":       round(deficit, 4),
        "hours_by_subsidiary": {k: round(v, 4) for k, v in hours_by_sub.items()},
        "hours_by_role":       {k: round(v, 4) for k, v in hours_by_role.items()},
    }


def shift_hours_and_night(start_str: str, end_str: str):
    """Exported for unit tests: returns (total_hours, night_hours_in_window)."""
    total = _shift_hours(start_str, end_str)
    night = _night_overlap_hours(_parse_hhmm(start_str), _parse_hhmm(end_str))
    return (round(total, 4), round(night, 4))


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    init_db()
    seed_from_excel()
    src = "(from env EZTIME_API_TOKEN)" if os.environ.get("EZTIME_API_TOKEN") else "(default)"
    print(f"[AUTH] Token: {API_TOKEN!r} {src}")


# ---------------------------------------------------------------------------
# /v1 API Router
# ---------------------------------------------------------------------------

v1 = APIRouter(prefix="/v1")


@v1.get("/payroll/daily")
def v1_payroll_daily(
    request:           Request,
    employee_id:       Optional[str] = None,
    date:              Optional[str] = None,
    include_shifts:    bool = True,
    include_breakdown: bool = True,
    authorization:     Optional[str] = Header(default=None),
):
    """
    GET /v1/payroll/daily
    Auth:    Authorization: Bearer <token>
    Params:  employee_id (str, required), date (YYYY-MM-DD, required)
             include_shifts (bool, default true)
             include_breakdown (bool, default true)
    """
    # 1. Auth
    try:
        _check_token(authorization)
    except _TokenError:
        return _api_error(401, "UNAUTHORIZED", "Invalid or missing API token")

    # 2. Validate required params
    if not employee_id:
        return _api_error(400, "VALIDATION_ERROR", "Missing required parameter: employee_id")
    if not date:
        return _api_error(400, "VALIDATION_ERROR", "Missing required parameter: date")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return _api_error(400, "VALIDATION_ERROR", "Parameter 'date' must be in YYYY-MM-DD format")

    # 3. Employee existence
    conn = get_conn()
    emp_row = conn.execute("SELECT id FROM Employees WHERE id=?", (employee_id,)).fetchone()
    conn.close()
    if not emp_row:
        return _api_error(404, "EMPLOYEE_NOT_FOUND", "Employee not found")

    # 4. Compute
    result = compute_daily(employee_id, date)

    if not result["shifts"]:
        return _api_error(404, "NO_SHIFTS_FOR_DATE",
                          "No shifts found for this employee on the requested date")

    # 5. Build response (field names match spec exactly)
    resp: dict = {
        "employee_id":           result["employee_id"],
        "employee_name":         result["employee_name"],
        "date":                  result["date"],

        "overtime_threshold":    result["overtime_threshold"],
        "night_hours_in_window": result["night_hours_in_window"],
        "night_rule_active":     result["night_hours_in_window"] >= 2.0,

        "total_hours": result["total_hours"],
        "hours_100":   result["hours_100"],
        "hours_125":   result["hours_125"],
        "hours_150":   result["hours_150"],

        "daily_standard": result["daily_standard"],
        "daily_deficit":  result["daily_deficit"],

        "max_rate":          result["max_rate"],
        "salary_simulation": result["salary_simulation"],

        "calculated_at": _now_jerusalem(),
    }

    if include_breakdown:
        resp["hours_by_subsidiary"] = result["hours_by_subsidiary"]
        resp["hours_by_role"]       = result["hours_by_role"]

    if include_shifts:
        resp["shifts"] = result["shifts"]

    return JSONResponse(status_code=200, content=resp)


app.include_router(v1)

# ---------------------------------------------------------------------------
# Existing endpoints (unchanged)
# ---------------------------------------------------------------------------

@app.get("/employees")
def list_employees():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, daily_standard FROM Employees ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/allowed/{employee_id}")
def get_allowed(employee_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, subsidiary, hourly_rate FROM AllowedRoles WHERE employee_id=? ORDER BY subsidiary, role",
        (employee_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

class ShiftIn(BaseModel):
    employee_id: str
    date: str
    subsidiary: str
    role: str
    start_time: str
    end_time: str

@app.post("/shifts")
def add_shift(shift: ShiftIn):
    try:
        s = _parse_hhmm(shift.start_time)
        e = _parse_hhmm(shift.end_time)
    except Exception:
        raise HTTPException(400, "Invalid time format. Use HH:MM")

    if e == s:
        raise HTTPException(400, "End time equals start time – shift has zero duration.")

    conn = get_conn()
    emp = conn.execute("SELECT id FROM Employees WHERE id=?", (shift.employee_id,)).fetchone()
    if not emp:
        conn.close()
        raise HTTPException(404, f"Employee {shift.employee_id} not found")

    allowed = conn.execute(
        "SELECT 1 FROM AllowedRoles WHERE employee_id=? AND subsidiary=? AND role=?",
        (shift.employee_id, shift.subsidiary, shift.role)
    ).fetchone()
    if not allowed:
        conn.close()
        raise HTTPException(400, f"Combination subsidiary='{shift.subsidiary}' / role='{shift.role}' not allowed for this employee.")

    existing = conn.execute(
        "SELECT start_time, end_time FROM RawShifts WHERE employee_id=? AND date=?",
        (shift.employee_id, shift.date)
    ).fetchall()

    warning = None
    s_end = e if e > s else e + 24
    for ex in existing:
        es = _parse_hhmm(ex["start_time"])
        ee = _parse_hhmm(ex["end_time"])
        if ee <= es:
            ee += 24
        if not (s_end <= es or s >= ee):
            warning = f"Warning: shift overlaps with existing shift {ex['start_time']}–{ex['end_time']}"
            break

    conn.execute(
        "INSERT INTO RawShifts(employee_id,date,subsidiary,role,start_time,end_time) VALUES(?,?,?,?,?,?)",
        (shift.employee_id, shift.date, shift.subsidiary, shift.role, shift.start_time, shift.end_time)
    )
    conn.commit()
    conn.close()

    result = {"status": "ok", "message": "Shift added."}
    if warning:
        result["warning"] = warning
    return result

@app.delete("/shifts/{shift_id}")
def delete_shift(shift_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM RawShifts WHERE id=?", (shift_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/shifts_list/{employee_id}/{work_date}")
def list_shifts(employee_id: str, work_date: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, subsidiary, role, start_time, end_time FROM RawShifts WHERE employee_id=? AND date=? ORDER BY start_time",
        (employee_id, work_date)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        h = _shift_hours(r["start_time"], r["end_time"])
        result.append({**dict(r), "hours": round(h, 4)})
    return result

@app.get("/daily/{employee_id}/{work_date}")
def daily_result(employee_id: str, work_date: str):
    try:
        result = compute_daily(employee_id, work_date)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result

@app.get("/", response_class=HTMLResponse)
def ui_home(request: Request):
    conn = get_conn()
    employees = conn.execute("SELECT id, name FROM Employees ORDER BY name").fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "employees": employees})
