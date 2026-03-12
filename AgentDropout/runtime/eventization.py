from typing import Dict, List, Set


class Eventizer:
    EVENT_KEYS = {
        "claim_create": "CLAIM_CREATE",
        "claim_challenge": "CLAIM_CHALLENGE",
        "claim_resolve": "CLAIM_RESOLVE",
        "summary_submit": "SUMMARY_SUBMIT",
        "summary_rollback": "SUMMARY_ROLLBACK",
        "agent_join": "AGENT_JOIN",
        "agent_drop": "AGENT_DROP",
        "msg_new_info": "MSG_NEW_INFO",
        "msg_rephrase": "MSG_REPHRASE",
        "tool_call_start": "TOOL_CALL_START",
        "tool_call_return": "TOOL_CALL_RETURN",
    }

    def __init__(self):
        self.previous_agents: Set[str] = set()

    def _keyword_events(self, agent_id: str, text: str, round_id: int) -> List[Dict]:
        text_lower = (text or "").lower()
        events = []
        if "the answer is" in text_lower:
            events.append({"type": self.EVENT_KEYS["claim_create"], "agent": agent_id, "round_id": round_id})
        if any(k in text_lower for k in ["however", "but", "disagree", "challenge"]):
            events.append({"type": self.EVENT_KEYS["claim_challenge"], "agent": agent_id, "round_id": round_id})
        if any(k in text_lower for k in ["therefore", "thus", "hence", "resolved"]):
            events.append({"type": self.EVENT_KEYS["claim_resolve"], "agent": agent_id, "round_id": round_id})
        if "summary" in text_lower:
            events.append({"type": self.EVENT_KEYS["summary_submit"], "agent": agent_id, "round_id": round_id})
        if any(k in text_lower for k in ["rollback", "revise summary", "retract"]):
            events.append({"type": self.EVENT_KEYS["summary_rollback"], "agent": agent_id, "round_id": round_id})
        if any(k in text_lower for k in ["new evidence", "new info", "additional evidence"]):
            events.append({"type": self.EVENT_KEYS["msg_new_info"], "agent": agent_id, "round_id": round_id})
        if any(k in text_lower for k in ["rephrase", "in other words"]):
            events.append({"type": self.EVENT_KEYS["msg_rephrase"], "agent": agent_id, "round_id": round_id})
        if "```python" in text_lower:
            events.append({"type": self.EVENT_KEYS["tool_call_start"], "agent": agent_id, "round_id": round_id})
            events.append({"type": self.EVENT_KEYS["tool_call_return"], "agent": agent_id, "round_id": round_id})
        return events

    def extract_from_round(self, round_answers: Dict[str, List[str]], round_id: int) -> List[Dict]:
        events = []
        current_agents = set(round_answers.keys())

        for agent_id in sorted(current_agents - self.previous_agents):
            events.append({"type": self.EVENT_KEYS["agent_join"], "agent": agent_id, "round_id": round_id})
        for agent_id in sorted(self.previous_agents - current_agents):
            events.append({"type": self.EVENT_KEYS["agent_drop"], "agent": agent_id, "round_id": round_id})

        for agent_id, output in round_answers.items():
            text = output[-1] if isinstance(output, list) and output else str(output)
            events.extend(self._keyword_events(agent_id=agent_id, text=text, round_id=round_id))

        self.previous_agents = current_agents
        return events
