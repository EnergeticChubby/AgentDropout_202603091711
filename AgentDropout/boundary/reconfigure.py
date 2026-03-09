from typing import List


class OnlineReconfigure:
    """
    Trigger-based reconfiguration rules from runtime traces.
    """

    def suggest(self, handoff_count: int, failure_count: int, round_idx: int) -> List[str]:
        actions: List[str] = []
        if handoff_count > 40:
            actions.append("dissolve")
        if failure_count > 3:
            actions.append("subteam")
        if round_idx >= 2 and handoff_count < 8:
            actions.append("merge")
        return actions
