document.querySelectorAll(".toggle-pw").forEach((button) => {
  button.addEventListener("click", () => {
    const input = button.previousElementSibling;
    const showPassword = input.type === "password";
    input.type = showPassword ? "text" : "password";
    button.textContent = showPassword ? "Hide" : "Show";
    button.setAttribute("aria-label", showPassword ? "Hide password" : "Show password");
  });
});
