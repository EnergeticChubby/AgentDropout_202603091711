from collections import Counter
from typing import Any, Dict, List


class ContractRepairer:
    """
    Generate lightweight contract repair suggestions from failure traces.
    """

    def suggest(self, audit_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = Counter()
        by_task_type = Counter()
        for item in audit_records:
            verification = item.get("verification", {})
            contract = item.get("contract", {})
            vios = verification.get("violations", [])
            if not vios:
                continue
            for vio in vios:
                violations[vio] += 1
                task_type = contract.get("metadata", {}).get("task_type", "unknown")
                by_task_type[(task_type, vio)] += 1

        recommendations: List[Dict[str, Any]] = []
        if violations["empty_deliverable"] > 0:
            recommendations.append(
                {
                    "target_clause": "acceptance_test",
                    "change": "require_non_empty",
                    "trigger": "empty_deliverable",
                }
            )
        if violations["missing_final_answer_pattern"] > 0:
            recommendations.append(
                {
                    "target_clause": "deliverable_schema",
                    "change": "enforce_explicit_final_answer",
                    "trigger": "missing_final_answer_pattern",
                }
            )

        return {
            "violation_counts": dict(violations),
            "task_violation_counts": {f"{k[0]}::{k[1]}": v for k, v in by_task_type.items()},
            "recommendations": recommendations,
        }
