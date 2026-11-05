(() => {
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // ---------- helpers ----------
  const setError = (input, message) => {
    const field = input.closest(".field");
    const out = field.querySelector(".error");
    field.classList.toggle("invalid", Boolean(message));
    out.textContent = message || "";
    return !message;
  };

  const clearOnInput = (form) => {
    form.addEventListener("input", (e) => {
      if (e.target.matches("input")) setError(e.target, "");
    });
  };

  // ---------- show / hide password ----------
  document.querySelectorAll(".toggle-pw").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
  });

  // ---------- login ----------
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    clearOnInput(loginForm);
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const email = loginForm.email;
      const password = loginForm.password;

      const ok = [
        setError(email, !email.value.trim() ? "Enter your email." :
                        !EMAIL_RE.test(email.value) ? "Enter a valid email address." : ""),
        setError(password, !password.value ? "Enter your password." : ""),
      ].every(Boolean);

      if (ok) {
        // Frontend only: hook up your backend here.
        console.log("Login submitted", { email: email.value });
      }
    });
  }

  // ---------- register ----------
  const regForm = document.getElementById("register-form");
  if (regForm) {
    clearOnInput(regForm);

    const tabs = document.querySelectorAll(".tab");
    const roleInput = document.getElementById("role");
    const therapistBlock = document.querySelector(".therapist-only");
    const license = document.getElementById("license");
    const fileInput = document.getElementById("credentials");
    const fileName = document.getElementById("credentials-name");

    const setRole = (role) => {
      roleInput.value = role;
      const isTherapist = role === "therapist";
      therapistBlock.hidden = !isTherapist;
      license.required = isTherapist;
      tabs.forEach((t) => {
        const active = t.dataset.role === role;
        t.classList.toggle("active", active);
        t.setAttribute("aria-selected", active);
      });
      if (!isTherapist) {
        setError(license, "");
        setError(fileInput, "");
      }
    };

    tabs.forEach((t) => t.addEventListener("click", () => setRole(t.dataset.role)));

    fileInput.addEventListener("change", () => {
      fileName.textContent = fileInput.files[0]?.name || "Verify your credentials";
      setError(fileInput, "");
    });

    regForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const f = regForm;
      const isTherapist = roleInput.value === "therapist";

      const checks = [
        setError(f.fullname, f.fullname.value.trim() ? "" : "Enter your full name."),
        setError(f.email, !f.email.value.trim() ? "Enter your email." :
                          !EMAIL_RE.test(f.email.value) ? "Enter a valid email address." : ""),
        setError(f.password, f.password.value.length < 8 ? "Use at least 8 characters." : ""),
        setError(f.confirm, f.confirm.value !== f.password.value ? "Passwords don't match." : ""),
        setError(f.terms, f.terms.checked ? "" : "Agree to the Terms and Privacy Policy to continue."),
      ];

      if (isTherapist) {
        checks.push(
          setError(f.license, f.license.value.trim() ? "" : "Enter your license number."),
          setError(fileInput, fileInput.files.length ? "" : "Upload a document to verify your credentials.")
        );
      }

      if (checks.every(Boolean)) {
        // Frontend only: hook up your backend here.
        console.log("Register submitted", { role: roleInput.value, email: f.email.value });
      }
    });
  }
})();
