# tests/test_cli.py
import json
import sys
import pytest
from unittest.mock import patch, MagicMock
from ovh_claude.cli import main_proxy, main_claude
from ovh_claude.credentials import CredentialsError

FAKE_CREDS = {
    "endpoint": "ovh-eu",
    "application_key": "APP_KEY",
    "application_secret": "APP_SECRET",
    "consumer_key": "CONSUMER_KEY",
}

def test_get_request_prints_json(capsys):
    mock_client = MagicMock()
    mock_client.get.return_value = ["/vps/vps-xxx.ovh.net"]
    with patch("ovh_claude.cli.load_credentials", return_value=FAKE_CREDS), \
         patch("ovh_claude.cli.ovh.Client", return_value=mock_client), \
         patch("sys.argv", ["ovh-api", "GET", "/vps"]):
        main_proxy()
    out = capsys.readouterr().out
    assert json.loads(out) == ["/vps/vps-xxx.ovh.net"]

def test_post_request_with_body(capsys):
    mock_client = MagicMock()
    mock_client.post.return_value = {"id": 42}
    body = '{"fieldType": "A", "target": "1.2.3.4"}'
    with patch("ovh_claude.cli.load_credentials", return_value=FAKE_CREDS), \
         patch("ovh_claude.cli.ovh.Client", return_value=mock_client), \
         patch("sys.argv", ["ovh-api", "POST", "/domain/zone/example.com/record", body]):
        main_proxy()
    mock_client.post.assert_called_once_with("/domain/zone/example.com/record", fieldType="A", target="1.2.3.4")

def test_api_error_exits_nonzero(capsys):
    import ovh
    mock_client = MagicMock()
    mock_client.get.side_effect = ovh.exceptions.APIError("Forbidden")
    with patch("ovh_claude.cli.load_credentials", return_value=FAKE_CREDS), \
         patch("ovh_claude.cli.ovh.Client", return_value=mock_client), \
         patch("sys.argv", ["ovh-api", "GET", "/vps"]):
        with pytest.raises(SystemExit) as exc_info:
            main_proxy()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Forbidden" in err
    assert "APP_SECRET" not in err

def test_invalid_method_exits_nonzero(capsys):
    with patch("ovh_claude.cli.load_credentials", return_value=FAKE_CREDS), \
         patch("sys.argv", ["ovh-api", "PATCH", "/vps"]):
        with pytest.raises(SystemExit) as exc_info:
            main_proxy()
    assert exc_info.value.code == 1

def test_install_skill_copies_file(tmp_path, capsys):
    skills_dir = tmp_path / ".claude" / "skills"
    fake_skill = tmp_path / "ovh-api.md"
    fake_skill.write_text("# OVH skill")
    with patch("ovh_claude.cli.SKILLS_SOURCE", fake_skill), \
         patch("ovh_claude.cli.SKILLS_DEST_DIR", skills_dir), \
         patch("sys.argv", ["ovh-claude", "install-skill"]):
        main_claude()
    assert (skills_dir / "ovh-api.md").read_text() == "# OVH skill"
    out = capsys.readouterr().out
    assert "installed" in out.lower()

def test_install_skill_creates_dir(tmp_path, capsys):
    skills_dir = tmp_path / "nonexistent" / "skills"
    fake_skill = tmp_path / "ovh-api.md"
    fake_skill.write_text("# OVH skill")
    with patch("ovh_claude.cli.SKILLS_SOURCE", fake_skill), \
         patch("ovh_claude.cli.SKILLS_DEST_DIR", skills_dir), \
         patch("sys.argv", ["ovh-claude", "install-skill"]):
        main_claude()
    assert (skills_dir / "ovh-api.md").exists()

def test_install_skill_unknown_subcommand_exits(capsys):
    with patch("sys.argv", ["ovh-claude", "unknown"]):
        with pytest.raises(SystemExit) as exc_info:
            main_claude()
    assert exc_info.value.code == 1

from ovh_claude.cli import _check_python_version, _check_credentials_file, _check_credentials_keys

def test_check_python_version_ok():
    with patch("ovh_claude.cli.sys.version_info", (3, 12, 1)):
        status, message = _check_python_version()
    assert status == "OK"
    assert "3.12.1" in message

def test_check_python_version_too_old():
    with patch("ovh_claude.cli.sys.version_info", (3, 9, 0)):
        status, message = _check_python_version()
    assert status == "FAIL"
    assert "3.10" in message

def test_check_credentials_file_present(tmp_path):
    creds = tmp_path / "credentials"
    creds.write_text("[default]\nendpoint=ovh-eu\n")
    with patch("ovh_claude.cli.credentials.CREDENTIALS_PATH", creds):
        status, message = _check_credentials_file()
    assert status == "OK"
    assert str(creds) in message

def test_check_credentials_file_missing(tmp_path):
    missing = tmp_path / "absent"
    with patch("ovh_claude.cli.credentials.CREDENTIALS_PATH", missing):
        status, message = _check_credentials_file()
    assert status == "FAIL"
    assert "not found" in message
    assert "createToken" in message

def test_check_credentials_keys_complete(tmp_path):
    creds = tmp_path / "credentials"
    creds.write_text(
        "[default]\n"
        "endpoint=ovh-eu\n"
        "application_key=K\n"
        "application_secret=S\n"
        "consumer_key=C\n"
    )
    with patch("ovh_claude.cli.credentials.CREDENTIALS_PATH", creds):
        status, message = _check_credentials_keys()
    assert status == "OK"
    assert "endpoint" in message
    assert "application_key" in message

def test_check_credentials_keys_missing(tmp_path):
    creds = tmp_path / "credentials"
    creds.write_text("[default]\nendpoint=ovh-eu\napplication_key=K\n")
    with patch("ovh_claude.cli.credentials.CREDENTIALS_PATH", creds):
        status, message = _check_credentials_keys()
    assert status == "FAIL"
    assert "application_secret" in message
    assert "consumer_key" in message

from ovh_claude.cli import _check_skill_installed, _check_api_reachable, main_doctor

def test_check_skill_installed_ok(tmp_path):
    skill_path = tmp_path / "ovh-api.md"
    skill_path.write_text("# skill")
    with patch("ovh_claude.cli.SKILLS_DEST_DIR", tmp_path):
        status, message = _check_skill_installed()
    assert status == "OK"
    assert str(skill_path) in message

def test_check_skill_installed_missing(tmp_path):
    with patch("ovh_claude.cli.SKILLS_DEST_DIR", tmp_path):
        status, message = _check_skill_installed()
    assert status == "FAIL"
    assert "ovh-claude install-skill" in message

def test_check_api_reachable_ok():
    mock_client = MagicMock()
    mock_client.get.return_value = {"status": "validated", "credentialId": 5678}
    with patch("ovh_claude.cli.load_credentials", return_value=FAKE_CREDS), \
         patch("ovh_claude.cli.ovh.Client", return_value=mock_client):
        status, message = _check_api_reachable()
    assert status == "OK"
    assert "validated" in message
    assert "currentCredential" in message
    mock_client.get.assert_called_once_with("/auth/currentCredential")

def test_check_api_reachable_api_error():
    import ovh
    mock_client = MagicMock()
    mock_client.get.side_effect = ovh.exceptions.APIError("Forbidden")
    with patch("ovh_claude.cli.load_credentials", return_value=FAKE_CREDS), \
         patch("ovh_claude.cli.ovh.Client", return_value=mock_client):
        status, message = _check_api_reachable()
    assert status == "FAIL"
    assert "Forbidden" in message
    assert FAKE_CREDS["application_secret"] not in message

def test_check_api_reachable_credentials_error():
    with patch("ovh_claude.cli.load_credentials", side_effect=CredentialsError("Credentials file not found")):
        status, message = _check_api_reachable()
    assert status == "FAIL"
    assert "Credentials" in message

def test_main_doctor_all_pass(capsys):
    with patch("ovh_claude.cli._check_python_version", return_value=("OK", "Python 3.12.1 (≥ 3.10 required)")), \
         patch("ovh_claude.cli._check_credentials_file", return_value=("OK", "Credentials file: /tmp/c")), \
         patch("ovh_claude.cli._check_credentials_keys", return_value=("OK", "Required keys: endpoint, application_key, application_secret, consumer_key")), \
         patch("ovh_claude.cli._check_skill_installed", return_value=("OK", "Skill installed: /tmp/s")), \
         patch("ovh_claude.cli._check_api_reachable", return_value=("OK", "OVH API reachable (GET /auth/currentCredential) → status: validated")), \
         patch("sys.argv", ["ovh-claude", "doctor"]):
        main_doctor()
    out = capsys.readouterr().out
    assert "[✓] Python" in out
    assert "[✓] Credentials file" in out
    assert "[✓] Required keys" in out
    assert "[✓] Skill installed" in out
    assert "[✓] OVH API reachable" in out
    assert "All checks passed" in out

def test_main_doctor_credentials_missing_short_circuits(capsys):
    with patch("ovh_claude.cli._check_python_version", return_value=("OK", "Python 3.12.1 (≥ 3.10 required)")), \
         patch("ovh_claude.cli._check_credentials_file", return_value=("FAIL", "Credentials file: /tmp/c (not found)\n    → Create one at https://api.ovh.com/createToken/")), \
         patch("ovh_claude.cli._check_credentials_keys") as mock_keys, \
         patch("ovh_claude.cli._check_skill_installed", return_value=("OK", "Skill installed: /tmp/s")), \
         patch("ovh_claude.cli._check_api_reachable") as mock_api, \
         patch("sys.argv", ["ovh-claude", "doctor"]):
        with pytest.raises(SystemExit) as exc_info:
            main_doctor()
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[✗] Credentials file" in out
    assert "[ ] Required keys (skipped" in out
    assert "[ ] OVH API reachable (skipped" in out
    assert "1 check failed" in out
    mock_keys.assert_not_called()
    mock_api.assert_not_called()

def test_main_doctor_api_fail_exits_nonzero(capsys):
    with patch("ovh_claude.cli._check_python_version", return_value=("OK", "Python 3.12.1 (≥ 3.10 required)")), \
         patch("ovh_claude.cli._check_credentials_file", return_value=("OK", "Credentials file: /tmp/c")), \
         patch("ovh_claude.cli._check_credentials_keys", return_value=("OK", "Required keys: endpoint, application_key, application_secret, consumer_key")), \
         patch("ovh_claude.cli._check_skill_installed", return_value=("OK", "Skill installed: /tmp/s")), \
         patch("ovh_claude.cli._check_api_reachable", return_value=("FAIL", "OVH API error: 403 Forbidden")), \
         patch("sys.argv", ["ovh-claude", "doctor"]):
        with pytest.raises(SystemExit) as exc_info:
            main_doctor()
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[✗] OVH API reachable" in out
    assert "1 check failed" in out

def test_main_claude_dispatches_doctor():
    with patch("ovh_claude.cli.main_doctor") as mock_doctor, \
         patch("sys.argv", ["ovh-claude", "doctor"]):
        main_claude()
    mock_doctor.assert_called_once()

def test_main_claude_unknown_subcommand_lists_known(capsys):
    with patch("sys.argv", ["ovh-claude", "unknown"]):
        with pytest.raises(SystemExit) as exc_info:
            main_claude()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "install-skill" in err
    assert "doctor" in err
