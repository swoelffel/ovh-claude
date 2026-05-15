import configparser
from pathlib import Path

CREDENTIALS_PATH = Path.home() / ".config" / "ovh" / "credentials"
REQUIRED_KEYS = ("endpoint", "application_key", "application_secret", "consumer_key")

TEMPLATE_HINT = """
Expected format:
    [default]
    endpoint=ovh-eu
    application_key=...
    application_secret=...
    consumer_key=...

Generate a token at https://api.ovh.com/createToken/"""


class CredentialsError(Exception):
    pass


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith("your_") or lowered.startswith("your-"):
        return True
    if value.startswith("<") and value.endswith(">"):
        return True
    return False


def load_credentials() -> dict:
    path = CREDENTIALS_PATH
    if not path.exists():
        raise CredentialsError(
            f"Credentials file not found: {path}\n"
            f"Create one at https://api.ovh.com/createToken/"
        )

    parser = configparser.ConfigParser()
    try:
        parser.read(path)
    except configparser.MissingSectionHeaderError:
        raise CredentialsError(
            f"Missing [default] section header in {path}.\n"
            f"Your credentials file must start with [default] on its own line.\n"
            f"{TEMPLATE_HINT}"
        )
    except configparser.Error as e:
        raise CredentialsError(f"Credentials file parse error: {e}")

    if "default" not in parser:
        raise CredentialsError(
            f"Missing [default] section header in {path}.\n"
            f"Your credentials file must start with [default] on its own line.\n"
            f"{TEMPLATE_HINT}"
        )

    section = parser["default"]
    missing = [k for k in REQUIRED_KEYS if k not in section]
    if missing:
        raise CredentialsError(
            f"Missing keys in {path}: {', '.join(missing)}\n"
            f"{TEMPLATE_HINT}"
        )

    loaded = {k: section[k].strip() for k in REQUIRED_KEYS}

    empty = [k for k, v in loaded.items() if not v]
    if empty:
        raise CredentialsError(
            f"Empty value for {', '.join(empty)} in {path}.\n"
            f"Fill in the missing values. Generate a token at https://api.ovh.com/createToken/"
        )

    placeholders = [k for k, v in loaded.items() if _looks_like_placeholder(v)]
    if placeholders:
        raise CredentialsError(
            f"Placeholder value detected for {', '.join(placeholders)} in {path}.\n"
            f"Replace with real values from https://api.ovh.com/createToken/"
        )

    return loaded
