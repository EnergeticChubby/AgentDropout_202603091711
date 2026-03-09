import json
from pathlib import Path
from typing import Dict, List

from AgentDropout.knowledge.proposition import Proposition


class EpistemicStateStore:
    def __init__(self) -> None:
        self.propositions: Dict[str, Proposition] = {}
        self.by_node: Dict[str, List[str]] = {}

    def add(self, proposition: Proposition) -> None:
        self.propositions[proposition.proposition_id] = proposition
        self.by_node.setdefault(proposition.source_node, []).append(proposition.proposition_id)

    def update_scope(self, proposition_id: str, scope: str) -> None:
        if proposition_id in self.propositions:
            self.propositions[proposition_id].scope = scope

    def update_status(self, proposition_id: str, status: str) -> None:
        if proposition_id in self.propositions:
            self.propositions[proposition_id].status = status

    def snapshot(self) -> Dict[str, Dict]:
        return {pid: prop.to_dict() for pid, prop in self.propositions.items()}

    def flush(self, path: str) -> str:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")
        return str(output_path)
