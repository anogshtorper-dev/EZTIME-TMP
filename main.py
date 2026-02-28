from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json

# יצירת האובייקט FastAPI
app = FastAPI()

# הגדרת תבניות HTML
templates = Jinja2Templates(directory="templates")

# מודל למידע של משמרת
class Shift(BaseModel):
    employee_id: str
    subsidiary: str
    role: str
    date: str
    start_time: str
    end_time: str

# API לקבלת כל העובדים
@app.get("/employees")
def get_employees():
    # לדוגמה, נחזיר רשימת עובדים
    return [{"employee_id": "E1001", "name": "Dana Alon"}, {"employee_id": "E1002", "name": "Amir Adri"}]

# API להוספת משמרת חדשה
@app.post("/shifts")
async def add_shift(shift: Shift):
    # כאן תשמור את המשמרת ב־DB שלך
    # לדוגמה, נבצע הדפסה לקונסול
    print(f"Shift added: {shift}")
    return {"message": "Shift added successfully!"}

# API לקבלת שכר יומי לעובד מסוים
@app.get("/v1/payroll/daily")
async def get_daily_payroll(employee_id: str, date: str):
    # מדמה החזרת נתונים חישוביים
    payroll_data = {
        "employee_id": employee_id,
        "date": date,
        "total_hours": 8.75,
        "hours_100": 8.0,
        "hours_125": 0.75,
        "hours_150": 0.0,
        "salary_simulation": 554.13,
        "max_rate": 62.0
    }
    return payroll_data

# API להצגת הדף הראשי (UI)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
