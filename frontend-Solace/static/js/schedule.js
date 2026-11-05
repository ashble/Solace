<!DOCTYPE html>

<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width,initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #000;
    }
  </style>
</head>
<body>
<!-- STITCH_THREEJS_START:ANIMATION_13 class="fixed inset-0 w-full h-full bg-transparent" -->
<div class="fixed inset-0 w-full h-full bg-transparent" style="display:block;">
<script src="https://ajax.googleapis.com/ajax/libs/threejs/r125/three.min.js"></script>
<div id="threejs-container-ANIMATION_13" style="width:100%;height:100%"></div>
<script>
(function() {
  const container = document.getElementById('threejs-container-ANIMATION_13');
  const devicePixelRatio = window.devicePixelRatio || 1;
  /**
 * schedule.js - Dynamic multi-month calendar picker, slot selection, and appointment submission
 */
document.addEventListener('DOMContentLoaded', () => {
  // Calendar State
  const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  let currentYear = 2027;
  let currentMonthIndex = 0; // 0 = January, 1 = February, etc.
  let selectedDay = 7;
  let chosenTime = '10:00 AM';

  // DOM Elements
  const monthTitleEl = document.querySelector('.month-title');
  const prevMonthBtn = document.querySelector('.nav-arrow-btn[aria-label="Previous Month"]') || document.querySelectorAll('.nav-arrow-btn')[0];
  const nextMonthBtn = document.querySelector('.nav-arrow-btn[aria-label="Next Month"]') || document.querySelectorAll('.nav-arrow-btn')[1];
  const daysGridEl = document.querySelector('.month-days-grid');

  const selectedDateEl = document.getElementById('selectedDate');
  const selectedTimeEl = document.getElementById('selectedTime');
  const requestBtn = document.getElementById('requestAppointment');
  const modalConfirmDate = document.getElementById('modalConfirmDate');
  const modalConfirmTime = document.getElementById('modalConfirmTime');
  const requestModal = document.getElementById('requestModalOverlay');
  const successModal = document.getElementById('successModalOverlay');

  // Format Helper: "YYYY-MM-DD"
  function getISODate(year, monthIdx, day) {
    const mm = String(monthIdx + 1).padStart(2, '0');
    const dd = String(day).padStart(2, '0');
    return `${year}-${mm}-${dd}`;
  }

  // Format Helper: "Month Day, Year"
  function getDisplayDate(year, monthIdx, day) {
    return `${MONTH_NAMES[monthIdx]} ${day}, ${year}`;
  }

  // Sync displayed date in UI & modal
  function updateDateDisplays() {
    const displayStr = getDisplayDate(currentYear, currentMonthIndex, selectedDay);
    if (selectedDateEl) selectedDateEl.textContent = displayStr;
    if (modalConfirmDate) modalConfirmDate.textContent = displayStr;
  }

  // Generate dynamic calendar days for currentYear and currentMonthIndex
  function renderCalendar() {
    if (!daysGridEl || !monthTitleEl) return;

    monthTitleEl.textContent = `${MONTH_NAMES[currentMonthIndex]} ${currentYear}`;

    // Total days in current month
    const daysInMonth = new Date(currentYear, currentMonthIndex + 1, 0).getDate();

    // Day of week of the 1st day of month (0 = Sun, 1 = Mon, ..., 6 = Sat)
    const firstDayIndex = new Date(currentYear, currentMonthIndex, 1).getDay();

    // Adjust for Monday start (Mon = 0, Tue = 1, ..., Sun = 6)
    const mondayOffset = (firstDayIndex + 6) % 7;

    // Remove existing day cells and empty spacers, keeping the 7 column headers (Mon..Sun)
    const dayHeaders = Array.from(daysGridEl.querySelectorAll('.col-head'));
    daysGridEl.innerHTML = '';
    dayHeaders.forEach(header => daysGridEl.appendChild(header));

    // Append empty placeholder cells for previous month padding
    for (let i = 0; i < mondayOffset; i++) {
      const emptySpan = document.createElement('span');
      emptySpan.className = 'day-empty';
      daysGridEl.appendChild(emptySpan);
    }

    // Clamp selectedDay if switching to a month with fewer days (e.g. 31st to February)
    if (selectedDay > daysInMonth) {
      selectedDay = daysInMonth;
    }

    // Render day cells
    for (let day = 1; day <= daysInMonth; day++) {
      const dayCell = document.createElement('span');
      dayCell.className = 'cal-day-cell';
      dayCell.textContent = day;

      if (day === selectedDay) {
        dayCell.classList.add('active-date');
      }

      dayCell.addEventListener('click', () => {
        document.querySelector('.cal-day-cell.active-date')?.classList.remove('active-date');
        dayCell.classList.add('active-date');
        selectedDay = day;
        updateDateDisplays();
      });

      daysGridEl.appendChild(dayCell);
    }

    updateDateDisplays();
  }

  // Month Navigation
  if (prevMonthBtn) {
    prevMonthBtn.addEventListener('click', () => {
      currentMonthIndex--;
      if (currentMonthIndex < 0) {
        currentMonthIndex = 11;
        currentYear--;
      }
      renderCalendar();
    });
  }

  if (nextMonthBtn) {
    nextMonthBtn.addEventListener('click', () => {
      currentMonthIndex++;
      if (currentMonthIndex > 11) {
        currentMonthIndex = 0;
        currentYear++;
      }
      renderCalendar();
    });
  }

  // Time Slots Selection
  document.querySelectorAll('.time-slot-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelector('.time-slot-btn.active-slot')?.classList.remove('active-slot');
      btn.classList.add('active-slot');
      chosenTime = btn.textContent.trim();

      if (selectedTimeEl) selectedTimeEl.textContent = chosenTime;
      if (modalConfirmTime) modalConfirmTime.textContent = chosenTime;
    });
  });

  // Modal Flow Controls
  window.openRequestModal = function() {
    updateDateDisplays();
    if (modalConfirmTime) modalConfirmTime.textContent = chosenTime;
    if (requestModal) requestModal.classList.add('modal-active');
  };

  window.closeRequestModal = function() {
    if (requestModal) requestModal.classList.remove('modal-active');
  };

  window.confirmAppointmentSubmission = async function() {
    const formattedISODate = getISODate(currentYear, currentMonthIndex, selectedDay);
    try {
      await fetch('/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client: 'Sylus Qin',
          therapist: 'Dr. Zayne Li',
          date: formattedISODate,
          time: chosenTime,
          session_type: 'Online Consultation'
        })
      });
    } catch (err) {
      console.warn('API error, proceeding with local UI update:', err);
    }

    closeRequestModal();
    if (successModal) {
      successModal.classList.add('modal-active');
    } else if (requestBtn) {
      requestBtn.textContent = 'Request sent';
      requestBtn.disabled = true;
      requestBtn.closest('.summary-action-col')?.insertAdjacentHTML(
        'beforeend',
        '<p class="booking-confirmation" style="margin-top: 8px; font-size: 12px; color: #499D4B;">Your request has been submitted.</p>'
      );
    }
  };

  if (requestBtn) {
    requestBtn.addEventListener('click', () => {
      if (requestModal) {
        openRequestModal();
      } else {
        confirmAppointmentSubmission();
      }
    });
  }

  window.closeOnBackdrop = function(e, modalId) {
    if (e.target.id === modalId) {
      document.getElementById(modalId)?.classList.remove('modal-active');
    }
  };

  // Initial Calendar Render
  renderCalendar();
});

})();
</script>
</div>
<!-- STITCH_THREEJS_END:ANIMATION_13 -->
</body>
</html>
