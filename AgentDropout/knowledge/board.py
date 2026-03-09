import json
from pathlib import Path
from typing import Dict, List


class SharedKnowledgeBoard:
    def __init__(self) -> None:
        self.public_items: List[Dict] = []

    def write(self, proposition: Dict) -> None:
        self.public_items.append(proposition)

    def retract(self, proposition_id: str) -> None:
        self.public_items = [p for p in self.public_items if p.get("proposition_id") != proposition_id]

    def flush(self, path: str) -> str:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.public_items, indent=2), encoding="utf-8")
        return str(output_path)
