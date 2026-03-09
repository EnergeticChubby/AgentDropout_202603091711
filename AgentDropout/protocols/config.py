from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class ProtocolConfig:
    enable_mirm: bool = False
    enable_edel: bool = False
    enable_abpp: bool = False
    risk_level: str = "medium"
    token_budget: int = 4096
    topk_disclosure: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "ProtocolConfig":
        if not data:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

