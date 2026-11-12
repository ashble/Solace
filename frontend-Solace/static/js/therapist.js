document.getElementById('strip').addEventListener('click', e => {
  const btn = e.target.closest('.day');
  if (!btn) return;
  document.querySelectorAll('.day').forEach(d => d.classList.remove('active'));
  btn.classList.add('active');
});