from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class Proposition:
    proposition_id: str
    text: str
    source_node: str
    source_role: str
    confidence: float = 0.5
    status: str = "belief"  # belief/high_confidence/verified
    scope: str = "private"  # private/pairwise/subgroup/team_public/verified_shared
    dependencies: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
