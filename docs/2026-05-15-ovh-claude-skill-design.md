# ovh-claude-skill — Design spec

**Date** : 2026-05-15  
**Repo cible** : `ovh-claude-skill` (nouveau repo public GitHub, indépendant d'AgentMail)

---

## Objectif

Fournir un proxy CLI sécurisé vers l'API OVH, accompagné d'un skill Claude Code, installables via pip. Les credentials OVH ne transitent jamais dans le contexte LLM — le proxy les lit directement depuis `~/.config/ovh/credentials`.

---

## Architecture

### Repo structure

```
ovh-claude-skill/
  src/ovh_claude/
    __init__.py
    cli.py           # entry points : ovh-api + ovh-claude
    credentials.py   # lecture ~/.config/ovh/credentials
  skills/
    ovh-api.md       # skill Claude Code
  pyproject.toml
  README.md
```

### Deux commandes installées par pip

| Commande | Rôle |
|----------|------|
| `ovh-api <METHOD> <path> [json_body]` | Proxy vers l'API OVH |
| `ovh-claude install-skill` | Copie `skills/ovh-api.md` dans `~/.claude/skills/` |

---

## Composants

### 1. `credentials.py`

Lit le fichier INI standard OVH `~/.config/ovh/credentials` :

```ini
[default]
endpoint=ovh-eu
application_key=...
application_secret=...
consumer_key=...
```

Lève une erreur claire si le fichier est absent ou incomplet. Ne log jamais les valeurs.

### 2. `cli.py` — commande `ovh-api`

**Interface :**
```bash
ovh-api GET /vps
ovh-api GET /vps/vps-xxx.ovh.net
ovh-api POST /domain/zone/example.com/record '{"fieldType":"A","subDomain":"@","target":"1.2.3.4","ttl":300}'
ovh-api DELETE /domain/zone/example.com/record/12345
```

**Flux interne :**
1. Parse `METHOD`, `path`, `body` (JSON optionnel) depuis argv
2. Lit les credentials via `credentials.py`
3. Instancie `ovh.Client` (SDK officiel OVH)
4. Appelle `client.call(method, path, **body)`
5. Affiche le JSON pretty-printed sur stdout
6. En cas d'erreur : message sur stderr, exit code non-zero

Les credentials ne transitent jamais par stdout.

### 3. `cli.py` — commande `ovh-claude install-skill`

Copie `skills/ovh-api.md` (bundlé dans le package pip) vers `~/.claude/skills/ovh-api.md`. Crée le répertoire si absent. Affiche confirmation.

### 4. `skills/ovh-api.md`

Skill Claude Code déclenché sur les tâches OVH. Contient :

- **Usage** : comment appeler `ovh-api METHOD path [body]`
- **Endpoints VPS** : list, status, reboot, snapshot, firewall rules
- **Endpoints DNS** : list zones, list/add/delete records, refresh zone
- **Endpoints monitoring** : `/me`, `/incident`, `/support/tickets`
- **Pattern opérationnel** : toujours GET avant POST/DELETE, reporter les résultats JSON, confirmer les actions destructives avec l'utilisateur
- **Gestion erreurs** : lire stderr + exit code non-zero

---

## Dépendances

| Package | Rôle |
|---------|------|
| `ovh` | SDK officiel OVH (signature SHA1, auth, retries) |

Python ≥ 3.10. Aucune autre dépendance externe.

---

## Installation

```bash
pipx install ovh-claude-skill   # installe ovh-api + ovh-claude
ovh-claude install-skill         # enregistre le skill dans ~/.claude/skills/
```

Pré-requis : `~/.config/ovh/credentials` existant (généré via https://api.ovh.com/createToken/).

---

## Sécurité

- Credentials lus depuis le fichier — jamais passés en argument CLI (pas de `--secret`)
- Stdout contient uniquement la réponse API JSON
- Stderr pour les erreurs (message sans valeur secrète)
- Pas de logging fichier par défaut

---

## Hors scope

- Interface web ou GUI
- Cache des réponses API
- Gestion multi-compte (un seul profil `[default]`)
- Wrapping haut niveau des endpoints (l'agent utilise les paths bruts)
