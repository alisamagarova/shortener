from typing import Optional
from urllib.parse import urlparse

from .config import settings


def validate_url(url: str) -> Optional[str]:
    """Возвращает описание причины отклонения, либо None если URL валиден (ФТ №1)."""
    if not url or not url.strip():
        return "originalUrl не может быть пустым"

    if len(url) > settings.max_url_length:
        return f"originalUrl превышает максимальную длину {settings.max_url_length} символов"

    try:
        parsed = urlparse(url)
    except ValueError:
        return "originalUrl не является синтаксически корректным URL"

    if not parsed.scheme or not parsed.netloc:
        return "originalUrl должен быть синтаксически корректным URL со схемой и хостом"

    if parsed.scheme not in settings.allowed_schemes:
        return (
            f"Схема '{parsed.scheme}' не поддерживается, "
            f"допустимы только: {', '.join(settings.allowed_schemes)}"
        )

    return None
