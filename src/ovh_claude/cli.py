import json
import sys
import shutil
from pathlib import Path
from importlib.resources import files
import ovh
from ovh_claude import credentials
from ovh_claude.credentials import load_credentials, CredentialsError

SKILLS_SOURCE = files("ovh_claude.data").joinpath("ovh-api.md")
SKILLS_DEST_DIR = Path.home() / ".claude" / "skills"

ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE"}


def _check_python_version() -> tuple[str, str]:
    version = sys.version_info
    version_str = f"{version[0]}.{version[1]}.{version[2]}"
    if (version[0], version[1]) < (3, 10):
        return "FAIL", f"Python {version_str} (≥ 3.10 required)"
    return "OK", f"Python {version_str} (≥ 3.10 required)"


def _check_credentials_file() -> tuple[str, str]:
    path = credentials.CREDENTIALS_PATH
    if not path.exists():
        return "FAIL", f"Credentials file: {path} (not found)\n    → Create one at https://api.ovh.com/createToken/"
    return "OK", f"Credentials file: {path}"


def _check_credentials_keys() -> tuple[str, str]:
    try:
        loaded = credentials.load_credentials()
    except credentials.CredentialsError as e:
        msg = str(e)
        if "Missing keys" in msg:
            missing_part = msg.split(": ", 2)[-1]
            return "FAIL", f"Required keys missing: {missing_part}"
        return "FAIL", f"Credentials error: {msg.splitlines()[0]}"
    return "OK", f"Required keys: {', '.join(loaded.keys())}"


def _check_skill_installed() -> tuple[str, str]:
    dest = SKILLS_DEST_DIR / "ovh-api.md"
    if not dest.exists():
        return "FAIL", f"Skill not installed at {dest}\n    → Run: ovh-claude install-skill"
    return "OK", f"Skill installed: {dest}"


def _check_api_reachable() -> tuple[str, str]:
    try:
        creds = load_credentials()
    except CredentialsError as e:
        return "FAIL", f"Credentials error: {str(e).splitlines()[0]}"
    try:
        client = ovh.Client(
            endpoint=creds["endpoint"],
            application_key=creds["application_key"],
            application_secret=creds["application_secret"],
            consumer_key=creds["consumer_key"],
        )
        cred = client.get("/auth/currentCredential")
    except ovh.exceptions.APIError as e:
        return "FAIL", f"OVH API error: {e}"
    except Exception as e:
        return "FAIL", f"OVH API unreachable: {type(e).__name__}"
    status = cred.get("status", "<unknown>")
    return "OK", f"OVH API reachable (GET /auth/currentCredential) → status: {status}"


def main_proxy():
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: ovh-api <METHOD> <path> [json_body]", file=sys.stderr)
        sys.exit(1)

    method, path = args[0].upper(), args[1]
    body_raw = args[2] if len(args) > 2 else None

    if method not in ALLOWED_METHODS:
        print(f"Error: method must be one of {', '.join(sorted(ALLOWED_METHODS))}", file=sys.stderr)
        sys.exit(1)

    try:
        creds = load_credentials()
        body = json.loads(body_raw) if body_raw else {}
        client = ovh.Client(
            endpoint=creds["endpoint"],
            application_key=creds["application_key"],
            application_secret=creds["application_secret"],
            consumer_key=creds["consumer_key"],
        )
        fn = getattr(client, method.lower())
        result = fn(path, **body)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except CredentialsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON body — {e}", file=sys.stderr)
        sys.exit(1)
    except ovh.exceptions.APIError as e:
        print(f"OVH API error: {e}", file=sys.stderr)
        sys.exit(1)


def main_claude():
    args = sys.argv[1:]
    if not args:
        print("Usage: ovh-claude <install-skill|doctor>", file=sys.stderr)
        sys.exit(1)

    subcommand = args[0]
    if subcommand == "install-skill":
        _install_skill()
        return
    if subcommand == "doctor":
        main_doctor()
        return

    print(f"Unknown subcommand: {subcommand}", file=sys.stderr)
    print("Available subcommands: install-skill, doctor", file=sys.stderr)
    sys.exit(1)


def _install_skill():
    SKILLS_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = SKILLS_DEST_DIR / "ovh-api.md"
    shutil.copy2(SKILLS_SOURCE, dest)
    print(f"Skill installed: {dest}")


def main_doctor():
    print("ovh-claude doctor")
    print("─────────────────")

    checks = [
        ("python", _check_python_version, ()),
        ("credentials_file", _check_credentials_file, ()),
        ("credentials_keys", _check_credentials_keys, ("credentials_file",)),
        ("skill", _check_skill_installed, ()),
        ("api", _check_api_reachable, ("credentials_file", "credentials_keys")),
    ]

    failures = 0
    results: dict[str, str] = {}
    for name, fn, deps in checks:
        if any(results.get(d) != "OK" for d in deps):
            skipped_dep = next((d for d in deps if results.get(d) != "OK"), deps[0])
            print(f"[ ] {_label_for(name)} (skipped — {_skipped_reason(skipped_dep)})")
            results[name] = "SKIPPED"
            continue
        status, message = fn()
        results[name] = status
        marker = "✓" if status == "OK" else "✗"
        label = _label_for(name)
        if status == "OK":
            print(f"[{marker}] {message}")
        else:
            print(f"[{marker}] {label}: {message}")
            failures += 1

    print()
    if failures == 0:
        print("All checks passed.")
    else:
        print(f"{failures} check{'s' if failures > 1 else ''} failed.")
        sys.exit(1)


def _label_for(name: str) -> str:
    return {
        "python": "Python version",
        "credentials_file": "Credentials file",
        "credentials_keys": "Required keys",
        "skill": "Skill installed",
        "api": "OVH API reachable",
    }[name]


def _skipped_reason(dep: str) -> str:
    return {
        "credentials_file": "credentials missing",
        "credentials_keys": "credentials invalid",
    }.get(dep, "prerequisite failed")
