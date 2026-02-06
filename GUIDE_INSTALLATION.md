# Guide d'Installation MCP - Antigravity ⇄ Cockpit
## Guide Complet Étape par Étape

**Date**: 2026-02-06  
**Plateforme**: macOS

---

## 📋 Prérequis

Vous devez avoir Python 3.9+ installé sur votre système.

---

## Étape 1: Vérifier Python

### 1.1 Vérifier que Python est installé

```bash
python3 --version
```

**Résultat attendu**: `Python 3.9.x` (ou version supérieure)

Si vous obtenez une erreur, installez Python:
```bash
# Avec Homebrew (recommandé)
brew install python3

# OU téléchargez depuis python.org
```

### 1.2 Vérifier pip3

```bash
pip3 --version
```

**Résultat attendu**: `pip 23.x.x from /usr/local/lib/python3.x/site-packages/pip (python 3.x)`

---

## Étape 2: Installer les Dépendances MCP

### 2.1 Naviguer vers le dossier Cockpit

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
```

### 2.2 Installer le SDK MCP

```bash
pip3 install mcp
```

**⚠️ Note**: Sur macOS, utilisez toujours `pip3` (pas `pip`)

### 2.3 Installer PySide6 (si pas déjà installé)

```bash
pip3 install PySide6
```

### 2.4 Vérifier l'installation

```bash
pip3 list | grep mcp
```

**Résultat attendu**: Vous devriez voir `mcp` dans la liste

---

## Étape 3: Tester le Serveur MCP

### 3.1 Lancer le test de vérification

```bash
python3 tests/verify_mcp_basic.py
```

**Résultat attendu**:
```
============================================================
Cockpit MCP Server Basic Verification
============================================================

Testing: Data Layer
  ✅ Demo project created: Demo
  ✅ Project retrieved: Demo

Testing: Tool Logic
  ✅ post_message works
  ✅ read_state works
  ✅ update_agent_state works
  ✅ Agent persisted correctly
  ✅ request_run works (status=...)
  ✅ get_quotas works

============================================================
Results: 2 passed, 0 failed
============================================================

✅ All basic checks passed!
```

### 3.2 Si le test échoue

**Problème**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
# Réinstaller avec --upgrade
pip3 install --upgrade mcp

# Ou avec --user si problème de permissions
pip3 install --user mcp
```

---

## Étape 4: Configurer Antigravity

### 4.1 Localiser le fichier de configuration Antigravity MCP

Le fichier de configuration se trouve généralement ici:
- `~/.config/antigravity/mcp_config.json`
- `~/Library/Application Support/Antigravity/mcp_config.json`

### 4.2 Créer/modifier la configuration

Ouvrez le fichier de config et ajoutez:

```json
{
  "mcpServers": {
    "cockpit": {
      "command": "python3",
      "args": ["/Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py"],
      "env": {
        "COCKPIT_PROJECT_ID": "demo"
      }
    }
  }
}
```

**📝 Note**: Si vous avez déjà d'autres serveurs MCP configurés, ajoutez simplement la section `"cockpit"` dans `mcpServers`.

### 4.3 Exemple de configuration complète

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    },
    "cockpit": {
      "command": "python3",
      "args": ["/Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py"],
      "env": {
        "COCKPIT_PROJECT_ID": "demo"
      }
    }
  }
}
```

---

## Étape 5: Créer un Projet Cockpit

### 5.1 Vérifier qu'un projet existe

```bash
ls -la /Users/oliviercloutier/Desktop/Cockpit/control/projects/
```

Vous devriez voir un dossier `demo/` (créé automatiquement lors des tests).

### 5.2 Créer un nouveau projet (optionnel)

Pour créer un projet spécifique pour votre travail:

```python
# Dans un script Python ou REPL
import sys
sys.path.insert(0, '/Users/oliviercloutier/Desktop/Cockpit')

from app.data.store import ensure_project_structure

# Créer un projet "motherload"
ensure_project_structure("motherload", "Motherload Project")
```

Ou créez manuellement la structure:
```bash
mkdir -p control/projects/motherload/{agents,chat/threads}
```

---

## Étape 6: Tester l'Intégration End-to-End

### 6.1 Démarrer une conversation Antigravity

1. Ouvrez Antigravity
2. Créez une nouvelle conversation

### 6.2 Tester les outils MCP

Dans votre conversation Antigravity, demandez à l'agent:

**Test 1 - Vérifier les quotas**:
```
Peux-tu vérifier les quotas Cockpit en utilisant l'outil cockpit.get_quotas ?
```

**Test 2 - Mettre à jour ton statut**:
```
Mets à jour ton statut dans Cockpit avec:
- status: "executing"
- progress: 50
- current_phase: "Testing Integration"
```

**Test 3 - Poster un message**:
```
Poste un message dans le chatroom Cockpit pour dire que le test fonctionne!
```

### 6.3 Vérifier dans Cockpit

Vérifiez que les données ont été sauvegardées:

```bash
# Voir les messages postés
cat control/projects/demo/settings.json | python3 -m json.tool | grep -A 10 "messages"

# Voir les agents enregistrés
ls -la control/projects/demo/agents/
```

---

## Étape 7: Utiliser les Outils MCP dans vos Agents

### 7.1 Exemple d'utilisation dans un prompt d'agent

Ajoutez ceci à vos prompts d'agents Antigravity:

```markdown
Tu as accès au système Cockpit via MCP. Utilise ces outils:

1. **cockpit.get_quotas** - Vérifie tes quotas avant des opérations coûteuses
2. **cockpit.update_agent_state** - Mets à jour ta progression toutes les 60s
3. **cockpit.post_message** - Poste des messages pour les événements importants
4. **cockpit.read_state** - Lis l'état du projet et la roadmap
5. **cockpit.request_run** - Demande l'exécution de runs (tests, deploy, etc.)

Exemple de heartbeat:
```python
await use_mcp_tool("cockpit.update_agent_state", {
    "agent_id": "ton_id_agent",
    "project_id": "motherload",
    "status": "executing",
    "heartbeat": True
})
```

Poste uniquement pour:
- Changements de phase importants
- Milestones atteints
- Erreurs/blocages
- Questions pour l'utilisateur

Ne spamme pas le chat avec chaque action!
```

### 7.2 Conventions à respecter

**Agent ID Format**: `ag_{projet}_{role}_{uuid8}`
- Exemple: `ag_motherload_miner_a7f3c12b`

**Tags Standard**:
- `#milestone` - Réalisation majeure
- `#blocker` - Travail bloqué
- `#question` - Besoin d'input utilisateur
- `#test` - Activité de test
- `#deploy` - Déploiement

**Status Values**:
- `idle` - Pas de travail actif
- `planning` - Recherche/conception
- `executing` - Implémentation
- `verifying` - Tests/validation
- `blocked` - Bloqué (attente user/externe)
- `error` - Erreur rencontrée
- `completed` - Tâche terminée

---

## 🔧 Dépannage

### Problème: "command not found: pip"

**Solution**: Utilisez `pip3` au lieu de `pip` sur macOS:
```bash
pip3 install mcp
```

### Problème: "Permission denied"

**Solution**: Installez en mode utilisateur:
```bash
pip3 install --user mcp
```

### Problème: Module MCP introuvable

**Solution**: Vérifiez le chemin Python:
```bash
which python3
pip3 show mcp
```

Si installé mais non trouvé, ajoutez au PATH:
```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

### Problème: Le serveur MCP ne démarre pas

**Solution**: Vérifiez les logs:
```bash
tail -f mcp_server.log
```

### Problème: Agent ne se connecte pas à Cockpit

**Vérifications**:
1. Le chemin dans `mcp_config.json` est-il correct?
2. Le `COCKPIT_PROJECT_ID` existe-t-il?
3. Y a-t-il des erreurs dans les logs Antigravity?

---

## 📚 Ressources

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](file:///Users/oliviercloutier/Desktop/Cockpit/QUICKSTART.md) | Guide de démarrage rapide |
| [control/README.md](file:///Users/oliviercloutier/Desktop/Cockpit/control/README.md) | Documentation complète du serveur MCP |
| [mcp_integration_spec.md](file:///Users/oliviercloutier/.gemini/antigravity/brain/b00d104d-62d7-423d-8534-edde4955adc3/mcp_integration_spec.md) | Spécification technique complète |
| [walkthrough.md](file:///Users/oliviercloutier/.gemini/antigravity/brain/b00d104d-62d7-423d-8534-edde4955adc3/walkthrough.md) | Walkthrough de l'implémentation |

---

## ✅ Checklist de Validation

Avant de considérer l'installation terminée, vérifiez:

- [ ] Python 3.9+ installé (`python3 --version`)
- [ ] pip3 fonctionnel (`pip3 --version`)
- [ ] MCP SDK installé (`pip3 list | grep mcp`)
- [ ] Tests passent (`python3 tests/verify_mcp_basic.py`)
- [ ] Configuration Antigravity créée
- [ ] Test end-to-end réussi (agent → Cockpit)
- [ ] Données visibles dans `control/projects/`

---

## 🎯 Prochain Étapes

Une fois l'installation validée:

1. **Créer votre projet réel**:
   ```python
   ensure_project_structure("votre_projet", "Nom du Projet")
   ```

2. **Configurer vos agents Antigravity** avec les prompts MCP

3. **Construire l'UI Cockpit** pour visualiser:
   - Grille des agents (agents_grid.py)
   - Chatroom (chatroom.py)
   - Roadmap (roadmap.py)

4. **Activer des features avancées**:
   - WebSockets pour updates temps réel
   - UI d'approbation de runs
   - Système de quotas réel
   - Dashboard analytics

---

**Version**: 1.0.0  
**Status**: Prêt pour production 🚀

Besoin d'aide? Consultez les logs dans `mcp_server.log`
