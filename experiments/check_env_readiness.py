#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
from pathlib import Path


def check_file(path: str):
    p = Path(path)
    return {"path": path, "exists": p.exists(), "is_file": p.is_file()}


def parse_args():
    parser = argparse.ArgumentParser(description="Check SVAMP data and API environment readiness.")
    parser.add_argument("--svamp_train_json", type=str, default="datasets/SVAMP/train.json")
    parser.add_argument("--svamp_test_json", type=str, default="datasets/SVAMP/test.json")
    parser.add_argument("--require_gsm8k", action="store_true")
    parser.add_argument("--gsm8k_train_json", type=str, default="datasets/gsm8k/train.jsonl")
    parser.add_argument("--gsm8k_test_json", type=str, default="datasets/gsm8k/test.jsonl")
    parser.add_argument("--skip_api_check", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    required_files = [
        args.svamp_train_json,
        args.svamp_test_json,
    ]
    if args.require_gsm8k:
        required_files.extend([args.gsm8k_train_json, args.gsm8k_test_json])
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
    ready_api = True if args.skip_api_check else (
        (env_checks["AGENTDROPOUT_BASE_URL"] and env_checks["AGENTDROPOUT_API_KEY"])
        or (env_checks["MINIMAX_BASE_URL"] and env_checks["MINIMAX_API_KEY"])
        or (env_checks["BASE_URL"] and env_checks["API_KEY"])
    )
    payload = {
        "data_ready": ready_data,
        "api_ready": ready_api,
        "skip_api_check": args.skip_api_check,
        "require_gsm8k": args.require_gsm8k,
        "files": file_checks,
        "env": env_checks,
    }
    print(json.dumps(payload, indent=2))
    if not (ready_data and ready_api):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
