from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from AgentDropout.core.memory.schema import MemoryObject


class MemoryStore:
    POOLS = ("local", "team", "global", "verified")

    def __init__(self):
        self.pools: Dict[str, List[MemoryObject]] = defaultdict(list)
        for pool in self.POOLS:
            self.pools[pool] = []

    def write(self, pool: str, memory: MemoryObject) -> None:
        if pool not in self.pools:
            raise ValueError(f"Unknown memory pool: {pool}")
        self.pools[pool].append(memory)

    def read(self, pool: Optional[str] = None, phase: Optional[str] = None, min_evidence: float = 0.0) -> List[MemoryObject]:
        memories = []
        pools = [pool] if pool else list(self.pools.keys())
        for selected_pool in pools:
            for memory in self.pools[selected_pool]:
                if phase and memory.phase != phase:
                    continue
                if memory.evidence_strength < min_evidence:
                    continue
                memory.read_count += 1
                memories.append(memory)
        return memories

    def challenge(self, pool: str, index: int, liability_delta: float = 0.1) -> MemoryObject:
        memory = self.pools[pool][index]
        memory.challenge_status = "contested"
        memory.verification_status = "contested"
        memory.error_liability = min(1.0, memory.error_liability + liability_delta)
        return memory

    def revert(self, pool: str, index: int) -> MemoryObject:
        memory = self.pools[pool][index]
        memory.verification_status = "deprecated"
        memory.challenge_status = "reverted"
        return memory

    def expire(self) -> int:
        expired = 0
        for pool in self.pools:
            for memory in self.pools[pool]:
                if memory.verification_status in {"deprecated", "expired"}:
                    continue
                memory.ttl -= 1
                if memory.ttl <= 0:
                    memory.verification_status = "expired"
                    memory.challenge_status = "expired"
                    expired += 1
        return expired
