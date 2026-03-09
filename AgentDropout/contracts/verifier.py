from typing import Any, List

from AgentDropout.contracts.schema import DelegationContract, ContractVerificationResult


class ContractVerifier:
    @staticmethod
    def _normalize_output(output: Any) -> str:
        if output is None:
            return ""
        if isinstance(output, list):
            return "\n".join(str(x) for x in output if x is not None).strip()
        return str(output).strip()

    def verify(self, contract: DelegationContract, output: Any) -> ContractVerificationResult:
        text = self._normalize_output(output)
        violations: List[str] = []

        if "non_empty" in contract.acceptance_test and len(text) == 0:
            violations.append("empty_deliverable")

        if "contains_final_answer_pattern" in contract.acceptance_test:
            if "the answer is" not in text.lower() and "answer:" not in text.lower():
                violations.append("missing_final_answer_pattern")

        if "python_block_or_text" in contract.acceptance_test:
            # tolerate either python fenced block or plain textual explanation.
            if len(text) == 0:
                violations.append("missing_python_or_text_deliverable")

        return ContractVerificationResult(
            passed=len(violations) == 0,
            violations=violations,
            details={"output_length": len(text)},
        )
