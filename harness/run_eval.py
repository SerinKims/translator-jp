from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.db.session import SessionLocal  # noqa: E402
from app.services.evaluator import EvaluationService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run translation quality harness.")
    parser.add_argument("--dataset", required=True, help="Path to a JSONL dataset.")
    parser.add_argument("--model", required=True, help="Ollama model name.")
    parser.add_argument("--output", help="Path to write the report JSON.")
    parser.add_argument("--baseline", help="Optional baseline report JSON path.")
    save_group = parser.add_mutually_exclusive_group()
    save_group.add_argument("--save-db", dest="save_db", action="store_true")
    save_group.add_argument("--no-save-db", dest="save_db", action="store_false")
    parser.set_defaults(save_db=False)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    db = SessionLocal() if args.save_db else None
    try:
        service = EvaluationService(db=db)
        report = await service.run_evaluation(
            dataset_path=args.dataset,
            model=args.model,
            output_path=args.output,
            baseline_path=args.baseline,
            save_db=args.save_db,
        )
    finally:
        if db is not None:
            db.close()

    summary = report["summary"]
    print(
        "Harness report written: "
        f"{report['run']['report_path']} "
        f"({summary['passed_cases']}/{summary['total_cases']} passed)"
    )
    print(f"Latest report written: {PROJECT_ROOT / 'harness' / 'reports' / 'latest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
