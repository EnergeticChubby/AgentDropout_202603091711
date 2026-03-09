from typing import Dict, Any


CONTRACT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "math": {
        "decision_rights": "solver_autonomy_medium",
        "deliverable_schema": "natural_language_with_final_answer",
        "evidence_obligation": ["step_reasoning"],
        "uncertainty_report": ["assumptions_if_any"],
        "acceptance_test": ["non_empty", "contains_final_answer_pattern"],
        "budget_clause": {"max_tokens": 2048},
    },
    "code": {
        "decision_rights": "implementation_autonomy_high",
        "deliverable_schema": "python_code_block",
        "evidence_obligation": ["test_feedback"],
        "uncertainty_report": ["known_limitations"],
        "acceptance_test": ["non_empty", "python_block_or_text"],
        "budget_clause": {"max_tokens": 4096},
    },
    "qa": {
        "decision_rights": "analysis_autonomy_medium",
        "deliverable_schema": "option_or_explanation",
        "evidence_obligation": ["brief_rationale"],
        "uncertainty_report": ["low_confidence_points"],
        "acceptance_test": ["non_empty"],
        "budget_clause": {"max_tokens": 1536},
    },
}


DEFAULT_TEMPLATE: Dict[str, Any] = {
    "decision_rights": "standard",
    "deliverable_schema": "text",
    "evidence_obligation": [],
    "uncertainty_report": [],
    "acceptance_test": ["non_empty"],
    "budget_clause": {"max_tokens": 1024},
}
