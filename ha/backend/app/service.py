from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .cache import RedisCache
from .codegen import generate_code
from .config import settings
from .models import Link

_MAX_CODE_GENERATION_ATTEMPTS = 5


@dataclass
class CreateLinkResult:
    link: Link
    created: bool  # True -> новая ссылка (201), False -> уже существовала (200)


def get_or_create_link(db: Session, original_url: str) -> CreateLinkResult:
    """Реализует ФТ №2: вернуть существующий код, либо создать новый."""
    existing = db.query(Link).filter(Link.original_url == original_url).first()
    if existing is not None:
        return CreateLinkResult(link=existing, created=False)

    for _ in range(_MAX_CODE_GENERATION_ATTEMPTS):
        code = generate_code(settings.code_length)
        link = Link(code=code, original_url=original_url)
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            # Коллизия уникального code (ФТ/НФТ №6) — пробуем сгенерировать заново.
            db.rollback()
            continue
        db.refresh(link)
        return CreateLinkResult(link=link, created=True)

    raise RuntimeError("Не удалось сгенерировать уникальный код после нескольких попыток")


def resolve_code(db: Session, cache: RedisCache, code: str) -> str | None:
    """Реализует ФТ №3 с использованием общего Redis-кэша (НФТ №5)."""
    cached_url = cache.get(code)
    if cached_url is not None:
        return cached_url

    link = db.query(Link).filter(Link.code == code).first()
    if link is None:
        return None

    cache.put(code, link.original_url)
    return link.original_url
