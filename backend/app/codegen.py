import secrets
import string

_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_code(length: int) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
