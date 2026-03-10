import json
import os
import time
from pathlib import Path

from openai import OpenAI


def _extract_text(response) -> str:
    try:
        return response.choices[0].message.content or ""
    except Exception:
        return str(response)


def _is_html_like(text: str) -> bool:
    t = text.lower()
    return "<!doctype html" in t or "<html" in t or "<head>" in t


def main():
    base_url = os.getenv("LLM_BASE_URL", "https://llm.undefined.qzz.io/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "qwen3-8b")
    n = int(os.getenv("HEALTH_PROBE_N", "20"))

    client = OpenAI(base_url=base_url, api_key=api_key)
    rows = []
    for idx in range(n):
        started = time.time()
        ok = True
        err = ""
        text = ""
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are concise."},
                    {"role": "user", "content": "Return exactly one character: B"},
                ],
                temperature=0.0,
            )
            text = _extract_text(resp)
        except Exception as e:
            ok = False
            err = str(e)
            text = ""
        rows.append(
            {
                "idx": idx,
                "ok": ok,
                "error": err,
                "latency_sec": time.time() - started,
                "is_html_like": _is_html_like(text),
                "text_preview": text[:120],
            }
        )

    summary = {
        "model": model,
        "base_url": base_url,
        "num_requests": n,
        "num_success": sum(1 for r in rows if r["ok"]),
        "num_html_like": sum(1 for r in rows if r["is_html_like"]),
        "num_errors": sum(1 for r in rows if not r["ok"]),
        "html_like_ratio": (sum(1 for r in rows if r["is_html_like"]) / n) if n else 0.0,
    }
    out_dir = Path("artifacts/runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "qwen3-endpoint-health-probe.json"
    with out_file.open("w", encoding="utf-8") as fp:
        json.dump({"summary": summary, "rows": rows}, fp, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
