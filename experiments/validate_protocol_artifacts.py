#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _simple_type_check(value: Any, type_name: str) -> bool:
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
    }
    py_type = mapping.get(type_name)
    if py_type is None:
        return True
    return isinstance(value, py_type)


def _fallback_validate(instance: Any, schema: Dict[str, Any], path: str = "$") -> None:
    schema_type = schema.get("type")
    if isinstance(schema_type, str) and not _simple_type_check(instance, schema_type):
        raise ValueError(f"{path}: expected type {schema_type}, got {type(instance).__name__}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise ValueError(f"{path}: missing required key `{key}`")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                _fallback_validate(value, properties[key], f"{path}.{key}")
    elif isinstance(instance, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(instance):
                _fallback_validate(item, item_schema, f"{path}[{idx}]")


def validate_with_jsonschema(instance: Any, schema: Dict[str, Any]) -> str:
    try:
        import jsonschema  # type: ignore
    except ImportError as exc:
        _fallback_validate(instance, schema)
        return "fallback"
    jsonschema.validate(instance=instance, schema=schema)
    return "jsonschema"


def parse_args():
    parser = argparse.ArgumentParser(description="Validate protocol artifacts against JSON schemas.")
    parser.add_argument("--instance_json", type=str, required=True)
    parser.add_argument("--schema_json", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    instance = load_json(args.instance_json)
    schema = load_json(args.schema_json)
    mode = validate_with_jsonschema(instance, schema)
    print(json.dumps({
        "instance_json": str(Path(args.instance_json)),
        "schema_json": str(Path(args.schema_json)),
        "validation_mode": mode,
        "valid": True,
    }, indent=2))


if __name__ == "__main__":
    main()
