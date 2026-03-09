from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class MultiLayerMessage:
    headline: str
    claims: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    full_rationale: str = ""
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _split_sentences(text: str) -> List[str]:
    chunks = [segment.strip() for segment in re.split(r"[。.!?\n]+", text) if segment.strip()]
    return chunks


def build_multilayer_message(text: str) -> Dict[str, Any]:
    text = text if isinstance(text, str) else str(text)
    sentences = _split_sentences(text)
    headline = sentences[0] if sentences else text[:120]
    claims = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*").strip()
        if not line:
            continue
        if len(line) <= 180:
            claims.append(line)
    if not claims and sentences:
        claims = sentences[: min(3, len(sentences))]
    evidence = []
    for sentence in sentences:
        lowered = sentence.lower()
        if "because" in lowered or "therefore" in lowered or "according to" in lowered:
            evidence.append(sentence)
    return MultiLayerMessage(
        headline=headline,
        claims=claims[:5],
        evidence=evidence[:5],
        full_rationale=text,
        raw_text=text,
    ).to_dict()


def coerce_multilayer_message(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        required = {"headline", "claims", "evidence", "full_rationale", "raw_text"}
        if required.issubset(payload.keys()):
            return payload
    if isinstance(payload, list):
        payload = payload[-1] if payload else ""
    return build_multilayer_message(str(payload))


def render_multilayer_message(payload: Any, read_level: int) -> str:
    message = coerce_multilayer_message(payload)
    level = max(0, min(4, int(read_level)))
    if level == 0:
        return ""
    if level == 1:
        return message["headline"]
    if level == 2:
        claims = "\n".join([f"- {item}" for item in message.get("claims", [])])
        return f"{message['headline']}\n{claims}".strip()
    if level == 3:
        claims = "\n".join([f"- {item}" for item in message.get("claims", [])])
        evidence = "\n".join([f"* {item}" for item in message.get("evidence", [])])
        return f"{message['headline']}\n{claims}\nEvidence:\n{evidence}".strip()
    return message.get("full_rationale") or message.get("raw_text") or message.get("headline", "")


def extract_choice_label(text: str) -> str:
    if not isinstance(text, str):
        return ""
    match = re.search(r"\b([ABCD])\b", text.upper())
    return match.group(1) if match else ""


def detect_conflict_peer_ids(peer_outputs: Dict[str, Any]) -> List[str]:
    labels = {peer_id: extract_choice_label(str(output)) for peer_id, output in peer_outputs.items()}
    valid_labels = [label for label in labels.values() if label]
    if len(valid_labels) <= 1:
        return []
    if len(set(valid_labels)) <= 1:
        return []
    return [peer_id for peer_id, label in labels.items() if label]
