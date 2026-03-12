#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim


PHASES = [
    "exploration",
    "productive",
    "repetition_stagnation",
    "premature_consensus",
    "recovery",
]
PHASE_TO_ID = {name: i for i, name in enumerate(PHASES)}

FEATURE_KEYS = [
    "answer_consensus",
    "answer_conflict",
    "new_information",
    "repetition_ratio",
    "semantic_novelty_drop",
    "token_growth",
    "progress_delta",
]


@dataclass
class TrainingMetrics:
    split: str
    loss: float
    phase_accuracy: float
    risk_repeat_accuracy: float
    risk_consensus_accuracy: float
    risk_capacity_accuracy: float
    phase_macro_f1: float


class StateObserverNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.phase_head = nn.Linear(hidden_dim, len(PHASES))
        self.risk_head = nn.Linear(hidden_dim, 3)

    def forward(self, x):
        h = self.backbone(x)
        return self.phase_head(h), self.risk_head(h)


def load_dataset(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def split_dataset(rows: List[Dict], seed: int, val_ratio: float) -> Tuple[List[Dict], List[Dict]]:
    rows_copy = list(rows)
    rng = random.Random(seed)
    rng.shuffle(rows_copy)
    val_size = max(1, int(len(rows_copy) * val_ratio))
    val_rows = rows_copy[:val_size]
    train_rows = rows_copy[val_size:]
    if len(train_rows) == 0:
        train_rows, val_rows = rows_copy, rows_copy
    return train_rows, val_rows


def build_tensors(rows: List[Dict]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    features = []
    phase_targets = []
    risk_targets = []
    for row in rows:
        feat = row.get("features", {})
        features.append([float(feat.get(k, 0.0)) for k in FEATURE_KEYS])
        phase_targets.append(PHASE_TO_ID.get(row.get("phase_label", "exploration"), 0))
        risk_targets.append([
            int(row.get("risk_repeat_label", 0)),
            int(row.get("risk_consensus_label", 0)),
            int(row.get("risk_capacity_label", 0)),
        ])

    x = torch.tensor(features, dtype=torch.float32)
    y_phase = torch.tensor(phase_targets, dtype=torch.long)
    y_risk = torch.tensor(risk_targets, dtype=torch.float32)
    return x, y_phase, y_risk


def macro_f1(y_true: torch.Tensor, y_pred: torch.Tensor, n_classes: int) -> float:
    scores = []
    for cls in range(n_classes):
        tp = int(((y_true == cls) & (y_pred == cls)).sum().item())
        fp = int(((y_true != cls) & (y_pred == cls)).sum().item())
        fn = int(((y_true == cls) & (y_pred != cls)).sum().item())
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if precision + recall == 0:
            scores.append(0.0)
        else:
            scores.append(2 * precision * recall / (precision + recall))
    return float(sum(scores) / len(scores))


def evaluate(
    model: StateObserverNet,
    x: torch.Tensor,
    y_phase: torch.Tensor,
    y_risk: torch.Tensor,
    ce_loss: nn.Module,
    bce_loss: nn.Module,
    split: str,
) -> TrainingMetrics:
    model.eval()
    with torch.no_grad():
        phase_logits, risk_logits = model(x)
        loss = ce_loss(phase_logits, y_phase) + bce_loss(risk_logits, y_risk)

        phase_pred = torch.argmax(phase_logits, dim=-1)
        risk_prob = torch.sigmoid(risk_logits)
        risk_pred = (risk_prob >= 0.5).long()

        phase_acc = float((phase_pred == y_phase).float().mean().item())
        rr_acc = float((risk_pred[:, 0] == y_risk[:, 0].long()).float().mean().item())
        rc_acc = float((risk_pred[:, 1] == y_risk[:, 1].long()).float().mean().item())
        rk_acc = float((risk_pred[:, 2] == y_risk[:, 2].long()).float().mean().item())
        f1 = macro_f1(y_phase, phase_pred, len(PHASES))

        return TrainingMetrics(
            split=split,
            loss=float(loss.item()),
            phase_accuracy=phase_acc,
            risk_repeat_accuracy=rr_acc,
            risk_consensus_accuracy=rc_acc,
            risk_capacity_accuracy=rk_acc,
            phase_macro_f1=f1,
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Train state observer from labeled telemetry dataset.")
    parser.add_argument("--dataset_jsonl", type=str, required=True)
    parser.add_argument("--model_out", type=str, required=True)
    parser.add_argument("--metrics_out", type=str, required=True)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden_dim", type=int, default=64)
    parser.add_argument("--val_ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    rows = load_dataset(args.dataset_jsonl)
    train_rows, val_rows = split_dataset(rows, seed=args.seed, val_ratio=args.val_ratio)

    x_train, y_phase_train, y_risk_train = build_tensors(train_rows)
    x_val, y_phase_val, y_risk_val = build_tensors(val_rows)

    model = StateObserverNet(input_dim=len(FEATURE_KEYS), hidden_dim=args.hidden_dim)
    ce_loss = nn.CrossEntropyLoss()
    bce_loss = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    best_state = None
    best_val_loss = float("inf")

    for _ in range(args.epochs):
        model.train()
        optimizer.zero_grad()
        phase_logits, risk_logits = model(x_train)
        loss = ce_loss(phase_logits, y_phase_train) + bce_loss(risk_logits, y_risk_train)
        loss.backward()
        optimizer.step()

        val_metrics = evaluate(model, x_val, y_phase_val, y_risk_val, ce_loss, bce_loss, split="val")
        if val_metrics.loss < best_val_loss:
            best_val_loss = val_metrics.loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    train_metrics = evaluate(model, x_train, y_phase_train, y_risk_train, ce_loss, bce_loss, split="train")
    val_metrics = evaluate(model, x_val, y_phase_val, y_risk_val, ce_loss, bce_loss, split="val")

    model_path = Path(args.model_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "feature_keys": FEATURE_KEYS,
        "phase_names": PHASES,
    }, model_path)

    metrics_payload = {
        "train": asdict(train_metrics),
        "val": asdict(val_metrics),
        "dataset_rows": len(rows),
        "train_rows": len(train_rows),
        "val_rows": len(val_rows),
    }
    metrics_path = Path(args.metrics_out)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print(json.dumps(metrics_payload, indent=2))


if __name__ == "__main__":
    main()
