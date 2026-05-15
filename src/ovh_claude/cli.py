import json
import sys
import shutil
from pathlib import Path
from importlib.resources import files
import ovh
from ovh_claude.credentials import load_credentials, CredentialsError

SKILLS_SOURCE = files("ovh_claude.data").joinpath("ovh-api.md")
SKILLS_DEST_DIR = Path.home() / ".claude" / "skills"

ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE"}


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
    if not args or args[0] != "install-skill":
        print("Usage: ovh-claude install-skill", file=sys.stderr)
        sys.exit(1)

    SKILLS_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = SKILLS_DEST_DIR / "ovh-api.md"
    shutil.copy2(SKILLS_SOURCE, dest)
    print(f"Skill installed: {dest}")
