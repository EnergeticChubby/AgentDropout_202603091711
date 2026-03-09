import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from AgentDropout.core.covariance_store import compute_pairwise_error_covariance
from AgentDropout.core.risk_card import RiskCard


def parse_args():
    parser = argparse.ArgumentParser(description="Build covariance store from benchmark prediction files.")
    parser.add_argument("--predictions_glob", type=str, required=True)
    parser.add_argument("--output_covariance", type=str, required=True)
    parser.add_argument("--output_risk_cards", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    paths = sorted(Path().glob(args.predictions_glob))
    if not paths:
        raise FileNotFoundError(f"No prediction files matched: {args.predictions_glob}")

    error_vectors: Dict[str, List[int]] = {}
    risk_cards: Dict[str, Dict] = {}
    for path in paths:
        agent_id = path.parent.name
        errors: List[int] = []
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                row = json.loads(line)
                errors.append(0 if row.get("is_correct", False) else 1)
        error_vectors[agent_id] = errors
        accuracy = 1.0 - (sum(errors) / len(errors) if errors else 0.0)
        card = RiskCard(agent_id=agent_id, base_accuracy=accuracy, uncertainty=1.0 - accuracy)
        risk_cards[agent_id] = card.to_dict()

    covariance = compute_pairwise_error_covariance(error_vectors)
    covariance.save(args.output_covariance)
    output_cards = Path(args.output_risk_cards)
    output_cards.parent.mkdir(parents=True, exist_ok=True)
    with output_cards.open("w", encoding="utf-8") as fp:
        json.dump(risk_cards, fp, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "num_agents": len(error_vectors),
                "output_covariance": args.output_covariance,
                "output_risk_cards": args.output_risk_cards,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
