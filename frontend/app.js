(() => {
  const api = window.APP_CONFIG?.API_BASE_URL?.replace(/\/$/, "");
  const $ = (id) => document.getElementById(id);
  const form = $("shortenForm"), input = $("longUrlInput"), button = $("shortenBtn");
  const result = $("resultCard"), output = $("shortUrlOutput"), analytics = $("analyticsCard");
  let currentCode = "";
  function message(id, text, kind = "") { const el = $(id); el.textContent = text; el.className = `message ${kind}`; }
  function validUrl(value) {
    try { const u = new URL(value); return /^https?:$/.test(u.protocol) && !!u.hostname && value.length <= 2048; }
    catch { return false; }
  }
  async function jsonResponse(response) { try { return await response.json(); } catch { return {}; } }
  form.addEventListener("submit", async (event) => {
    event.preventDefault(); const url = input.value.trim(); message("formMessage", "");
    result.hidden = true; analytics.hidden = true;
    if (!validUrl(url)) { message("formMessage", "Enter a valid HTTP or HTTPS URL, up to 2,048 characters.", "error"); input.focus(); return; }
    if (!api || !validUrl(api)) { message("formMessage", "The deployed API is not configured yet. Run the deployment script.", "error"); return; }
    button.disabled = true; button.textContent = "Creating…"; button.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(`${api}/shorten`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
      const data = await jsonResponse(response);
      if (!response.ok) throw new Error(data.error || "Could not shorten this URL.");
      if (typeof data.shortCode !== "string" || !/^[A-Za-z0-9]{1,32}$/.test(data.shortCode) || !validUrl(data.shortUrl)) throw new Error("The API returned an invalid short link.");
      currentCode = data.shortCode; output.value = data.shortUrl; $("openLink").href = data.shortUrl; result.hidden = false;
      message("formMessage", "Your short link is ready.", "success"); await refreshStats();
    } catch (error) { message("formMessage", error instanceof TypeError ? "Could not reach the API. Check your connection and deployment CORS settings." : error.message, "error"); }
    finally { button.disabled = false; button.textContent = "Shorten URL"; button.removeAttribute("aria-busy"); }
  });
  async function refreshStats() {
    if (!currentCode) return; analytics.hidden = false; message("analyticsMessage", "Refreshing statistics…");
    try {
      const response = await fetch(`${api}/stats/${encodeURIComponent(currentCode)}`), data = await jsonResponse(response);
      if (!response.ok) throw new Error(data.error || "Could not load analytics.");
      $("statShortCode").textContent = data.shortCode;
      const original = $("statLongUrl"); original.textContent = data.originalUrl;
      if (validUrl(data.originalUrl)) { original.href = data.originalUrl; original.rel = "noopener noreferrer"; } else original.removeAttribute("href");
      $("statClicks").textContent = Number.isFinite(Number(data.clicks)) ? String(data.clicks) : "—";
      const date = new Date(data.createdAt); $("statCreatedAt").textContent = Number.isNaN(date.valueOf()) ? "—" : date.toLocaleString();
      message("analyticsMessage", "Statistics loaded from DynamoDB.", "success");
    } catch (error) { message("analyticsMessage", error instanceof TypeError ? "Could not reach the API." : error.message, "error"); }
  }
  $("refreshBtn").addEventListener("click", refreshStats);
  $("copyBtn").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(output.value); message("copyMessage", "Copied to clipboard.", "success"); }
    catch { output.select(); message("copyMessage", "Select and copy the link.", "error"); }
  });
})();
