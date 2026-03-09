import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

from AgentDropout.contracts.schema import DelegationContract, ContractVerificationResult


@dataclass
class ContractAuditRecord:
    timestamp: float
    run_id: str
    round_idx: int
    from_node: str
    to_node: str
    contract: Dict[str, Any]
    verification: Dict[str, Any]


class ContractAuditLog:
    def __init__(self, output_dir: str = "artifacts/contracts/raw") -> None:
        self.output_dir = Path(output_dir)
        self.records: List[ContractAuditRecord] = []

    def record(
        self,
        run_id: str,
        round_idx: int,
        from_node: str,
        to_node: str,
        contract: DelegationContract,
        verification: ContractVerificationResult,
    ) -> None:
        self.records.append(
            ContractAuditRecord(
                timestamp=time.time(),
                run_id=run_id,
                round_idx=round_idx,
                from_node=from_node,
                to_node=to_node,
                contract=contract.to_dict(),
                verification=verification.to_dict(),
            )
        )

    def metrics(self) -> Dict[str, Any]:
        total = len(self.records)
        passed = sum(1 for r in self.records if r.verification.get("passed"))
        failed = total - passed
        silent_failure = sum(
            1
            for r in self.records
            if (not r.verification.get("passed")) and ("empty_deliverable" in r.verification.get("violations", []))
        )
        return {
            "total_contracts": total,
            "passed_contracts": passed,
            "failed_contracts": failed,
            "acceptance_pass_precision": (passed / total) if total else 0.0,
            "silent_failure_rate": (silent_failure / total) if total else 0.0,
            "rework_rate": (failed / total) if total else 0.0,
            "rollback_frequency": failed,
        }

    def flush(self, run_id: str) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        records_path = self.output_dir / f"{run_id}.json"
        payload = [asdict(r) for r in self.records]
        records_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        metrics = self.metrics()
        metrics_path = self.output_dir / f"{run_id}.metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return {"records_path": str(records_path), "metrics_path": str(metrics_path), **metrics}

    def reset(self) -> None:
        self.records = []
