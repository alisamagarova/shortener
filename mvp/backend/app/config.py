import os


def _int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://shortener:shortener@localhost:5432/shortener",
    )

    # Ограничение на длину и допустимые схемы оригинального URL (ФТ №1)
    max_url_length: int = _int_env("MAX_URL_LENGTH", 2048)
    allowed_schemes: tuple[str, ...] = ("http", "https")

    # Длина генерируемого короткого кода
    code_length: int = _int_env("CODE_LENGTH", 7)

    # Ёмкость LRU-кэша (НФТ №5)
    cache_max_size: int = _int_env("CACHE_MAX_SIZE", 1000)

    # Rate limiting (НФТ №3, №4): запросов в минуту с одного IP
    rate_limit_create_per_minute: int = _int_env("RATE_LIMIT_CREATE_PER_MINUTE", 20)
    rate_limit_redirect_per_minute: int = _int_env("RATE_LIMIT_REDIRECT_PER_MINUTE", 300)

    api_prefix: str = os.environ.get("API_PREFIX", "/api/v1")

    cors_origins: list[str] = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()
