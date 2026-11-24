window.solaceCsrfHeaders = async function (headers = {}) {
  const response = await fetch("/api/csrf", { credentials: "same-origin" });
  const data = await response.json();
  if (!response.ok || !data.csrf_token) throw new Error("Could not prepare a secure request.");
  return { ...headers, "X-CSRF-Token": data.csrf_token };
};
