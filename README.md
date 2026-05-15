# ovh-claude

![CI](https://github.com/swoelffel/ovh-claude/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Let Claude Code manage OVHcloud resources safely — API credentials stay local and never enter the LLM context.

- Credentials stay on your machine
- Simple API calls via `ovh-api`
- Claude Code skill installs in one command

## Why this exists

When an AI agent (Claude Code, an autonomous SRE bot, a multi-agent pipeline) needs to act on cloud infrastructure, the naive solution is to give it your API keys — pasted into the prompt, exported as env vars, or baked into the agent's context. Any of these leaks the secret into the model's input.

`ovh-claude` solves this by installing a local CLI (`ovh-api`) that reads your OVHcloud credentials from `~/.config/ovh/credentials` and returns only the JSON the agent needs. The agent calls the CLI; the credentials never appear in any prompt.

## Quickstart

```bash
# 1. Install from PyPI (under 1 min)
pipx install ovh-claude

# 2. Register the Claude Code skill
ovh-claude install-skill

# 3. Verify everything works end-to-end (incl. live API call)
ovh-claude doctor

# 4. First real call
ovh-api GET /me
```

If `doctor` passes, you're done. Total: under 5 minutes including token creation.

## Prerequisites

### Install pipx

[`pipx`](https://pipx.pypa.io/) lets you install Python CLI tools in isolated environments.

| Platform | Command |
|----------|---------|
| macOS (Homebrew) | `brew install pipx && pipx ensurepath` |
| Debian / Ubuntu | `sudo apt install pipx && pipx ensurepath` |
| Fedora | `sudo dnf install pipx && pipx ensurepath` |
| Arch / Manjaro | `sudo pacman -S python-pipx && pipx ensurepath` |
| Windows (Scoop) | `scoop install pipx && pipx ensurepath` |
| Any platform (fallback) | `python -m pip install --user pipx && python -m pipx ensurepath` |

After install, open a new shell (or run `source ~/.zshrc` / `source ~/.bashrc`) so the PATH is refreshed.

### Create the OVH credentials file

Create `~/.config/ovh/credentials` (Windows: `%USERPROFILE%\.config\ovh\credentials`):

```ini
[default]
endpoint=ovh-eu
application_key=YOUR_APP_KEY
application_secret=YOUR_APP_SECRET
consumer_key=YOUR_CONSUMER_KEY
```

Generate tokens at https://api.ovh.com/createToken/ with the rights you need.

## Platform support

| Platform | Status | Notes |
|----------|--------|-------|
| macOS | ✅ Supported (tested) | Tested with pipx |
| Linux | ✅ Supported (tested via CI on Ubuntu) | Verified on Python 3.10/3.11/3.12 in CI |
| WSL (Ubuntu/Debian) | 🟢 Should work, not yet tested | Recommended path for Claude Code on Windows |
| Windows (PowerShell native) | ⚠️ Best-effort, untested | Credentials path: `%USERPROFILE%\.config\ovh\credentials`. JSON body in PowerShell: use single-quote outside, double-quote inside, or read from file. PRs welcome. |

## Usage

```bash
ovh-api GET /vps
ovh-api GET /vps/vps-xxx.ovh.net
ovh-api POST /domain/zone/example.com/record '{"fieldType":"A","subDomain":"@","target":"1.2.3.4","ttl":300}'
ovh-api DELETE /domain/zone/example.com/record/12345
```

## Claude Code skill

After `ovh-claude install-skill`, the skill `ovh-api` is registered in `~/.claude/skills/`. Claude agents automatically use it for OVH-related tasks. The bundled skill enforces operational defaults: GET before POST/DELETE, human confirmation before destructive actions, no secrets in stdout.

## Security model

**What ovh-claude protects:**

- OVH credentials are read from `~/.config/ovh/credentials`, never passed via CLI arguments (no `--api-secret …` flag → no shell history leak)
- Credentials never appear on stdout (only the API JSON response is printed)
- Errors go to stderr with sanitized messages (no secret values)
- The agent's LLM context never sees credentials, only API responses

**What ovh-claude does NOT protect:**

- The agent's *decisions* — if the agent decides to delete a record, `ovh-api DELETE …` will delete it. Keep a human in the loop for destructive actions (the bundled skill enforces this convention but cannot prevent a misuse-prompted call).
- OVH-side authorization — if your consumer key has permission to drop a domain, the proxy will let the agent drop it.
- Local file system access — anyone with read access to `~/.config/ovh/credentials` can use the proxy.

**Best practices:**

- Generate a separate consumer key per environment (dev / staging / prod) at https://api.ovh.com/createToken/
- Scope each token to the minimum API rights needed (e.g. `GET /vps/*` only, no DELETE)
- Set expiry on tokens, rotate periodically
- Never commit the credentials file — `~/.config/ovh/credentials` is outside any repo by design

## Contributing

Issues and PRs welcome — especially platform validation for Linux, WSL, and Windows.

## License

MIT
