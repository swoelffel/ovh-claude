import configparser
from pathlib import Path

CREDENTIALS_PATH = Path.home() / ".config" / "ovh" / "credentials"
REQUIRED_KEYS = ("endpoint", "application_key", "application_secret", "consumer_key")


class CredentialsError(Exception):
    pass


def load_credentials() -> dict:
    if not CREDENTIALS_PATH.exists():
        raise CredentialsError(f"Credentials file not found: {CREDENTIALS_PATH}\nCreate one at https://api.ovh.com/createToken/")
    parser = configparser.ConfigParser()
    try:
        parser.read(CREDENTIALS_PATH)
    except configparser.Error as e:
        raise CredentialsError(f"Credentials file parse error: {e}") from e
    section = parser["default"] if "default" in parser else {}
    missing = [k for k in REQUIRED_KEYS if k not in section]
    if missing:
        raise CredentialsError(f"Missing keys in {CREDENTIALS_PATH}: {', '.join(missing)}")
    return {k: section[k] for k in REQUIRED_KEYS}
