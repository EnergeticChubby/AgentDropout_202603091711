from typing import Dict, Any, List, Union
import itertools
import re

from AgentDropout.prompt.prompt_set import PromptSet
from AgentDropout.prompt.prompt_set_registry import PromptSetRegistry
from AgentDropout.prompt.common import get_combine_materials


CLASS_ORDER = ["UE", "TX-Origin", "RENT", "ARTHM", "TimeO", "LE", "TimeM"]

roles = itertools.cycle(
    [
        "Solidity Security Auditor",
        "Smart Contract Exploit Researcher",
        "EVM Static Analysis Specialist",
        "Formal Verification Thinker",
        "DeFi Incident Investigator",
    ]
)


ROLE_DESCRIPTION = {
    "Solidity Security Auditor": (
        "You are a senior Solidity security auditor. "
        "Analyze the contract carefully and identify vulnerabilities with concrete evidence."
    ),
    "Smart Contract Exploit Researcher": (
        "You are a smart contract exploit researcher. "
        "Focus on attack paths and whether each vulnerability is exploitable."
    ),
    "EVM Static Analysis Specialist": (
        "You are an EVM static analysis specialist. "
        "Focus on opcode/semantic patterns and known anti-patterns."
    ),
    "Formal Verification Thinker": (
        "You think like a formal verification engineer. "
        "Reason from invariants and safety properties."
    ),
    "DeFi Incident Investigator": (
        "You investigate real DeFi incidents. "
        "Use practical exploit heuristics from historical incidents."
    ),
    "Fake": (
        "You are a liar and must intentionally provide incorrect vulnerability judgments."
    ),
}


OUTPUT_RULE = (
    "Target labels follow fixed order [UE, TX-Origin, RENT, ARTHM, TimeO, LE, TimeM]. "
    "You MUST output exactly one 7-length binary vector in <answer> tags, "
    "for example <answer>[0,1,0,1,0,0,0]</answer>. "
    "Do not output any extra vector."
)


@PromptSetRegistry.register("scrawld")
class ScrawlDPromptSet(PromptSet):
    @staticmethod
    def get_role():
        return next(roles)

    @staticmethod
    def get_decision_role():
        return (
            "You are the final security decision-maker. "
            "You aggregate all agent analyses and return the final multi-label vulnerability vector."
        )

    @staticmethod
    def get_constraint():
        return (
            "Given a Solidity contract, detect vulnerabilities among "
            "[UE, TX-Origin, RENT, ARTHM, TimeO, LE, TimeM]. "
            + OUTPUT_RULE
        )

    @staticmethod
    def get_analyze_constraint(role):
        role_desc = ROLE_DESCRIPTION.get(role, "You are a smart contract security analyst.")
        return (
            f"{role_desc}\n"
            "Task: detect whether each vulnerability type exists in the given Solidity contract.\n"
            "Definitions:\n"
            "- UE: Unhandled Exception / unchecked external call return value.\n"
            "- TX-Origin: authorization through tx.origin.\n"
            "- RENT: reentrancy.\n"
            "- ARTHM: arithmetic overflow/underflow.\n"
            "- TimeO: timestamp ordering / transaction order dependence.\n"
            "- LE: locked ether.\n"
            "- TimeM: block values as a proxy for time manipulation.\n"
            + OUTPUT_RULE
        )

    @staticmethod
    def get_decision_constraint():
        return (
            "You will receive multiple agent outputs for vulnerability classification. "
            "Synthesize them and output final prediction. "
            + OUTPUT_RULE
        )

    @staticmethod
    def get_format():
        return "binary_vector"

    @staticmethod
    def get_answer_prompt(question):
        return question

    @staticmethod
    def get_adversarial_answer_prompt(question):
        return (
            "Provide an intentionally wrong vulnerability judgment for this contract. "
            + OUTPUT_RULE
            + f"\nContract:\n{question}"
        )

    @staticmethod
    def get_query_prompt(question):
        raise NotImplementedError

    @staticmethod
    def get_file_analysis_prompt(query, file):
        raise NotImplementedError

    @staticmethod
    def get_websearch_prompt(query):
        raise NotImplementedError

    @staticmethod
    def get_distill_websearch_prompt(query, results):
        raise NotImplementedError

    @staticmethod
    def get_reflect_prompt(question, answer):
        raise NotImplementedError

    @staticmethod
    def get_combine_materials(materials: Dict[str, Any]) -> str:
        return get_combine_materials(materials)

    @staticmethod
    def get_decision_few_shot():
        return (
            "Example:\n"
            "If only ARTHM and LE are present, output <answer>[0,0,0,1,0,1,0]</answer>.\n"
        )

    def postprocess_answer(self, answer: Union[str, List[str]]) -> str:
        if isinstance(answer, list):
            answer = answer[0] if answer else ""
        if not isinstance(answer, str):
            answer = str(answer)
        m = re.search(r"<answer>(.*?)</answer>", answer, flags=re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else answer.strip()
