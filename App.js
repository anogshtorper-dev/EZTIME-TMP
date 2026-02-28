// פונקציה להמיר קוד QR או NFC לפרמטרים
function handleScanInput(scanCode) {
  const scanData = parseScanCode(scanCode);
  
  // עדכון השדות עם המידע שנשלף
  document.getElementById('subsidiary').value = scanData.subsidiary;
  document.getElementById('role').value = scanData.role;
  document.getElementById('employee_name').value = scanData.employee_name;
  
  // עדכון שעת הסריקה
  document.getElementById('scan_time').value = new Date().toISOString().split('T')[1].split('.')[0]; // חותמת זמן
}

// פונקציה לפענוח קוד QR/NFC
function parseScanCode(scanCode) {
  // זו יכולה להיות פונקציה שמפענחת את הקוד ומחזירה אובייקט עם המידע
  return {
    subsidiary: 'Subsidiary A',  // המידע שמתקבל מתוך הקוד
    role: 'Security',
    employee_name: 'Dana Alon'  // המידע שמתקבל מתוך הקוד
  };
}

// פונקציה לשליחת משמרת
function submitShift() {
  const shiftData = {
    employee_id: document.getElementById('employee_id').value,
    subsidiary: document.getElementById('subsidiary').value,
    role: document.getElementById('role').value,
    employee_name: document.getElementById('employee_name').value,
    scan_time: document.getElementById('scan_time').value,
    clock_in_out: document.getElementById('clock_in_out').value, // כניסה או יציאה
    start_time: document.getElementById('start_time').value,
    end_time: document.getElementById('end_time').value
  };

  // אם יש קוד סריקה, נקרא לפונקציה שתמלא את השדות
  const scanCode = document.getElementById('scanCode').value;
  if (scanCode) {
    handleScanInput(scanCode);
  }

  // שלח את הנתונים ל־API
  fetch('/shifts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(shiftData)
  }).then(response => {
    if (response.ok) {
      alert('Shift added successfully!');
    } else {
      alert('Failed to add shift');
    }
  });
}
