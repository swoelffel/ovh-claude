---
name: ovh-api
description: Use when performing any OVH infrastructure operation — VPS management, DNS records, firewall rules, snapshots, billing, or any other OVH API call. Invoked automatically when the task involves mail4ai.eu or any OVH resource.
---

## Usage

Call the `ovh-api` proxy — credentials are read automatically from `~/.config/ovh/credentials`.

```bash
ovh-api <METHOD> <path> [json_body]
```

Methods: `GET`, `POST`, `PUT`, `DELETE`

The response is pretty-printed JSON on stdout. Errors go to stderr with a non-zero exit code.

## Operational pattern

1. **Always GET before POST/DELETE** — confirm the resource exists and note its ID
2. **Report JSON results** to the user for review before mutating actions
3. **Confirm with the user** before any POST, PUT, or DELETE call
4. **Check exit code** — non-zero means the API returned an error (read stderr)

## VPS endpoints

```bash
# List VPS
ovh-api GET /vps

# VPS details
ovh-api GET /vps/vps-xxx.ovh.net

# VPS status
ovh-api GET /vps/vps-xxx.ovh.net/status

# Reboot (confirm with user first)
ovh-api POST /vps/vps-xxx.ovh.net/reboot

# List snapshots
ovh-api GET /vps/vps-xxx.ovh.net/snapshot

# Create snapshot (confirm with user first)
ovh-api POST /vps/vps-xxx.ovh.net/snapshot

# Firewall rules
ovh-api GET /vps/vps-xxx.ovh.net/serviceInfos
```

## DNS endpoints

```bash
# List zones
ovh-api GET /domain/zone

# List records in a zone
ovh-api GET /domain/zone/example.com/record

# Record details
ovh-api GET /domain/zone/example.com/record/12345

# Add A record (confirm with user first)
ovh-api POST /domain/zone/example.com/record '{"fieldType":"A","subDomain":"@","target":"1.2.3.4","ttl":300}'

# Add CNAME record (confirm with user first)
ovh-api POST /domain/zone/example.com/record '{"fieldType":"CNAME","subDomain":"www","target":"example.com.","ttl":300}'

# Add MX record (confirm with user first)
ovh-api POST /domain/zone/example.com/record '{"fieldType":"MX","subDomain":"","target":"mail.example.com.","ttl":300}'

# Delete record (confirm with user first)
ovh-api DELETE /domain/zone/example.com/record/12345

# Refresh zone (apply changes)
ovh-api POST /domain/zone/example.com/refresh
```

## Account & monitoring

```bash
# Account info
ovh-api GET /me

# Active incidents
ovh-api GET /incident

# Support tickets
ovh-api GET /support/tickets

# Ticket details
ovh-api GET /support/tickets/12345
```

## Error handling

- Exit code 0 + JSON on stdout = success
- Exit code 1 + message on stderr = error
  - `Credentials file not found` → verify `~/.config/ovh/credentials` exists
  - `OVH API error: 403 Forbidden` → token lacks required permissions
  - `OVH API error: 404 Not Found` → resource doesn't exist, verify path with a GET first
