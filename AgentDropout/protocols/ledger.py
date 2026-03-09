from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from AgentDropout.protocols.types import ClaimObject, ClaimStatus


class EpistemicLedger:
    def __init__(self):
        self.claims: Dict[str, ClaimObject] = {}

    def add_claims(self, claims: List[ClaimObject]) -> None:
        for claim in claims:
            self._update_status(claim)
            self.claims[claim.claim_id] = claim

    def settle_claim(self, claim_id: str, asset: Dict | None = None, liability_type: str | None = None) -> None:
        if claim_id not in self.claims:
            return
        claim = self.claims[claim_id]
        if asset:
            claim.assets.append(asset)
        if liability_type:
            claim.liabilities = [item for item in claim.liabilities if item.get("type") != liability_type]
        self._update_status(claim)

    def _update_status(self, claim: ClaimObject) -> None:
        liability_count = len(claim.liabilities)
        asset_count = len(claim.assets)
        if liability_count == 0 and asset_count > 0:
            claim.status = ClaimStatus.VERIFIED
        elif liability_count > 0 and asset_count > 0:
            claim.status = ClaimStatus.SUPPORTED
        elif liability_count > 0:
            claim.status = ClaimStatus.CONTESTED
        else:
            claim.status = ClaimStatus.PROPOSED

    def gate_claim(self, claim: ClaimObject, max_liabilities: int = 1) -> bool:
        return len(claim.liabilities) <= max_liabilities

    def snapshot(self) -> Dict[str, Dict]:
        return {claim_id: asdict(claim) for claim_id, claim in self.claims.items()}

    def stats(self) -> Dict[str, float]:
        total = len(self.claims)
        if total == 0:
            return {"total_claims": 0, "verified_claims": 0, "verified_ratio": 0.0}
        verified = sum(1 for claim in self.claims.values() if claim.status == ClaimStatus.VERIFIED)
        return {
            "total_claims": total,
            "verified_claims": verified,
            "verified_ratio": verified / total,
        }

