# 🕐 EZTIME-TMP – Time & Attendance Payroll Management System

A modern, fast, and user-friendly time tracking and payroll calculation system with a beautiful web interface and comprehensive REST API.

---

## 📑 Table of Contents

1. [✨ Key Features](#key-features)
2. [🚀 Quick Start](#quick-start)
3. [📂 Project Structure](#project-structure)
4. [⚙️ Installation Guide](#installation-guide)
5. [🌐 Using the System](#using-the-system)
6. [📡 API Endpoints](#api-endpoints)
7. [🔐 Security & Authentication](#security--authentication)
8. [💼 Business Rules](#business-rules)
9. [🧪 Testing & Quality](#testing--quality)
10. [📝 Postman Examples](#postman-examples)
11. [🚀 Production Deployment](#production-deployment)
12. [🛠️ Development Setup](#development-setup)
13. [🤝 Contributing Guidelines](#contributing-guidelines)
14. [🐛 Troubleshooting](#troubleshooting)

---

## ✨ Key Features

### 🎯 Leading System Features

#### 1. 📱 Smart User Interface
- ✅ Autocomplete employee selection
- ✅ Responsive design for mobile/tablet
- ✅ Real-time visual feedback (success/error messages)
- ✅ Modern, clean design (Material Design principles)

#### 2. 💰 Automatic Payroll Calculation
- ✅ Instant salary calculation based on shifts
- ✅ Support for overtime with multiplier rates (100%, 125%, 150%)
- ✅ Automatic night shift detection (22:00-06:00)
- ✅ Daily deficit calculation

#### 3. 🌙 Advanced Business Rules
- ✅ Max Rate Rule - uses highest rate for entire day
- ✅ Midnight Crossing - correctly handles shifts past midnight
- ✅ Accurate night hours calculation
- ✅ Support for multiple shifts per day

#### 4. 📊 Deep Data Analytics
- ✅ Hours breakdown by subsidiary
- ✅ Hours breakdown by role
- ✅ Detailed daily shift report
- ✅ Shift deletion with automatic recalculation

#### 5. 🔌 Professional REST API
- ✅ Bearer Token authentication
- ✅ Multiple data retrieval endpoints
- ✅ Optional parameters support
- ✅ Standard HTTP status codes

#### 6. 🗄️ Database Management
- ✅ Automatic database creation on first run
- ✅ Automatic Excel data import
- ✅ Real-time data updates
- ✅ Support for UTF-8 and special characters

#### 7. 🔒 Security & Compliance
- ✅ Bearer Token authentication
- ✅ CORS support for external services
- ✅ Input validation on all endpoints
- ✅ Precise timezone (Asia/Jerusalem)

---

## 🚀 Quick Start

### Get Running in 60 Seconds

```bash
# 1. Create Virtual Environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Start Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Open Browser
http://localhost:8000
```

**System is now running!** ✅

---

## 📂 Project Structure

```
EZTIME-TMP/
│
├── 📄 main.py                      ← FastAPI Server + Business Logic
├── 📄 requirements.txt             ← Python Dependencies
├── 📊 EZTIME_DATA.xlsx            ← Your Data File (required)
├── 🗄️ eztime.db                   ← SQLite Database (auto-created)
├── 🧪 test_payroll.py             ← Unit Tests
├── 📄 README.md                   ← This Documentation
│
└── 📁 templates/
    └── 🌐 index.html              ← Web User Interface
```

### Important Files Explanation

| File | Description |
|------|-------------|
| `main.py` | All business logic, API routes, database operations |
| `requirements.txt` | List of all required Python libraries |
| `EZTIME_DATA.xlsx` | Your data file (employees, rates, shifts) |
| `eztime.db` | Database file (created automatically on first run) |
| `templates/index.html` | Web user interface |

---

## ⚙️ Installation Guide

### Prerequisites

- ✅ **Python 3.9+** - Check: `python --version`
- ✅ **pip** - Package manager (usually comes with Python)
- ✅ **Excel File** - `EZTIME_DATA.xlsx` with your data
- ✅ **Git** (optional) - For cloning the repository

### Step 1️⃣ - Clone Repository

```bash
git clone https://github.com/anogshtorper-dev/EZTIME-TMP.git
cd EZTIME-TMP
```

### Step 2️⃣ - Create Virtual Environment

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Success indicator:**
```
(venv) user@computer:~/EZTIME-TMP$
```

### Step 3️⃣ - Install Dependencies

```bash
pip install -r requirements.txt
```

**Installation time:** ~30-60 seconds

**Libraries installed:**
- 📦 fastapi==0.111.0
- 📦 uvicorn[standard]==0.29.0
- 📦 jinja2==3.1.4
- 📦 pandas==2.2.2
- 📦 openpyxl==3.1.2
- 📦 pydantic==2.7.1
- 📦 python-multipart==0.0.9
- 📦 tzdata==2024.1

### Step 4️⃣ - Prepare Data File

```bash
# Copy EZTIME_DATA.xlsx to project root
cp /path/to/EZTIME_DATA.xlsx ./EZTIME_DATA.xlsx
```

**Excel file must contain three sheets:**

#### Sheet 1 - Employees
```
employee_id  | name        | daily_standard
E1022        | John Doe    | 8.0
E1023        | Jane Smith  | 8.5
```

#### Sheet 2 - Rates & Roles
```
employee_id | role              | subsidiary    | hourly_rate
E1022       | Warehouse Manager | Subsidiary A  | 62.0
E1022       | Picker            | Subsidiary B  | 50.0
E1023       | Manager           | Subsidiary A  | 75.0
```

#### Sheet 3 - Shifts
```
employee_id | date       | start_time | end_time | subsidiary   | role
E1022       | 2026-01-19 | 07:45      | 16:30    | Subsidiary A | Warehouse Manager
E1023       | 2026-01-19 | 08:00      | 17:00    | Subsidiary A | Manager
```

### Step 5️⃣ - Start Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
[SEED] Sheet names: ['Employees', 'Rates', 'Shifts']
[SEED] DB already seeded – skipping.
[AUTH] Token: 'demo-token' (default)
```

### Step 6️⃣ - Open in Browser

```
http://localhost:8000
```

**Congratulations!** System is ready to use! ✅

---

## 🌐 Using the System

### Complete User Guide

#### 1. Select Employee
```
1. Type employee name in the "Employee" field
2. Select from the displayed list
3. Or use "📱 Scan QR" to scan QR code
```

#### 2. Pick Date
```
1. Click on "Date" field
2. Select date from calendar widget
3. Or type manually in format: YYYY-MM-DD
```

#### 3. Choose Subsidiary & Role
```
1. Select Subsidiary from dropdown (auto-filtered by employee)
2. Select Role from dropdown (auto-filtered by subsidiary)
3. Fields update automatically
```

#### 4. Add Work Hours
```
1. Enter Start Time in HH:MM format (e.g., 07:45)
2. Enter End Time in HH:MM format (e.g., 16:30)
3. Click "+ Add Shift"
```

#### 5. Calculate Payroll
```
1. Click "⟳ Calculate"
2. System automatically calculates all data
3. View detailed report in "Daily Payroll Result" panel
```

#### 6. Edit & Delete
```
1. See shift in table? Click ✕ to delete
2. System automatically recalculates
```

### Payroll Results Report

When clicking "Calculate", you get a detailed report including:

```
📊 Daily Payroll Result

👤 Employee: John Doe | 2026-01-19

💰 Salary Simulation: ₪554.13
   (Calculated salary based on rate and work type)

📋 Statistics:
   • Total Hours: 8.75 hours
   • Hours @100%: 8.0 hours (regular salary)
   • Hours @125%: 0.75 hours (overtime 1st tier)
   • Hours @150%: 0.0 hours (overtime 2nd tier)

🌙 Night Rule Active: NO
   • Night Hours in Window: 0.0 hours

⚠️ Daily Deficit: 0.25 hours
   (Missing 0.25 hours from daily standard of 9.0)

🔧 Overtime Threshold: 8 hours
💵 Max Rate: ₪62.0 per hour

📦 Hours by Subsidiary:
   • Subsidiary A: 8.75 hours

👔 Hours by Role:
   • Warehouse Manager: 8.75 hours

📋 Shifts Table:
   [1] Warehouse Manager @ Subsidiary A
       07:45 → 16:30 (8.75h) | ₪62.0/h
```

---

## 📡 API Endpoints

### 🌍 UI Endpoints (No Authentication)

#### 1. List All Employees
```http
GET /employees
```

**Response:**
```json
[
  {"id": "E1022", "name": "John Doe", "daily_standard": 8.0},
  {"id": "E1023", "name": "Jane Smith", "daily_standard": 8.5}
]
```

#### 2. Get Available Roles for Employee
```http
GET /allowed/{employee_id}
```

**Example:**
```http
GET /allowed/E1022
```

**Response:**
```json
[
  {"role": "Warehouse Manager", "subsidiary": "Subsidiary A", "hourly_rate": 62.0},
  {"role": "Picker", "subsidiary": "Subsidiary B", "hourly_rate": 50.0}
]
```

#### 3. Add Shift
```http
POST /shifts

Content-Type: application/json

{
  "employee_id": "E1022",
  "date": "2026-01-19",
  "subsidiary": "Subsidiary A",
  "role": "Warehouse Manager",
  "start_time": "07:45",
  "end_time": "16:30"
}
```

**Response:**
```json
{"status": "ok", "message": "Shift added."}
```

#### 4. Calculate Daily Payroll
```http
GET /daily/{employee_id}/{date}
```

**Example:**
```http
GET /daily/E1022/2026-01-19
```

**Response:**
```json
{
  "employee_id": "E1022",
  "employee_name": "John Doe",
  "date": "2026-01-19",
  "total_hours": 8.75,
  "hours_100": 8.0,
  "hours_125": 0.75,
  "hours_150": 0.0,
  "salary_simulation": 554.13,
  "max_rate": 62.0,
  "overtime_threshold": 8,
  "night_hours_in_window": 0.0,
  "daily_deficit": 0.25
}
```

#### 5. List Shifts for Date
```http
GET /shifts_list/{employee_id}/{date}
```

**Example:**
```http
GET /shifts_list/E1022/2026-01-19
```

#### 6. Delete Shift
```http
DELETE /shifts/{shift_id}
```

**Example:**
```http
DELETE /shifts/1
```

### 🔒 v1 API (Requires Bearer Token)

#### Calculate Payroll via API
```http
GET /v1/payroll/daily?employee_id=E1022&date=2026-01-19
Authorization: Bearer demo-token
```

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| employee_id | string | ✅ | — | Employee ID |
| date | string | ✅ | — | Date (YYYY-MM-DD) |
| include_shifts | boolean | ❌ | true | Include shift details |
| include_breakdown | boolean | ❌ | true | Include hours breakdown |

---

## 🔐 Security & Authentication

### Default Token

```
demo-token
```

### Change API Token

**Using Environment Variable:**

```bash
export EZTIME_API_TOKEN=my-secret-token
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Windows (PowerShell):**
```powershell
$env:EZTIME_API_TOKEN="my-secret-token"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Token Security

| ⚠️ Warning | Action |
|-----------|--------|
| **Don't use default in production** | Change to strong, random token |
| **Don't put token in code** | Use environment variables only |
| **Don't share token in files** | Keep it secret and secure |

### API Request with Token

```bash
curl -H "Authorization: Bearer your-secret-token" \
  "http://localhost:8000/v1/payroll/daily?employee_id=E1022&date=2026-01-19"
```

---

## 💼 Business Rules

### Payroll Calculation - Detailed Explanation

#### 1. Threshold Determination

```
IF night_hours_in_window >= 2.0
  THEN threshold = 7 hours
ELSE
  threshold = 8 hours
```

**Example:**
- Employee worked 2.5 night hours → threshold = 7 hours
- Employee worked 1 night hour → threshold = 8 hours

#### 2. Hours Distribution

```
hours_100% = MIN(total_hours, threshold)
hours_125% = MAX(0, MIN(total_hours - threshold, 2.0))
hours_150% = MAX(0, total_hours - threshold - 2.0)
```

**Example with 10 total hours:**
```
threshold = 8
hours_100% = MIN(10, 8) = 8 hours
hours_125% = MIN(10-8, 2) = 2 hours
hours_150% = 10-8-2 = 0 hours
```

#### 3. Salary Calculation

```
salary = (hours_100 × rate) + (hours_125 × rate × 1.25) + (hours_150 × rate × 1.5)
```

**Example with ₪50/hour:**
```
salary = (8 × 50) + (2 × 50 × 1.25) + (0 × 50 × 1.5)
salary = 400 + 125 + 0
salary = ₪525
```

#### 4. Daily Deficit

```
deficit = MAX(0, daily_standard - total_hours)
```

**Example:**
- daily_standard = 9 hours
- total_hours = 8.75 hours
- deficit = MAX(0, 9 - 8.75) = 0.25 hours

### Night Work (Night Window)

**Night Window:** 22:00 → 06:00

**Night Hours Calculation:**
- Each hour within this window counts as "night hour"
- If ≥2 night hours → threshold becomes 7 hours

**Examples:**
```
Shift 20:00-23:00
├─ Night hours: 1 hour (23:00-24:00)
└─ Threshold: 8 hours

Shift 22:00-06:00
├─ Night hours: 8 hours (entire shift)
└─ Threshold: 7 hours

Shift 04:00-08:00
├─ Night hours: 2 hours (04:00-06:00)
└─ Threshold: 7 hours
```

### Max Rate Rule

**Rule:** If employee worked with different rates on same day - use highest rate

**Example:**
```
Shift 1: 8 hours @ Subsidiary A @ ₪50/hour
Shift 2: 2 hours @ Subsidiary B @ ₪75/hour

Max Rate = ₪75 (highest)
Salary = (8+2) × ₪75 × [rates] = ...
```

---

## 🧪 Testing & Quality

### Run Unit Tests

```bash
# Basic test
python test_payroll.py

# Verbose test with pytest
python -m pytest test_payroll.py -v

# With coverage report
python -m pytest test_payroll.py --cov=main
```

### What's Tested

- ✅ Overtime bucket calculations (3 scenarios)
- ✅ Night window detection
- ✅ Early morning shifts (04:00-08:00)
- ✅ Midnight crossing logic (23:00-03:00)
- ✅ Bearer token validation
- ✅ Timezone handling (Asia/Jerusalem)
- ✅ Missing parameter validation

### Example Test

```python
import unittest
from main import compute_daily

class TestPayroll(unittest.TestCase):
    def test_simple_shift(self):
        result = compute_daily("E1022", "2026-01-19")
        self.assertEqual(result["total_hours"], 8.75)
        self.assertEqual(result["hours_100"], 8.0)
        
if __name__ == '__main__':
    unittest.main()
```

---

## 📝 Postman Examples

### ✅ Example 1 - Successful Request (200 OK)

**Setup:**
```
Method:  GET
URL:     http://localhost:8000/v1/payroll/daily
         ?employee_id=E1022&date=2026-01-19
Headers: Authorization: Bearer demo-token
```

**Steps in Postman:**
1. Open Postman
2. Click "New Request"
3. Select "GET"
4. Paste the URL
5. Go to "Headers" tab
6. Add: `Authorization: Bearer demo-token`
7. Click "Send"

**Response:**
```json
{
  "employee_id": "E1022",
  "employee_name": "John Doe",
  "date": "2026-01-19",
  "total_hours": 8.75,
  "hours_100": 8.0,
  "hours_125": 0.75,
  "hours_150": 0.0,
  "salary_simulation": 554.13,
  "max_rate": 62.0,
  "overtime_threshold": 8,
  "night_hours_in_window": 0.0,
  "night_rule_active": false,
  "daily_standard": 9.0,
  "daily_deficit": 0.25,
  "calculated_at": "2026-01-19T10:00:00+02:00"
}
```

### ❌ Example 2 - Invalid Token (401)

```
Headers: Authorization: Bearer wrong-token
```

**Response:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API token"
  }
}
```

### ❌ Example 3 - Employee Not Found (404)

```
URL: /v1/payroll/daily?employee_id=NOTEXIST&date=2026-01-19
```

**Response:**
```json
{
  "error": {
    "code": "EMPLOYEE_NOT_FOUND",
    "message": "Employee not found"
  }
}
```

### ❌ Example 4 - Missing Parameter (400)

```
URL: /v1/payroll/daily?employee_id=E1022
```

**Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required parameter: date"
  }
}
```

---

## 🚀 Production Deployment

### 1. Production Environment Setup

```bash
# SSH to your server
ssh user@production-server.com

# Create directory
mkdir -p /opt/eztime
cd /opt/eztime

# Clone repository
git clone https://github.com/anogshtorper-dev/EZTIME-TMP.git .
```

### 2. Environment Configuration

```bash
# Create .env file
nano .env
```

**Add:**
```
EZTIME_EXCEL=/opt/eztime/EZTIME_DATA.xlsx
EZTIME_DB=/opt/eztime/data/eztime.db
EZTIME_API_TOKEN=your-secret-production-token-12345
```

### 3. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Setup Gunicorn (Production Server)

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### 5. Configure Nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/eztime
server {
    listen 80;
    server_name eztime.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d eztime.example.com

# Update Nginx
sudo certbot --nginx -d eztime.example.com
```

### 7. Create Systemd Service (Auto-start)

```bash
# Create service file
sudo nano /etc/systemd/system/eztime.service
```

**Add:**
```ini
[Unit]
Description=EZTIME Payroll Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/eztime
Environment="EZTIME_API_TOKEN=your-secret-token"
ExecStart=/opt/eztime/venv/bin/gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable & Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable eztime
sudo systemctl start eztime
sudo systemctl status eztime
```

### 8. Automatic Backup

```bash
# Create backup script
nano /opt/eztime/backup.sh
```

**Add:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/eztime/backups"
DB_FILE="/opt/eztime/data/eztime.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/eztime_$DATE.db
gzip $BACKUP_DIR/eztime_$DATE.db

# Keep only 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
```

**Add to Crontab:**
```bash
crontab -e
# Add:
0 2 * * * /opt/eztime/backup.sh
```

---

## 🛠️ Development Setup

### 1. Local Development Environment

```bash
# Create project directory
mkdir eztime-dev
cd eztime-dev

# Clone repository
git clone https://github.com/anogshtorper-dev/EZTIME-TMP.git
cd EZTIME-TMP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install with dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### 2. Start Server with Hot Reload

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Every file change → Server restarts automatically**

### 3. Code Style & Formatting

```bash
# Format code
black main.py templates/ tests/

# Check style
flake8 main.py

# Type checking
mypy main.py
```

### 4. Debug Mode

```bash
# Debug with logging
LOGLEVEL=debug uvicorn main:app --reload

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("My debug message")
```

### 5. SQLite Browser

```bash
# Install DB Browser
pip install db-browser

# Or use GUI
# https://sqlitebrowser.org/

# Or command line
sqlite3 eztime.db
sqlite> .tables
sqlite> SELECT * FROM Employees;
```

---

## 🤝 Contributing Guidelines

### How to Contribute to the Project

#### Step 1: Fork the Repository

1. Go to: https://github.com/anogshtorper-dev/EZTIME-TMP
2. Click "Fork" button (top-right)
3. Select your account

#### Step 2: Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/EZTIME-TMP.git
cd EZTIME-TMP
git remote add upstream https://github.com/anogshtorper-dev/EZTIME-TMP.git
```

#### Step 3: Create New Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bug-fix
# or
git checkout -b docs/your-doc-update
```

**Naming Convention:**
- `feature/` - for new features
- `bugfix/` - for bug fixes
- `docs/` - for documentation
- `refactor/` - for code improvements

#### Step 4: Make Your Changes

```bash
# Edit files
nano main.py

# Check changes
git status

# Add changes
git add main.py

# Commit with clear message
git commit -m "Add feature: automatic shift validation"
```

**Commit Message Rules:**
```
✨ Add: description of what you added
🐛 Fix: description of what you fixed
📚 Docs: documentation update
🔧 Refactor: code improvement
⚡ Performance: performance improvement
```

#### Step 5: Push Branch

```bash
git push origin feature/your-feature-name
```

#### Step 6: Create Pull Request

1. Go to your repository on GitHub
2. See "Compare & pull request"
3. Click it
4. Fill in details

**PR Content Should Include:**
- ✅ Clear description of change
- ✅ Why this change is needed
- ✅ How you tested the code
- ✅ Example screenshots if relevant

**Example PR Description:**
```markdown
## Description
Adds automatic validation of shift hours to prevent errors.

## Why This Matters
- Prevents data entry errors
- Saves manual validation time
- Improves data quality

## How I Tested
- Tested with regular shifts ✅
- Tested with night shifts ✅
- Tested with midnight-crossing shifts ✅

## Screenshots
[Add screenshots if relevant]
```

### Code Quality Standards

#### 1. Clear Structure

```python
# ❌ Bad
def calc(eid,d):
    c=get_conn()
    r=c.execute("SELECT * FROM RawShifts WHERE employee_id=? AND date=?",
    (eid,d)).fetchall()
    return r

# ✅ Good
def get_shifts_for_employee_and_date(employee_id: str, work_date: str) -> list:
    """Get all shifts for a specific employee on a specific date."""
    conn = get_conn()
    shifts = conn.execute(
        "SELECT * FROM RawShifts WHERE employee_id=? AND date=? ORDER BY start_time",
        (employee_id, work_date)
    ).fetchall()
    return shifts
```

#### 2. Type Hints

```python
# ❌ Bad
def compute_salary(hours, rate):
    return hours * rate

# ✅ Good
def compute_salary(hours: float, rate: float) -> float:
    """Calculate salary based on hours and hourly rate."""
    return hours * rate
```

#### 3. Documentation

```python
# ✅ Good
def _night_overlap_hours(start_h: float, end_h: float) -> float:
    """
    Count overlap of shift with 22:00–06:00 night window.
    
    Uses 0–48h minute axis. Night window split into segments:
      [00:00, 06:00] → same-day early morning
      [22:00, 24:00] → evening
      [24:00, 30:00] → next-day (midnight-crossing)
    
    Args:
        start_h: Start hour in decimal (e.g., 7.75 = 07:45)
        end_h: End hour in decimal (e.g., 16.5 = 16:30)
    
    Returns:
        Overlap hours as float (e.g., 2.5)
    """
    # Implementation...
```

#### 4. Error Handling

```python
# ❌ Bad
def get_employee(emp_id):
    return db.query(f"SELECT * FROM Employees WHERE id={emp_id}")

# ✅ Good
def get_employee(emp_id: str) -> dict:
    """Get employee by ID, raising exception if not found."""
    try:
        conn = get_conn()
        emp = conn.execute(
            "SELECT * FROM Employees WHERE id=?",
            (emp_id,)
        ).fetchone()
        
        if not emp:
            raise ValueError(f"Employee {emp_id} not found")
            
        return dict(emp)
    except Exception as e:
        logger.error(f"Error fetching employee: {e}")
        raise
```

### Review Process

When submitting a PR:

1. **Automated Checks** (automatic):
   - ✅ Code style (flake8, black)
   - ✅ Type hints (mypy)
   - ✅ Unit tests
   - ✅ Coverage

2. **Manual Review** (by maintainers):
   - ✅ Logic correctness
   - ✅ Performance impact
   - ✅ Documentation
   - ✅ Backwards compatibility

3. **Approval & Merge**:
   - At least 1 approval required
   - All checks must pass
   - Code is merged to main

### Reporting Bugs

If you find a bug:

1. **Open Issue**: https://github.com/anogshtorper-dev/EZTIME-TMP/issues
2. **Use Clear Title**: "Bug: XYZ not working"
3. **Provide Reproduction Steps**:
   ```
   Steps to reproduce:
   1. ...
   2. ...
   3. ...
   
   Expected: ...
   Actual: ...
   ```
4. **Include Environment**:
   ```
   OS: macOS/Windows/Linux
   Python: 3.9.x
   EZTIME Version: 1.0
   ```

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 🔴 Port 8000 Already in Use

```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux

# Or
netstat -ano | findstr :8000  # Windows

# Solution: use different port
uvicorn main:app --port 8001
```

#### 🔴 `requirements.txt` Not Found

```bash
# Create the file
cat > requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn[standard]==0.29.0
jinja2==3.1.4
pandas==2.2.2
openpyxl==3.1.2
pydantic==2.7.1
python-multipart==0.0.9
tzdata==2024.1
EOF
```

#### 🔴 Excel File Not Found

```bash
# Verify file exists
ls -la EZTIME_DATA.xlsx  # macOS/Linux

# Or
dir EZTIME_DATA.xlsx  # Windows

# If missing, copy it
cp /path/to/EZTIME_DATA.xlsx ./
```

#### 🔴 Database Already Seeded

```bash
# Delete the database
rm eztime.db  # macOS/Linux
del eztime.db  # Windows

# Restart server - it will recreate automatically
uvicorn main:app --reload
```

#### 🔴 No Employees Showing

**Check:**
1. Excel file has Employees sheet?
2. Correct columns? (employee_id, name, daily_standard)
3. Data format accepted?

**Fix:**
```bash
# Check database
sqlite3 eztime.db
sqlite> SELECT COUNT(*) FROM Employees;
```

#### 🔴 Token Not Working

```bash
# Test your token
curl -H "Authorization: Bearer demo-token" \
  http://localhost:8000/v1/payroll/daily?employee_id=E1022&date=2026-01-19

# Or change token
export EZTIME_API_TOKEN=my-new-token
uvicorn main:app --reload
```

#### 🔴 Timezone Not Correct

```bash
# Check timezone
python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('Asia/Jerusalem')))"

# If not working, install tzdata
pip install tzdata
```

### Debug Mode

```bash
# Run with debug logging
LOGLEVEL=debug uvicorn main:app --reload

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

---

## 🔧 Environment Variables Complete Reference

```bash
# Database
EZTIME_DB=/path/to/eztime.db

# Excel Data
EZTIME_EXCEL=/path/to/EZTIME_DATA.xlsx

# API Token
EZTIME_API_TOKEN=your-secret-token

# Development
DEBUG=true
LOGLEVEL=debug

# Production
DEBUG=false
LOGLEVEL=info
```

---

## 📞 Getting Help

### Resources

1. **Documentation:** This README file
2. **Issues:** https://github.com/anogshtorper-dev/EZTIME-TMP/issues
3. **Discussions:** https://github.com/anogshtorper-dev/EZTIME-TMP/discussions

### Report an Issue

When there's a problem:
1. Go to Issues
2. Click "New Issue"
3. Select appropriate template
4. Fill in issue details

---

## 📄 License & Credits

**Project:** EZTIME-TMP  
**Version:** 1.0  
**Last Updated:** 2026-02-28  
**Repository:** https://github.com/anogshtorper-dev/EZTIME-TMP  
**Author:** anogshtorper-dev  

---

**Tip:** Bookmark this README for quick reference!

**Happy time tracking! ⏰✨**
