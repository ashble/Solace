const sidebarToggle = document.querySelector(".sidebar-toggle");

if (sidebarToggle) {
  sidebarToggle.setAttribute("aria-expanded", "false");
  sidebarToggle.hidden = false;

  sidebarToggle.addEventListener("click", () => {
    const expanded = sidebarToggle.getAttribute("aria-expanded") === "true";
    sidebarToggle.setAttribute("aria-expanded", String(!expanded));
  });

  sidebarToggle.closest(".sidebar").addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sidebarToggle.offsetWidth &&
        sidebarToggle.getAttribute("aria-expanded") === "true") {
      sidebarToggle.setAttribute("aria-expanded", "false");
      sidebarToggle.focus();
    }
  });
}
