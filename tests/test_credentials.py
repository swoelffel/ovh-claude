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


def test_missing_default_section_clear_message(tmp_path):
    creds_file = tmp_path / "credentials"
    creds_file.write_text("endpoint=ovh-eu\napplication_key=K\n")  # No [default]
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        with pytest.raises(CredentialsError) as exc_info:
            load_credentials()
    msg = str(exc_info.value)
    assert "[default]" in msg
    assert "section header" in msg.lower()


def test_missing_keys_message_includes_template(tmp_path):
    creds_file = tmp_path / "credentials"
    creds_file.write_text("[default]\nendpoint=ovh-eu\n")  # only endpoint
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        with pytest.raises(CredentialsError) as exc_info:
            load_credentials()
    msg = str(exc_info.value)
    assert "application_key" in msg
    assert "application_secret" in msg
    assert "consumer_key" in msg
    # Template hint
    assert "[default]" in msg


def test_empty_value_raises(tmp_path):
    creds_file = tmp_path / "credentials"
    creds_file.write_text(
        "[default]\n"
        "endpoint=ovh-eu\n"
        "application_key=\n"
        "application_secret=S\n"
        "consumer_key=C\n"
    )
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        with pytest.raises(CredentialsError) as exc_info:
            load_credentials()
    msg = str(exc_info.value)
    assert "application_key" in msg
    assert "empty" in msg.lower()


def test_placeholder_value_your_prefix(tmp_path):
    creds_file = tmp_path / "credentials"
    creds_file.write_text(
        "[default]\n"
        "endpoint=ovh-eu\n"
        "application_key=YOUR_APP_KEY\n"
        "application_secret=S\n"
        "consumer_key=C\n"
    )
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        with pytest.raises(CredentialsError) as exc_info:
            load_credentials()
    msg = str(exc_info.value)
    assert "application_key" in msg
    assert "placeholder" in msg.lower()
    assert "createToken" in msg


def test_placeholder_value_angle_brackets(tmp_path):
    creds_file = tmp_path / "credentials"
    creds_file.write_text(
        "[default]\n"
        "endpoint=ovh-eu\n"
        "application_key=K\n"
        "application_secret=<MY_SECRET>\n"
        "consumer_key=C\n"
    )
    with patch("ovh_claude.credentials.CREDENTIALS_PATH", creds_file):
        with pytest.raises(CredentialsError) as exc_info:
            load_credentials()
    msg = str(exc_info.value)
    assert "application_secret" in msg
    assert "placeholder" in msg.lower()
