#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path


def check_file(path: str):
    p = Path(path)
    return {"path": path, "exists": p.exists(), "is_file": p.is_file()}


def main():
    required_files = [
        "datasets/SVAMP/train.json",
        "datasets/SVAMP/test.json",
    ]
    file_checks = [check_file(path) for path in required_files]

    env_keys = [
        "AGENTDROPOUT_BASE_URL",
        "AGENTDROPOUT_API_KEY",
        "MINIMAX_BASE_URL",
        "MINIMAX_API_KEY",
        "BASE_URL",
        "API_KEY",
    ]
    env_checks = {key: bool(os.getenv(key, "").strip()) for key in env_keys}

    ready_data = all(item["exists"] and item["is_file"] for item in file_checks)
    ready_api = (
        (env_checks["AGENTDROPOUT_BASE_URL"] and env_checks["AGENTDROPOUT_API_KEY"])
        or (env_checks["MINIMAX_BASE_URL"] and env_checks["MINIMAX_API_KEY"])
        or (env_checks["BASE_URL"] and env_checks["API_KEY"])
    )
    payload = {
        "data_ready": ready_data,
        "api_ready": ready_api,
        "files": file_checks,
        "env": env_checks,
    }
    print(json.dumps(payload, indent=2))
    if not (ready_data and ready_api):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
