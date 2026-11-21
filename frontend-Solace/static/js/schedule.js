(() => {
  const form = document.getElementById('appointment-request');
  const submit = form.querySelector('button[type="submit"]');
  const status = document.getElementById('appointment-request-status');

  submit.disabled = false;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (submit.disabled) return;

    const fields = new FormData(form);
    const payload = {
      therapist_id: Number(fields.get('therapist_id')),
      date: fields.get('date'),
      time: fields.get('time'),
    };

    const therapist = form.elements.therapist_id.selectedOptions[0].textContent;
    submit.disabled = true;
    status.textContent = 'Sending request…';
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': fields.get('csrf_token') },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        status.textContent = error.error || 'The request could not be saved. Try again.';
        return;
      }

      const list = document.querySelector('.client-appointment-list');
      if (list) {
        const items = list.querySelector('ul') || document.createElement('ul');
        list.querySelector('p')?.remove();
        const appointment = document.createElement('li');
        appointment.textContent = `${therapist} · ${payload.date} at ${payload.time} · Pending`;
        items.prepend(appointment);
        if (!items.parentElement) list.append(items);
      }
      form.elements.date.value = '';
      form.elements.time.value = '';
      status.textContent = 'Request submitted. Your appointment is pending confirmation.';
    } catch {
      status.textContent = 'The request could not be confirmed. Check with the therapist before submitting it again.';
    } finally {
      submit.disabled = false;
    }
  });
})();
