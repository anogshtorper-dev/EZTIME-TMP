from fastapi import FastAPI, HTTPException, Request, Body
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import json

app = FastAPI()

# ===========================
# Dummy Data (Simulate DB)
# ===========================

# Allowed Roles Mapping (This is a simplified example, you may want to load this from a DB)
allowed_roles = {
    "Subsidiary A": ["Security", "Warehouse"],
    "Subsidiary B": ["Manager", "Warehouse"]
}

# Mock employee data (should be replaced with real DB queries)
employees = {
    "E1001": {"full_name": "Dana Alon", "status": "active", "allowed_roles": ["Security", "Warehouse"]},
    "E1002": {"full_name": "Amit Edri", "status": "active", "allowed_roles": ["Security"]}
}

# ===========================
# Data Models (Request/Response)
# ===========================

class EventPayload(BaseModel):
    employee_id: str
    subsidiary_id: str
    role_id: str
    event_type: str  # IN / OUT
    timestamp_utc: datetime
    proof_type: str  # GPS / GEOFENCE / QR / NFC / MANUAL
    device_id: str
    attestation_status: str
    manual_reason: str = None

class ScanPayload(BaseModel):
    employee_id: str
    scanned_payload: str  # Payload coming from the QR/NFC Scan

# ===========================
# Functions for Event Processing
# ===========================

def resolve_scan_payload(scanned_payload: str) -> Dict[str, str]:
    """
    This function parses the scan payload (QR or NFC) and returns subsidiary and role.
    It supports JSON, KV pair, and CSV-like formats.
    """
    # Attempt to parse the payload
    scanned_payload = scanned_payload.strip()
    
    # Try JSON format
    if scanned_payload.startswith("{") and scanned_payload.endswith("}"):
        try:
            parsed_json = json.loads(scanned_payload)
            subsidiary = parsed_json.get("subsidiary", "").strip()
            role = parsed_json.get("role", "").strip()
            if subsidiary and role:
                return {"subsidiary": subsidiary, "role": role}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Try key-value pair format (subsidiary=SubsidiaryA;role=Security)
    if "=" in scanned_payload:
        try:
            kv_pairs = dict(item.split("=") for item in scanned_payload.split(";"))
            subsidiary = kv_pairs.get("subsidiary", "").strip()
            role = kv_pairs.get("role", "").strip()
            if subsidiary and role:
                return {"subsidiary": subsidiary, "role": role}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key-value pair payload")
    
    # Try CSV-like format: SubsidiaryA,Security
    if "," in scanned_payload:
        parts = scanned_payload.split(",")
        if len(parts) == 2:
            subsidiary, role = parts
            return {"subsidiary": subsidiary.strip(), "role": role.strip()}
    
    raise HTTPException(status_code=400, detail="Unsupported scan payload format")

def validate_event_data(event: EventPayload) -> bool:
    """
    This function checks if the scanned subsidiary and role match the allowed roles for the employee.
    """
    if event.subsidiary_id not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid subsidiary: {event.subsidiary_id}")
    
    if event.role_id not in allowed_roles[event.subsidiary_id]:
        raise HTTPException(status_code=400, detail=f"Invalid role: {event.role_id} for subsidiary {event.subsidiary_id}")
    
    return True

# ===========================
# API Endpoints
# ===========================

@app.post("/scan/resolve")
async def resolve_scan(payload: ScanPayload):
    """
    This endpoint resolves the scan payload and maps it to the valid subsidiary and role.
    """
    try:
        # Resolve the scanned payload into subsidiary and role
        scan_result = resolve_scan_payload(payload.scanned_payload)
        
        # Check if the employee exists
        if payload.employee_id not in employees:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Check if the employee is allowed to have this role
        employee = employees[payload.employee_id]
        if scan_result["role"] not in employee["allowed_roles"]:
            raise HTTPException(status_code=400, detail="Employee not allowed to have this role")
        
        return {"subsidiary": scan_result["subsidiary"], "role": scan_result["role"], "status": "success"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/events/scan")
async def create_event_from_scan(event: EventPayload):
    """
    This endpoint receives an event with scanned data (QR/NFC) and stores it in the database.
    """
    # First, validate the scanned event data
    validate_event_data(event)
    
    # In a real system, you would store this event in your database
    # For demonstration, we simply return a success message
    return {"message": "Event created successfully", "event": event.dict()}

@app.post("/shifts")
async def create_shift(event: EventPayload):
    """
    This endpoint is used to create a shift record for an employee.
    """
    # Validate event data
    validate_event_data(event)
    
    # In a real system, you would store the shift data in your database
    # For demonstration, we simply return the shift data
    return {"message": "Shift created successfully", "shift": event.dict()}

@app.get("/employees")
async def get_employees():
    """
    This endpoint returns a list of employees for validation or selection.
    """
    return [{"employee_id": emp_id, "full_name": emp["full_name"], "status": emp["status"]} for emp_id, emp in employees.items()]

@app.get("/allowed/{employee_id}")
async def get_allowed_roles(employee_id: str):
    """
    This endpoint returns the roles allowed for a specific employee.
    """
    if employee_id not in employees:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee = employees[employee_id]
    return [{"role": role} for role in employee["allowed_roles"]]

@app.get("/v1/payroll/daily")
async def get_daily_payroll(employee_id: str, date: str):
    """
    This endpoint returns the payroll data for a specific employee and date.
    """
    if employee_id not in employees:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # For the sake of this example, we simulate payroll calculation
    return {
        "employee_id": employee_id,
        "date": date,
        "total_hours": 8.0,
        "hours_100": 8.0,
        "hours_125": 0.0,
        "hours_150": 0.0,
        "salary_simulation": 1000.0,
        "max_rate": 125.0,
        "daily_standard": 8.0,
        "daily_deficit": 0.0
    }

@app.delete("/shifts/{shift_id}")
async def delete_shift(shift_id: int):
    """
    This endpoint deletes a shift record.
    """
    # In a real system, you would delete the shift from the database
    return {"message": f"Shift {shift_id} deleted successfully"}
