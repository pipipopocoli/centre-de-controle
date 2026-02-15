# 🏗️ Projet Cockpit V2 — Spécification Technique Complète

> **Document de référence pour Clems (Orchestrator L0)**
> **Auteur :** Léo (Agent L1 — Recherche & Architecture)
> **Date :** 2026-02-13
> **Statut :** Validé par Olivier — Prêt pour implémentation

---

## Table des Matières

1. [Contexte & Justification](#1-contexte--justification)
2. [Architecture Cible V2](#2-architecture-cible-v2)
3. [Plugin 1 : Agent Registry & Hiérarchie](#3-plugin-1--agent-registry--hiérarchie)
4. [Plugin 2 : SOUL.md & Skills Dynamiques](#4-plugin-2--soulmd--skills-dynamiques)
5. [Plugin 3 : Task Manager Simplifié](#5-plugin-3--task-manager-simplifié)
6. [Plugin 4 : Platform Router (Multi-Runtime)](#6-plugin-4--platform-router-multi-runtime)
7. [Plugin 5 : Mémoire Progressive (FTS → Vector)](#7-plugin-5--mémoire-progressive-fts--vector)
8. [Prérequis Hardware & Infrastructure](#8-prérequis-hardware--infrastructure)
9. [Dépendances Logicielles](#9-dépendances-logicielles)
10. [Roadmap & Tâches Détaillées](#10-roadmap--tâches-détaillées)
11. [Risques & Mitigations](#11-risques--mitigations)

---

## 1. Contexte & Justification

### 1.1 Pourquoi ce projet ?

Cockpit V1 a atteint ses limites structurelles. Voici les **5 murs** identifiés lors de la recherche R1 :

| # | Mur | Preuve dans le code | Impact |
|---|-----|---------------------|--------|
| 1 | **Agents hardcodés** | `auto_mode.py:296-309` — `_agent_platform()` est un if/else statique | Impossible d'ajouter un agent sans modifier Python |
| 2 | **Pas de mémoire cross-projet** | `brainfs.py:63-71` — `load_profile()` lit UN profil par projet | Un agent ne se souvient de rien d'un projet à l'autre |
| 3 | **Skills décoratives** | `brainfs.py:19-31` — `load_skills()` lit un JSON statique jamais injecté | Les "compétences" ne changent rien au comportement |
| 4 | **Dispatch fragile** | `auto_mode.py:458-489` — `dispatch_once()` traite 1 requête à la fois, synchrone | Si Cockpit crash pendant un dispatch, la requête est perdue |
| 5 | **Single runtime** | `auto_mode.py:296` — 5/7 agents sur Codex | Si Codex est down, 80% de l'équipe est paralysée |

### 1.2 Objectif V2

Transformer Cockpit d'une **boîte à outils** (agents éphémères, mémoire jetable) en un **organisme** (agents hiérarchisés, mémoire persistante, compétences dynamiques).

### 1.3 Ce qui ne change PAS

- L'UI reste en **Qt/Python** (pas de migration web).
- Le filesystem reste le **storage primaire** (pas de base SQL pour les projets).
- L'humain reste **dans la boucle** (pas d'autonomie totale).
- Le design reste **Paper Ops** (propre, sobre, professionnel).

---

## 2. Architecture Cible V2

### 2.1 Schéma Général

```
┌──────────────────────────────────────────────────────────────────┐
│                        COCKPIT V2                                │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Qt Desktop  │  │  Task Manager │  │   Org Chart (Vue)      │  │
│  │  (UI Layer)  │  │  (Dashboard)  │  │   (Hiérarchie L0-L2)  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬───────────┘  │
│         │                 │                        │              │
│  ───────┴─────────────────┴────────────────────────┴──────────   │
│                     SERVICE LAYER                                │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Agent Registry │  │ Platform     │  │ Memory Engine        │  │
│  │ (agents.json)  │  │ Router       │  │ (FTS5 → ChromaDB)    │  │
│  └────────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│           │                 │                      │              │
│  ┌────────┴───────┐  ┌─────┴────────┐  ┌──────────┴───────────┐  │
│  │ SOUL.md        │  │ Codex Runner │  │ brainfs/memory/      │  │
│  │ Skills Library │  │ AG Runner    │  │   ├── index.db       │  │
│  │ brainfs/       │  │ Gemini Runner│  │   ├── vectors.db     │  │
│  │  ├── souls/    │  │ Ollama Runner│  │   └── patterns.json  │  │
│  │  ├── skills/   │  └──────────────┘  └──────────────────────┘  │
│  │  └── library/  │                                              │
│  └────────────────┘                                              │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Flux de données

```
Olivier → [Chat] → Clems (L0)
                      │
                      ├─→ Victor (L1) ──→ Agent-1 (L2, Codex)
                      │                 ├→ Agent-3 (L2, Codex)
                      │                 └→ Agent-5 (L2, Ollama)
                      │
                      └─→ Léo (L1) ────→ Agent-2 (L2, Antigravity)
                                        └→ Agent-4 (L2, Gemini)
```

---

## 3. Plugin 1 : Agent Registry & Hiérarchie

### 3.1 Pourquoi ?

Aujourd'hui, ajouter "Agent-6" nécessite de :
1. Modifier `_agent_platform()` dans `auto_mode.py` (code Python).
2. Créer manuellement `agents/agent-6/state.json`.
3. Espérer que le dispatch le reconnaisse.

C'est **fragile**, **non-scalable**, et **non-documenté**.

### 3.2 Ce qu'on construit

Un fichier central `brainfs/agents_registry.json` qui est la **source de vérité** pour tous les agents.

#### Structure du fichier

```json
{
  "schema_version": 1,
  "agents": {
    "clems": {
      "level": 0,
      "role": "Orchestrator",
      "platform": "antigravity",
      "fallback_platform": "codex",
      "manages": ["victor", "leo"],
      "skills": ["project-management", "delegation", "risk-assessment"],
      "soul_path": "brainfs/souls/clems.md",
      "max_concurrent_tasks": 3,
      "status": "active"
    },
    "victor": {
      "level": 1,
      "role": "Backend Engineering Lead",
      "platform": "codex",
      "fallback_platform": "antigravity",
      "manages": ["agent-1", "agent-3", "agent-5"],
      "skills": ["python-expert", "testing-pytest", "git-workflow", "code-review"],
      "soul_path": "brainfs/souls/victor.md",
      "max_concurrent_tasks": 2,
      "status": "active"
    },
    "leo": {
      "level": 1,
      "role": "UI/UX Architecture Lead",
      "platform": "antigravity",
      "fallback_platform": null,
      "manages": ["agent-2", "agent-4"],
      "skills": ["qt-styling", "ux-audit", "accessibility-check"],
      "soul_path": "brainfs/souls/leo.md",
      "max_concurrent_tasks": 2,
      "status": "active"
    },
    "agent-1": {
      "level": 2,
      "role": "Python Backend Worker",
      "platform": "codex",
      "fallback_platform": "ollama",
      "manages": [],
      "skills": ["python-expert"],
      "soul_path": null,
      "max_concurrent_tasks": 1,
      "status": "standby"
    }
  }
}
```

### 3.3 Fichiers à modifier

| Fichier | Action | Détail |
|---------|--------|--------|
| `brainfs/agents_registry.json` | **CRÉER** | Source de vérité pour tous les agents |
| `app/services/brainfs.py` | **MODIFIER** | Ajouter `load_agent_registry()` et `get_agent(agent_id)` |
| `app/services/auto_mode.py` | **MODIFIER** | `_agent_platform()` → lookup dans le registry au lieu du if/else |
| `app/data/model.py` | **MODIFIER** | Ajouter `level: int`, `parent_id: str | None`, `manages: list[str]` à `AgentState` |
| `app/ui/agents_grid.py` | **MODIFIER** | Grouper les cartes par niveau (accordion ou sections) |

### 3.4 Tâches détaillées

| # | Tâche | Assigné | Effort | Dépendances |
|---|-------|---------|--------|-------------|
| 1.1 | Créer `brainfs/agents_registry.json` avec les 5 agents initiaux | Victor | 1h | Aucune |
| 1.2 | Ajouter `load_agent_registry()` à `brainfs.py` | Victor | 2h | 1.1 |
| 1.3 | Refactorer `_agent_platform()` pour lire le registry | Victor | 3h | 1.2 |
| 1.4 | Ajouter champs `level`, `parent_id`, `manages` à `AgentState` | Victor | 1h | Aucune |
| 1.5 | Modifier `agents_grid.py` pour grouper par niveau | Léo | 4h | 1.4 |
| 1.6 | Tests unitaires pour le registry | Victor | 2h | 1.2, 1.3 |

**Total estimé : 13 heures**

---

## 4. Plugin 2 : SOUL.md & Skills Dynamiques

### 4.1 Pourquoi ?

Le fichier `brainfs/skills/skills.json` contient 5 entrées statiques :
```json
{"id": "python", "name": "Python", "description": "Analyze Python projects..."}
```

Ce sont des **étiquettes**, pas des compétences. Elles ne changent rien au comportement de l'agent. Un agent avec le skill "Python" ne code pas mieux qu'un agent sans.

### 4.2 Ce qu'on construit

#### A) SOUL.md (Identité Agent)

Un fichier Markdown par agent qui définit **qui il est**.

```markdown
# Victor — Backend Engineering Lead

## Identité
Tu es Victor. Tu es un ingénieur backend senior obsédé par la qualité du code.
Tu ne livres jamais de code sans tests. Tu détestes les hacks et les raccourcis.

## Règles
1. Toujours écrire un test AVANT de modifier du code.
2. Jamais de `# TODO` sans issue associée.
3. Rapporter les blockers à Clems en moins de 30 minutes.
4. Documenter toute décision architecturale dans DECISIONS.md.

## Ton
- Professionnel mais direct.
- Tu expliques le "pourquoi", pas juste le "quoi".

## Mémoire Persistante
- Tu te souviens des patterns récurrents (ex: "store.py a des problèmes de permission").
- Tu notes les leçons apprises dans brainfs/memory/patterns.json.
```

#### B) Skill Library (Compétences Téléchargeables)

Structure de `brainfs/library/` :
```
brainfs/library/
├── python-expert/
│   ├── SKILL.md          ← Instructions pour l'agent
│   ├── scripts/
│   │   └── lint_check.sh ← Outils automatiques
│   └── resources/
│       └── patterns.md   ← Patterns connus
├── qt-styling/
│   ├── SKILL.md
│   └── resources/
│       ├── color_palette.json
│       └── component_library.md
└── testing-pytest/
    ├── SKILL.md
    └── scripts/
        └── run_coverage.sh
```

Chaque `SKILL.md` suit le standard ouvert (compatible Claude Code, Copilot, Gemini CLI) :
```yaml
---
name: python-expert
version: 1.0.0
description: Advanced Python development patterns and best practices
compatible_agents: [victor, agent-1, agent-3]
---

# Python Expert Skill

## Instructions
Quand tu travailles sur du code Python :
1. Utilise `pathlib` au lieu de `os.path`.
2. Utilise `dataclasses` ou `pydantic` pour les modèles.
3. Type hints OBLIGATOIRES sur toutes les fonctions publiques.
...
```

### 4.3 Comment ça s'intègre (Loader de Skills)

Quand l'auto-mode dispatche une tâche à un agent :

```
1. Lire agents_registry.json → agent.skills = ["python-expert", "testing-pytest"]
2. Pour chaque skill_id dans agent.skills :
     a. Lire brainfs/library/{skill_id}/SKILL.md
     b. Extraire les instructions
3. Injecter les instructions dans le prompt de l'agent
4. Envoyer le tout au runtime (Codex/AG/Gemini)
```

Le **résultat** : l'agent "reçoit" ses compétences au moment du dispatch. Il n'est plus générique.

### 4.4 Fichiers à modifier

| Fichier | Action | Détail |
|---------|--------|--------|
| `brainfs/souls/` | **CRÉER** (dossier) | Un `.md` par agent nommé (clems, victor, leo) |
| `brainfs/library/` | **CRÉER** (dossier) | Un sous-dossier par skill avec `SKILL.md` |
| `app/services/brainfs.py` | **MODIFIER** | Ajouter `load_soul(agent_id)` et `load_skills_for_agent(agent_id)` |
| `app/services/auto_mode.py` | **MODIFIER** | `format_prompt()` → injecter SOUL + Skills dans le prompt |

### 4.5 Tâches détaillées

| # | Tâche | Assigné | Effort | Dépendances |
|---|-------|---------|--------|-------------|
| 2.1 | Écrire `brainfs/souls/clems.md` | Léo | 1h | Aucune |
| 2.2 | Écrire `brainfs/souls/victor.md` | Léo | 1h | Aucune |
| 2.3 | Écrire `brainfs/souls/leo.md` | Léo | 1h | Aucune |
| 2.4 | Créer `brainfs/library/python-expert/SKILL.md` | Victor | 2h | Aucune |
| 2.5 | Créer `brainfs/library/qt-styling/SKILL.md` | Léo | 2h | Aucune |
| 2.6 | Créer `brainfs/library/testing-pytest/SKILL.md` | Victor | 1h | Aucune |
| 2.7 | Implémenter `load_soul()` dans `brainfs.py` | Victor | 1h | 2.1-2.3 |
| 2.8 | Implémenter `load_skills_for_agent()` dans `brainfs.py` | Victor | 2h | 2.4-2.6 |
| 2.9 | Modifier `format_prompt()` pour injecter SOUL + Skills | Victor | 3h | 2.7, 2.8, 1.2 |
| 2.10 | Tests unitaires pour le skill loader | Victor | 2h | 2.8 |

**Total estimé : 16 heures**

---

## 5. Plugin 3 : Task Manager Simplifié

### 5.1 Pourquoi ?

Quand l'auto-mode tourne, c'est une **boîte noire**. L'opérateur (Olivier) ne voit rien :
- Qui travaille ?
- Qui est bloqué ?
- Combien de tâches ont été terminées ?

Les données **existent déjà** dans `auto_mode_state.json` (compteurs, statuts, timestamps). Elles ne sont juste pas affichées.

### 5.2 Ce qu'on construit

Un nouveau widget Qt dans le dashboard qui affiche :

| Colonne | Source de données |
|---------|-------------------|
| **Agent** | `agents_registry.json → agent_id` |
| **Statut** | `state.json → status` mappé : `active` → "🟢 En Mission", `idle` → "⚪ Au Repos", `blocked` → "🟡 En Attente" |
| **Mission** | `state.json → current_task` (texte court) |
| **Depuis** | `state.json → hearbeat` (delta temps) |
| **Niveau** | `agents_registry.json → level` |

**Pas de tokens. Pas de coûts.** (Phase 3 si nécessaire.)

### 5.3 Terminologie officielle

| Ancien terme | Nouveau terme | Signification |
|-------------|---------------|---------------|
| Active | **En Mission** | L'agent exécute une tâche |
| Idle | **Au Repos** | L'agent est disponible |
| Standby | **En Attente** | L'agent attend une info ou une validation |
| Error | **Bloqué** | L'agent a rencontré une erreur |

### 5.4 Fichiers à modifier

| Fichier | Action | Détail |
|---------|--------|--------|
| `app/ui/task_manager.py` | **CRÉER** | Widget `QTableWidget` avec les 5 colonnes |
| `app/ui/sidebar.py` | **MODIFIER** | Ajouter entrée "Mission Control" dans la navigation |
| `app/main.py` | **MODIFIER** | Intégrer le nouveau widget dans le `QStackedWidget` central |

### 5.5 Tâches détaillées

| # | Tâche | Assigné | Effort | Dépendances |
|---|-------|---------|--------|-------------|
| 3.1 | Créer `task_manager.py` (widget + colonnes) | Léo | 4h | 1.1 (registry) |
| 3.2 | Connecter au `QTimer` de refresh (5s) | Victor | 1h | 3.1 |
| 3.3 | Ajouter dans la sidebar + stack principal | Léo | 2h | 3.1 |
| 3.4 | Styliser (Paper Ops) | Léo | 2h | 3.1 |
| 3.5 | Test manuel : lancer auto-mode et vérifier le refresh | Léo | 1h | 3.1-3.4 |

**Total estimé : 10 heures**

---

## 6. Plugin 4 : Platform Router (Multi-Runtime)

### 6.1 Pourquoi ?

```python
# auto_mode.py — Le mapping actuel
def _agent_platform(agent_id: str) -> str:
    if agent_id == "leo":     return "antigravity"
    if agent_id == "victor":  return "codex"
    ...
    return "codex"  # DEFAULT = tout va chez Codex
```

Résultat : **5 agents sur 7 dépendent de Codex**. Si Codex est lent, ou a une panne quotidienne, ou tombe en maintenance, 80% de l'équipe est bloquée.

### 6.2 Ce qu'on construit

Une couche d'abstraction `PlatformRouter` qui :
1. Lit la `platform` et `fallback_platform` dans le registry.
2. Tente d'envoyer au platform primaire.
3. Si échec → tente le fallback.
4. Si tout échoue → met la requête en "retry queue".

#### Interface abstraite

```python
class RuntimeProvider:
    """Interface commune pour tous les runtimes."""
    
    def dispatch(self, agent_id: str, prompt: str) -> DispatchResult:
        raise NotImplementedError
    
    def is_available(self) -> bool:
        raise NotImplementedError

class CodexProvider(RuntimeProvider): ...
class AntigravityProvider(RuntimeProvider): ...
class GeminiProvider(RuntimeProvider): ...
class OllamaProvider(RuntimeProvider): ...
```

### 6.3 Fichiers à modifier

| Fichier | Action | Détail |
|---------|--------|--------|
| `app/services/platform_router.py` | **CRÉER** | `PlatformRouter` + `RuntimeProvider` interface |
| `app/services/providers/codex.py` | **CRÉER** | Wrapper Codex existant |
| `app/services/providers/antigravity.py` | **CRÉER** | Wrapper AG existant |
| `app/services/providers/ollama.py` | **CRÉER** | Nouveau : appels API locale Ollama |
| `app/services/auto_mode.py` | **MODIFIER** | Remplacer `_agent_platform()` par `PlatformRouter.dispatch()` |

### 6.4 Tâches détaillées

| # | Tâche | Assigné | Effort | Dépendances |
|---|-------|---------|--------|-------------|
| 4.1 | Définir l'interface `RuntimeProvider` | Victor | 2h | Aucune |
| 4.2 | Implémenter `CodexProvider` (refactoring du code existant) | Victor | 3h | 4.1 |
| 4.3 | Implémenter `AntigravityProvider` | Victor | 2h | 4.1 |
| 4.4 | Implémenter `OllamaProvider` (optionnel Phase 2) | Victor | 4h | 4.1 |
| 4.5 | Implémenter `PlatformRouter` avec fallback logic | Victor | 3h | 4.2, 4.3 |
| 4.6 | Refactorer `auto_mode.py` pour utiliser le Router | Victor | 4h | 4.5, 1.3 |
| 4.7 | Tests unitaires avec mocks | Victor | 3h | 4.5 |

**Total estimé : 21 heures**

---

## 7. Plugin 5 : Mémoire Progressive (FTS → Vector)

### 7.1 Pourquoi ?

Aujourd'hui, la "mémoire" d'un agent est : le chat courant + `STATE.md`. Quand la session finit, tout est perdu. Pas de recherche, pas de patterns, pas d'apprentissage.

### 7.2 Ce qu'on construit (en 2 étapes)

#### Étape A — SQLite FTS5 (Court terme, Phase 1)

**Quoi :** Un fichier SQLite par projet qui indexe tous les messages du chat, les issues, et les décisions.

```sql
-- brainfs/memory/index.db
CREATE VIRTUAL TABLE memory_fts USING fts5(
    project_id,
    agent_id,
    content,
    source,       -- 'chat', 'issue', 'decision', 'pattern'
    created_at
);
```

**Avantages :**
- 0 dépendance externe (SQLite est dans la stdlib Python).
- Recherche par mots-clés instantanée.
- ~5 lignes de code pour indexer, ~3 pour chercher.

#### Étape B — ChromaDB Vector Store (Moyen terme, Phase 3)

**Quoi :** Un vector store local qui indexe les embeddings de tous les documents.

```python
import chromadb

# Initialisation (1 fois)
client = chromadb.PersistentClient(path="brainfs/memory/vectors")
collection = client.create_collection("cockpit_memory")

# Indexation (à chaque nouveau message)
collection.add(
    documents=["Le bug de permission dans store.py a été causé par..."],
    metadatas=[{"agent": "victor", "project": "cockpit", "type": "decision"}],
    ids=["msg-2026-02-13-001"]
)

# Recherche sémantique
results = collection.query(
    query_texts=["Comment résoudre les problèmes d'accès fichier ?"],
    n_results=3
)
```

### 7.3 Fichiers à modifier

| Fichier | Action | Détail |
|---------|--------|--------|
| `brainfs/memory/` | **CRÉER** (dossier) | Stockage des fichiers DB |
| `app/services/memory_engine.py` | **CRÉER** | `MemoryEngine` avec `index()`, `search()`, `learn_pattern()` |
| `app/services/auto_mode.py` | **MODIFIER** | Après chaque dispatch réussi, indexer le prompt + résultat |
| `app/data/store.py` | **MODIFIER** | Hook `append_chat_message()` pour indexer automatiquement |

### 7.4 Tâches détaillées

| # | Tâche | Assigné | Effort | Dépendances |
|---|-------|---------|--------|-------------|
| 5.1 | Créer `memory_engine.py` avec SQLite FTS5 | Victor | 4h | Aucune |
| 5.2 | Hook dans `store.py` pour indexation auto | Victor | 2h | 5.1 |
| 5.3 | Hook dans `auto_mode.py` pour indexation post-dispatch | Victor | 2h | 5.1 |
| 5.4 | Commande CLI `cockpit search "query"` | Victor | 2h | 5.1 |
| 5.5 | Tests unitaires pour le memory engine | Victor | 2h | 5.1 |
| 5.6 | (Phase 3) Ajouter ChromaDB en remplacement/complément | Victor | 8h | 5.1 |

**Total estimé : 12h (Phase 1) + 8h (Phase 3)**

---

## 8. Prérequis Hardware & Infrastructure

### 8.1 Configuration Minimale (Mode Local — Ce qu'Olivier a probablement)

| Composant | Minimum | Recommandé | Rôle |
|-----------|---------|------------|------|
| **CPU** | Apple M1 (ou Intel i5 10e gen) | Apple M2 Pro / M3 | Exécution de l'app Qt + SQLite FTS |
| **RAM** | 8 GB | 16 GB | Qt + 3 agents Codex simultanés |
| **Stockage** | 10 GB libres | 50 GB SSD | Projets + brainfs + memory DB |
| **OS** | macOS 13+ | macOS 14+ | Compatibilité Qt + Codex |
| **Réseau** | Connexion stable | Fibre | Appels API Codex/AG/Gemini |

> **Verdict :** Un MacBook Pro M1/M2 avec 16 GB de RAM suffit pour TOUT sauf le Vector Store lourd (ChromaDB + embeddings).

### 8.2 Si on veut Ollama (Modèle IA local)

| Composant | Minimum | Recommandé | Rôle |
|-----------|---------|------------|------|
| **GPU** | Apple M1 (GPU intégré) | Apple M2 Ultra / NVIDIA RTX 4070 | Inférence LLM locale |
| **RAM** | 16 GB unifiée | 32 GB unifiée (ou 16 GB VRAM) | Chargement du modèle en mémoire |
| **Stockage** | + 5 GB (modèle 7B) | + 20 GB (modèle 13B) | Stockage du modèle |

**Modèles recommandés pour Ollama :**

| Modèle | Taille | RAM requise | Qualité | Vitesse |
|--------|--------|-------------|---------|---------|
| `llama3.2:3b` | 2 GB | 4 GB | ⭐⭐ | ⚡⚡⚡ |
| `llama3.2:7b` | 4 GB | 8 GB | ⭐⭐⭐ | ⚡⚡ |
| `codellama:13b` | 7 GB | 16 GB | ⭐⭐⭐⭐ | ⚡ |
| `deepseek-coder:6.7b` | 4 GB | 8 GB | ⭐⭐⭐⭐ (code) | ⚡⚡ |

> **Verdict :** Avec un Mac M2 16 GB, on peut faire tourner `llama3.2:7b` pour les tâches simples (summaries, formatting) et garder Codex/Claude pour le code complexe.

### 8.3 Si on veut ChromaDB + Embeddings

| Composant | Minimum | Recommandé | Rôle |
|-----------|---------|------------|------|
| **RAM** | + 500 MB | + 1 GB | Modèle d'embedding en mémoire |
| **Stockage** | + 200 MB (modèle) | + 500 MB | Modèle `all-MiniLM-L6-v2` |
| **CPU** | Apple M1 | Apple M2 | Calcul des embeddings (pas de GPU nécessaire pour ce modèle) |

> **Verdict :** Très léger. Ça tourne sur n'importe quel Mac récent.

### 8.4 Serveur Privé — Est-ce nécessaire ?

**Réponse : NON, pas pour l'instant.**

Un serveur privé (VPS, dedicated) serait utile si :
- On veut faire tourner les agents **24/7** sans avoir le Mac allumé.
- On veut un modèle LLM local **très gros** (70B+).
- On veut héberger ChromaDB comme un service partagé entre plusieurs machines.

**Si on décide d'en prendre un (plus tard) :**

| Type | Fournisseur | Spécifications | Prix/mois | Cas d'usage |
|------|-------------|----------------|-----------|-------------|
| **VPS simple** | Hetzner / OVH | 4 vCPU, 16 GB RAM, 100 GB SSD | ~20-30 €/mois | Cron jobs, mémoire centralisée |
| **GPU Cloud** | Lambda Labs / Vast.ai | 1x RTX 4090, 24 GB VRAM, 64 GB RAM | ~100-300 €/mois | LLM local gros (70B), training |
| **Mac Mini M4** (self-hosted) | Apple | M4, 24 GB unifiée, 512 GB SSD | ~800 € (achat) | LLM local performant, 0 coût récurrent |

> **Ma recommandation :** Si tu veux un serveur, achète un **Mac Mini M4 24 GB**. C'est un one-time cost, ça fait tourner Ollama + ChromaDB + Cockpit 24/7, et c'est silencieux.

---

## 9. Dépendances Logicielles

### Phase 1 (Aucune nouvelle dépendance)

| Package | Version | Installé ? | Rôle |
|---------|---------|------------|------|
| Python | 3.10+ | ✅ | Runtime |
| PySide6 / PyQt6 | 6.x | ✅ | UI |
| SQLite | 3.35+ (FTS5) | ✅ (stdlib) | Mémoire Phase 1 |

### Phase 2 (Optionnelles)

| Package | Version | Taille | Rôle |
|---------|---------|--------|------|
| `chromadb` | 0.5+ | ~50 MB | Vector Store |
| `sentence-transformers` | 2.x | ~200 MB | Modèle d'embedding |
| `ollama` (CLI) | 0.3+ | ~50 MB + modèle | LLM local |

### Phase 3 (Optionnelles)

| Package | Version | Taille | Rôle |
|---------|---------|--------|------|
| `networkx` | 3.x | ~5 MB | Graphe de connaissances |
| `google-generativeai` | latest | ~10 MB | Gemini Provider |

---

## 10. Roadmap & Tâches Détaillées

### Phase 1 — Fondations (Semaines 1-2)

**Objectif :** Agents identifiés, compétents, et visibles.

| # | Tâche | Plugin | Assigné | Effort | Priorité |
|---|-------|--------|---------|--------|----------|
| 1.1 | Créer `agents_registry.json` | P1 | Victor | 1h | 🔴 |
| 1.2 | Écrire 3x `SOUL.md` (Clems, Victor, Léo) | P2 | Léo | 3h | 🔴 |
| 1.3 | Créer `brainfs/library/` + 3 skills de base | P2 | Victor + Léo | 5h | 🔴 |
| 1.4 | `load_agent_registry()` dans `brainfs.py` | P1 | Victor | 2h | 🔴 |
| 1.5 | Refactorer `_agent_platform()` | P1 | Victor | 3h | 🔴 |
| 1.6 | `load_soul()` + `load_skills_for_agent()` | P2 | Victor | 3h | 🟡 |
| 1.7 | Modifier `format_prompt()` | P2 | Victor | 3h | 🟡 |
| 1.8 | Task Manager widget (MVP) | P3 | Léo | 6h | 🟡 |
| 1.9 | Tests unitaires (registry + skills) | P1+P2 | Victor | 4h | 🟡 |

**Total Phase 1 : ~30 heures**

### Phase 2 — Intelligence (Semaines 3-6)

**Objectif :** Mémoire persistante, routage intelligent.

| # | Tâche | Plugin | Assigné | Effort | Priorité |
|---|-------|--------|---------|--------|----------|
| 2.1 | `memory_engine.py` (SQLite FTS5) | P5 | Victor | 4h | 🔴 |
| 2.2 | Hooks d'indexation (store.py + auto_mode) | P5 | Victor | 4h | 🔴 |
| 2.3 | `PlatformRouter` + `RuntimeProvider` interface | P4 | Victor | 5h | 🟡 |
| 2.4 | `CodexProvider` + `AntigravityProvider` | P4 | Victor | 5h | 🟡 |
| 2.5 | Refactorer `auto_mode.py` → Router | P4 | Victor | 4h | 🟡 |
| 2.6 | `AgentState` enrichi (level, parent_id) | P1 | Victor | 1h | 🟡 |
| 2.7 | Org Chart widget (lecture registry) | P3 | Léo | 4h | 🟡 |
| 2.8 | Tests intégration (Router + Memory) | P4+P5 | Victor | 4h | 🟡 |

**Total Phase 2 : ~31 heures**

### Phase 3 — Puissance (Mois 2-3)

**Objectif :** Vector Store, LLM local, coûts.

| # | Tâche | Plugin | Assigné | Effort | Priorité |
|---|-------|--------|---------|--------|----------|
| 3.1 | ChromaDB intégration | P5 | Victor | 8h | 🟡 |
| 3.2 | `OllamaProvider` | P4 | Victor | 4h | 🟡 |
| 3.3 | `GeminiProvider` | P4 | Victor | 4h | 🟡 |
| 3.4 | Token/Cost tracking | P3 | Victor | 6h | ⚪ |
| 3.5 | Skill installer depuis GitHub | P2 | Victor | 4h | ⚪ |
| 3.6 | Pattern learning (meta-mémoire) | P5 | Victor | 8h | ⚪ |

**Total Phase 3 : ~34 heures**

### Résumé Global

| Phase | Durée | Effort | Résultat |
|-------|-------|--------|----------|
| Phase 1 | 2 semaines | ~30h | Agents identifiés, Skills, Task Manager MVP |
| Phase 2 | 4 semaines | ~31h | Mémoire FTS, Platform Router, Org Chart |
| Phase 3 | 8 semaines | ~34h | Vector Store, LLM local, Coûts |
| **Total** | **~3 mois** | **~95h** | **Cockpit V2 complet** |

---

## 11. Risques & Mitigations

| # | Risque | Probabilité | Impact | Mitigation |
|---|--------|-------------|--------|------------|
| 1 | **Permissions macOS** empêchent l'écriture dans `brainfs/memory/` | Élevée | 🔴 | Stocker dans le dossier projet (pas App Support) |
| 2 | **ChromaDB** trop lourd pour un laptop | Faible | 🟡 | SQLite FTS5 comme plan B permanent |
| 3 | **Ollama** consomme trop de RAM | Moyenne | 🟡 | Utiliser modèles <7B, décharger après usage |
| 4 | **Prompt trop long** (SOUL + Skills + Context) | Moyenne | 🔴 | Budget token par section, compression intelligente |
| 5 | **Migration auto_mode.py** casse le dispatch existant | Élevée | 🔴 | Feature flags, rollback path, tests avant merge |
| 6 | **Codex rate limiting** avec plus d'agents | Moyenne | 🟡 | Platform Router + fallback + queue |

---

> **Ce document est la feuille de route complète pour Cockpit V2.**
> Clems peut l'utiliser pour distribuer les tâches, phase par phase.
> Aucun codage ne commence avant validation par Olivier.
