from __future__ import annotations

from typing import Any


def build_questions(intake: dict[str, Any], max_questions: int = 5) -> list[str]:
    questions: list[str] = []

    if not intake.get("readme_excerpt"):
        questions.append("Quel est le but principal du projet?")

    if "tests" not in " ".join(intake.get("top_files", [])).lower():
        questions.append("Comment lancer les tests (s il y en a) ?")

    if "unknown" in (intake.get("stack") or []):
        questions.append("Quelle est la stack principale (langage, framework) ?")

    questions.append("Quels sont les objectifs prioritaires (1-3) pour la prochaine release ?")
    questions.append("Quelles contraintes ou risques devons-nous respecter ?")

    return questions[:max_questions]
