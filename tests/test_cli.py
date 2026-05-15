# tests/test_cli.py
import json
import sys
import pytest
from unittest.mock import patch, MagicMock
from ovh_claude.cli import main_proxy, main_claude

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

from ovh_claude.cli import _check_python_version

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
