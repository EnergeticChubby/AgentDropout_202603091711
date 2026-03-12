import argparse
import importlib
import json
import sys
from pathlib import Path


MODULES_TO_CHECK = [
    "AgentDropout.graph",
    "AgentDropout.graph.graph",
    "AgentDropout.graph.node",
    "AgentDropout.agents",
    "AgentDropout.agents.agent_registry",
    "AgentDropout.llm",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Assert that AgentDropout runtime path does not fallback to AgentPrune."
    )
    parser.add_argument("--root", type=str, default="AgentDropout")
    parser.add_argument("--output", type=str, default="result/Blny-v3/phase2/agentdropout_path_assert.json")
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    root = Path(args.root).resolve()
    violations = []
    module_report = {}

    for module_name in MODULES_TO_CHECK:
        module = importlib.import_module(module_name)
        module_file = getattr(module, "__file__", None)
        module_report[module_name] = module_file
        if module_file and "AgentPrune" in module_file:
            violations.append(f"Module {module_name} resolved to AgentPrune path: {module_file}")

    for py_file in root.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if "AgentPrune." in content:
            violations.append(f"Residual AgentPrune import in {py_file}")

    output = {
        "root": str(root),
        "checked_modules": module_report,
        "violations": violations,
        "ok": len(violations) == 0,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[AD-PATH-ASSERT] output={output_path} ok={output['ok']} violations={len(violations)}")
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
