"""
Download and convert the CRAG (Comprehensive RAG Benchmark) dataset
from HuggingFace to PromptLab's CSV format.

Usage:
    cd backend
    uv run python ../scripts/download_crag.py

Output:
    ../crag_eval_dataset.csv  (ready to upload in PromptLab)
"""

import csv
import sys
from pathlib import Path

def download_crag(output_path: str = "crag_eval_dataset.csv", max_rows: int = 500):
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: 'datasets' library not found.")
        print("Please run: cd backend && uv sync")
        sys.exit(1)

    print("Downloading CRAG dataset from HuggingFace (Quivr/CRAG)...")
    ds = load_dataset("Quivr/CRAG", "crag_task_1_and_2", split="train")

    # CRAG columns:
    #   query        -> question
    #   answer       -> expected_answer
    #   domain       -> metadata for context construction
    #   question_type -> metadata
    #   static_or_dynamic -> metadata
    #   answer_type  -> 'valid', 'invalid', 'no_answer'

    rows = []
    for i, item in enumerate(ds):
        if i >= max_rows:
            break

        # Skip invalid / no-answer rows for a cleaner eval set
        if item.get("answer_type") != "valid":
            continue

        question = item.get("query", "").strip()
        answer = item.get("answer", "").strip()

        # Construct a context from metadata since CRAG is retrieval-based
        # and doesn't ship with pre-retrieved passages
        domain = item.get("domain", "unknown")
        qtype = item.get("question_type", "unknown")
        temporal = item.get("static_or_dynamic", "unknown")

        context = (
            f"This is a {qtype.replace('_', ' ')} question in the {domain} domain. "
            f"The information required is {temporal.replace('_', ' ')}. "
            f"Answer based on factual knowledge about {domain}."
        )

        if question and answer:
            rows.append({
                "question": question,
                "context": context,
                "expected_answer": answer,
            })

    # Write CSV
    out = Path(output_path)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "context", "expected_answer"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {out.resolve()}")
    print(f"Domain distribution:")
    from collections import Counter
    domains = Counter(r["context"].split("domain.")[0].split("the ")[-1].split(" ")[0] for r in rows)
    for d, c in domains.most_common():
        print(f"  {d}: {c}")


if __name__ == "__main__":
    download_crag()
