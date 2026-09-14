// В docker-compose nginx проксирует /api/v1 на backend, поэтому относительный
// путь работает без дополнительной настройки. Для локального запуска фронтенда
// напрямую (без nginx) можно переопределить адрес backend через window.API_BASE.
const API_BASE = window.API_BASE || "/api/v1";

const form = document.getElementById("shorten-form");
const input = document.getElementById("url-input");
const submitBtn = document.getElementById("submit-btn");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");
const resultLink = document.getElementById("result-link");
const copyBtn = document.getElementById("copy-btn");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
  resultEl.hidden = true;
}

function showResult(shortCode) {
  const shortUrl = `${window.location.origin}${API_BASE}/${shortCode}`;
  resultLink.href = shortUrl;
  resultLink.textContent = shortUrl;
  resultEl.hidden = false;
  errorEl.hidden = true;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const originalUrl = input.value.trim();
  if (!originalUrl) {
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Сокращаем...";

  try {
    const response = await fetch(`${API_BASE}/links`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ originalUrl }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const message = data?.detail || `Ошибка запроса (${response.status})`;
      showError(message);
      return;
    }

    showResult(data.shortCode);
  } catch (err) {
    showError("Не удалось связаться с сервером. Попробуйте позже.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Сократить";
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(resultLink.href);
    const original = copyBtn.textContent;
    copyBtn.textContent = "Скопировано!";
    setTimeout(() => {
      copyBtn.textContent = original;
    }, 1500);
  } catch (err) {
    // clipboard API недоступен (например, без HTTPS) — молча игнорируем
  }
});
