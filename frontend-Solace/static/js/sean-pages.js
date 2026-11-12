// Loaded only by the assigned booking, appointment, and profile pages.
(() => {
  const profileForm = document.querySelector('#profileForm');
  if (profileForm) {
    profileForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const notice = document.querySelector('#profileEditorNotice');
      try {
        const response = await fetch(`/api/profile/${profileForm.dataset.role}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(Object.fromEntries(new FormData(profileForm)))
        });
        if (!response.ok) throw new Error('Profile save failed');
        document.querySelector('#profileEditor')?.close();
        const savedNotice = document.querySelector('#profileNotice');
        if (savedNotice) savedNotice.textContent = 'Profile updated successfully.';
        window.setTimeout(() => window.location.reload(), 450);
      } catch {
        if (notice) notice.textContent = 'Could not save changes. Please try again.';
      }
    });
  }

  async function updateAppointment(button, row, status) {
    const confirmation = status === 'Cancelled'
      ? 'Cancel this appointment request?'
      : 'Accept and confirm this appointment request?';
    if (!window.confirm(confirmation)) return;
    button.disabled = true;
    try {
      const response = await fetch(`/api/appointments/${row.dataset.appointmentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!response.ok) throw new Error('Appointment update failed');
      window.location.reload();
    } catch {
      button.disabled = false;
      button.textContent = 'Try again';
    }
  }

  document.querySelectorAll('[data-appointment-id] [data-status]').forEach((button) => {
    button.addEventListener('click', () => updateAppointment(button, button.closest('[data-appointment-id]'), button.dataset.status));
  });

  const reviewDialog = document.querySelector('#appointmentReview');
  document.querySelectorAll('[data-review]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = button.closest('[data-appointment-id]');
      if (!row || !reviewDialog) return;
      document.querySelector('#reviewClient').textContent = row.dataset.client;
      document.querySelector('#reviewEmail').textContent = row.dataset.email;
      document.querySelector('#reviewSchedule').textContent = row.dataset.scheduleLabel;
      document.querySelector('#reviewSession').textContent = row.dataset.session;
      document.querySelector('#reviewStatus').textContent = row.dataset.status;
      const confirmButton = document.querySelector('#reviewConfirm');
      confirmButton.hidden = row.dataset.status !== 'Pending';
      confirmButton.onclick = () => updateAppointment(confirmButton, row, 'Confirmed');
      reviewDialog.showModal();
    });
  });

  const search = document.querySelector('.booking-search');
  const statusFilter = document.querySelector('.booking-filter');
  const bookingFilters = Array.from(document.querySelectorAll('[data-booking-filter]'));
  const sortOrder = document.querySelector('.booking-sort');
  const tableBody = document.querySelector('.appointment-table tbody');
  if (!tableBody) return;

  const rows = Array.from(tableBody.querySelectorAll('tr[data-appointment-id]'));
  const noResults = tableBody.querySelector('.no-filter-results');
  const pageSize = 10;
  let currentPage = 1;
  const pagination = document.querySelector('.booking-pagination');
  const previousButton = pagination?.querySelector('.previous-page');
  const nextButton = pagination?.querySelector('.next-page');

  function renderRows() {
    const query = (search?.value || '').trim().toLowerCase();
    const status = statusFilter?.value || bookingFilters.find((button) => button.getAttribute('aria-pressed') === 'true')?.dataset.bookingFilter || 'all';
    const matching = rows.filter((row) =>
      (!query || row.dataset.search.includes(query)) && (status === 'all' || row.dataset.status === status)
    );
    const direction = sortOrder?.value === 'asc' ? 1 : -1;
    matching.sort((left, right) => (Number(left.dataset.schedule) - Number(right.dataset.schedule)) * direction);

    const pageCount = Math.max(1, Math.ceil(matching.length / pageSize));
    currentPage = Math.min(currentPage, pageCount);
    const pageRows = matching.slice((currentPage - 1) * pageSize, currentPage * pageSize);
    pageRows.forEach((row) => tableBody.insertBefore(row, noResults));
    rows.forEach((row) => { row.hidden = !pageRows.includes(row); });
    if (noResults) noResults.hidden = matching.length > 0 || rows.length === 0;

    const visibleCount = document.querySelector('#visibleAppointmentCount');
    const totalCount = document.querySelector('#matchingAppointmentCount');
    if (visibleCount) visibleCount.textContent = pageRows.length;
    if (totalCount) totalCount.textContent = matching.length;

    if (pagination) {
      pagination.hidden = rows.length === 0;
      pagination.querySelectorAll('.dynamic-page').forEach((button) => button.remove());
      for (let page = 1; page <= pageCount; page += 1) {
        const pageButton = document.createElement('button');
        pageButton.type = 'button';
        pageButton.className = `page-btn dynamic-page${page === currentPage ? ' active-page' : ''}`;
        pageButton.textContent = page;
        pageButton.setAttribute('aria-label', `Page ${page}`);
        pageButton.addEventListener('click', () => { currentPage = page; renderRows(); });
        pagination.insertBefore(pageButton, nextButton);
      }
      if (previousButton) previousButton.disabled = currentPage === 1;
      if (nextButton) nextButton.disabled = currentPage === pageCount;
    }
  }

  search?.addEventListener('input', () => { currentPage = 1; renderRows(); });
  statusFilter?.addEventListener('change', () => { currentPage = 1; renderRows(); });
  bookingFilters.forEach((button) => button.addEventListener('click', () => {
    bookingFilters.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
    currentPage = 1;
    renderRows();
  }));
  sortOrder?.addEventListener('change', () => { currentPage = 1; renderRows(); });
  previousButton?.addEventListener('click', () => { currentPage -= 1; renderRows(); });
  nextButton?.addEventListener('click', () => { currentPage += 1; renderRows(); });
  renderRows();
})();
