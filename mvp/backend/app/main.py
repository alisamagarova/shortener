import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from .cache import LRUCache
from .config import settings
from .database import Base, engine, get_db
from .rate_limiter import RateLimiter
from .schemas import LinkCreateRequest, LinkResponse
from .service import get_or_create_link, resolve_code
from .validation import validate_url

logger = logging.getLogger("shortener")

app = FastAPI(title="URL Shortener API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = LRUCache(max_size=settings.cache_max_size)
create_rate_limiter = RateLimiter(settings.rate_limit_create_per_minute)
redirect_rate_limiter = RateLimiter(settings.rate_limit_redirect_per_minute)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce_create_rate_limit(request: Request) -> None:
    if not create_rate_limiter.allow(_client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="Превышен лимит запросов на создание ссылок: не более 20 в минуту с одного IP",
        )


def enforce_redirect_rate_limit(request: Request) -> None:
    if not redirect_rate_limiter.allow(_client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="Превышен лимит запросов на переход по ссылкам: не более 300 в минуту с одного IP",
        )


@app.get(f"{settings.api_prefix}/health")
def health() -> dict:
    return {"status": "ok"}


@app.post(
    f"{settings.api_prefix}/links",
    response_model=LinkResponse,
    response_model_by_alias=True,
    dependencies=[Depends(enforce_create_rate_limit)],
)
def create_link(payload: LinkCreateRequest, db: Session = Depends(get_db)):
    reason = validate_url(payload.original_url)
    if reason is not None:
        raise HTTPException(status_code=400, detail=reason)

    result = get_or_create_link(db, payload.original_url)

    response = LinkResponse(
        id=result.link.id,
        shortCode=result.link.code,
        originalUrl=result.link.original_url,
        createdAt=result.link.created_at,
    )
    status_code = 201 if result.created else 200
    return _json_response(response, status_code)


@app.get(f"{settings.api_prefix}/{{code}}", dependencies=[Depends(enforce_redirect_rate_limit)])
def redirect_to_original(code: str, db: Session = Depends(get_db)):
    original_url = resolve_code(db, cache, code)
    if original_url is None:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return RedirectResponse(url=original_url, status_code=302)


def _json_response(response: LinkResponse, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(by_alias=True, mode="json"),
    )
