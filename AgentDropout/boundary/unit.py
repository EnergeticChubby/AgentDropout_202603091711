from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class OrganizationUnit:
    unit_id: str
    unit_type: str  # internal/tool/single_agent/subteam
    members: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)
