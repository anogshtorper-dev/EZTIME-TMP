// פונקציה להמיר קוד QR או NFC לפרמטרים
function handleScanInput(scanCode) {
  // דימוי המרה (בפועל תוכל לשלוף את המידע מתוך QR או NFC)
  const scanData = parseScanCode(scanCode);
  
  // עדכון השדות עם המידע שנשלף
  document.getElementById('subsidiary').value = scanData.subsidiary;
  document.getElementById('role').value = scanData.role;
}

// פונקציה לפענוח קוד QR/NFC
function parseScanCode(scanCode) {
  // זו יכולה להיות פונקציה שמפענחת את הקוד ומחזירה אובייקט עם המידע
  return {
    subsidiary: 'Subsidiary A', // דוגמה
    role: 'Security' // דוגמה
  };
}

// פונקציה לשליחת משמרת
function submitShift() {
  const shiftData = {
    employee_id: document.getElementById('employee_id').value,
    subsidiary: document.getElementById('subsidiary').value,
    role: document.getElementById('role').value,
    date: new Date().toISOString().split('T')[0], // תאריך במבנה YYYY-MM-DD
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
