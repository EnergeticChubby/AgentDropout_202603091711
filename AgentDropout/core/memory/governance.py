from __future__ import annotations

from typing import Dict

from AgentDropout.core.memory.constitution import GovernanceConstitution
from AgentDropout.core.memory.schema import MemoryObject
from AgentDropout.core.memory.store import MemoryStore


class MemoryGovernance:
    def __init__(self, store: MemoryStore, constitution: GovernanceConstitution):
        self.store = store
        self.constitution = constitution

    def safe_write(self, pool: str, memory: MemoryObject) -> Dict[str, str]:
        allowed, reason = self.constitution.validate_write(memory)
        if not allowed:
            return {"status": "rejected", "reason": reason}
        if pool == "verified":
            memory.verification_status = "accepted"
        elif pool == "global":
            memory.verification_status = "provisional"
        else:
            memory.verification_status = "proposed"
        self.store.write(pool, memory)
        return {"status": "accepted", "reason": reason}

    def challenge(self, pool: str, index: int) -> Dict[str, str]:
        memory = self.store.challenge(pool, index)
        if self.constitution.should_downgrade(memory):
            memory.verification_status = "deprecated"
        return {"status": memory.verification_status, "challenge_status": memory.challenge_status}

    def revert(self, pool: str, index: int) -> Dict[str, str]:
        memory = self.store.revert(pool, index)
        return {"status": memory.verification_status, "challenge_status": memory.challenge_status}

    def expire(self) -> Dict[str, int]:
        count = self.store.expire()
        return {"expired": count}
