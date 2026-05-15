# tests/test_credentials.py
import pytest
from pathlib import Path
from unittest.mock import patch
from ovh_claude.credentials import load_credentials, CredentialsError

VALID_INI = """
[default]
endpoint=ovh-eu
application_key=APP_KEY
application_secret=APP_SECRET
consumer_key=CONSUMER_KEY
"""

def test_load_valid_credentials(tmp_path):
    creds_file = tmp_path / "credentials"
    creds_file.write_text(VALID_INI)
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        result = load_credentials()
    assert result == {
        "endpoint": "ovh-eu",
        "application_key": "APP_KEY",
        "application_secret": "APP_SECRET",
        "consumer_key": "CONSUMER_KEY",
    }

def test_missing_file_raises(tmp_path):
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", tmp_path / "missing"):
        with pytest.raises(CredentialsError, match="not found"):
            load_credentials()

def test_missing_key_raises(tmp_path):
    ini = "[default]\nendpoint=ovh-eu\napplication_key=APP_KEY\napplication_secret=APP_SECRET\n"
    creds_file = tmp_path / "credentials"
    creds_file.write_text(ini)
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        with pytest.raises(CredentialsError, match="consumer_key"):
            load_credentials()
