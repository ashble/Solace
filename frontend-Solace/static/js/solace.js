const pill = document.getElementById('userPill'), menu = document.getElementById('roleMenu');
pill.addEventListener('click', () => {
  const open = menu.classList.toggle('open');
  pill.setAttribute('aria-expanded', open);
});
document.addEventListener('click', e => {
  if (!pill.contains(e.target) && !menu.contains(e.target)) menu.classList.remove('open');
});