// nginx проксирует /api/v1 через LB на реплики backend, поэтому относительный
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

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  // navigator.clipboard недоступен вне secure context (например, http:// без TLS) —
  // используем запасной вариант через скрытый textarea.
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try {
    if (!document.execCommand("copy")) {
      throw new Error("execCommand('copy') failed");
    }
  } finally {
    document.body.removeChild(textarea);
  }
}

copyBtn.addEventListener("click", async () => {
  const original = copyBtn.textContent;
  try {
    await copyText(resultLink.href);
    copyBtn.textContent = "Скопировано!";
  } catch (err) {
    copyBtn.textContent = "Не удалось скопировать";
  } finally {
    setTimeout(() => {
      copyBtn.textContent = original;
    }, 1500);
  }
});
