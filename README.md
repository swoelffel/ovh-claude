# ovh-claude

Secure OVH API proxy + Claude Code skill for AI agents.

Credentials stay in `~/.config/ovh/credentials` — they never appear in the LLM context.

## Install

```bash
pipx install ovh-claude
ovh-claude install-skill
```

## Prerequisites

Create `~/.config/ovh/credentials`:

```ini
[default]
endpoint=ovh-eu
application_key=YOUR_APP_KEY
application_secret=YOUR_APP_SECRET
consumer_key=YOUR_CONSUMER_KEY
```

Generate tokens at https://api.ovh.com/createToken/ with the rights you need.

## Usage

```bash
ovh-api GET /vps
ovh-api GET /vps/vps-xxx.ovh.net
ovh-api POST /domain/zone/example.com/record '{"fieldType":"A","subDomain":"@","target":"1.2.3.4","ttl":300}'
ovh-api DELETE /domain/zone/example.com/record/12345
```

## Claude Code skill

After `ovh-claude install-skill`, the skill `ovh-api` is registered in `~/.claude/skills/`. Claude agents automatically use it for OVH-related tasks.

## Security

- Credentials are read from file — never passed as CLI arguments
- Stdout contains only the API JSON response
- Errors go to stderr without exposing secret values
