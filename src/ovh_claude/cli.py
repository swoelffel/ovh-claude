import json
import sys
import ovh
from ovh_claude.credentials import load_credentials, CredentialsError

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
    pass  # implemented in Task 4
