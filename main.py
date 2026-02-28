from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json

app = FastAPI()

templates = Jinja2Templates(directory="templates")

class Shift(BaseModel):
    employee_id: str
    subsidiary: str
    role: str
    employee_name: str
    scan_time: str
    clock_in_out: str
    start_time: str
    end_time: str

@app.post("/shifts")
async def add_shift(shift: Shift):
    # כאן נשמור את המשמרת ב־DB שלך
    # לדוגמה, נבצע הדפסה לקונסול
    print(f"Shift added: {shift}")
    return {"message": "Shift added successfully!"}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
