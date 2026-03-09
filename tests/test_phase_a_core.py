from pathlib import Path

from AgentDropout.core.instrumentation import Instrumentation
from AgentDropout.core.phase import DEFAULT_PHASE_SEQUENCE, PhaseScheduler
from AgentDropout.core.simulator import replay_summary


def test_phase_scheduler_defaults():
    scheduler = PhaseScheduler()
    states = [scheduler.phase_at(idx) for idx in range(6)]
    assert states[:4] == DEFAULT_PHASE_SEQUENCE
    assert states[-1] == "aggregate"


def test_instrumentation_writes_jsonl(tmp_path: Path):
    output_file = tmp_path / "events.jsonl"
    instrumentation = Instrumentation(run_id="run-1", output_path=str(output_file))
    instrumentation.emit(
        event_type="round_start",
        phase="propose",
        round_idx=0,
        metadata={"num_nodes": 5},
    )
    instrumentation.emit(
        event_type="message_read",
        phase="propose",
        round_idx=0,
        read_level=4,
        metadata={"edge_type": "spatial"},
    )
    instrumentation.to_jsonl()
    assert output_file.exists()
    summary = replay_summary(str(output_file))
    assert summary["total_events"] == 2
    assert summary["by_event"]["message_read"] == 1
