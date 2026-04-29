# Scripts

Helper scripts for dataset preparation and utility tasks.

## `download_crag.py`

Downloads the **CRAG (Comprehensive RAG Benchmark)** dataset from HuggingFace and converts it to PromptLab's CSV format.

### Usage

```bash
cd backend
uv run python ../scripts/download_crag.py
```

### What it does

1. Downloads `Quivr/CRAG` (`crag_task_1_and_2` subset, ~2.7k rows)
2. Filters to **valid** answers only (skips `invalid` and `no_answer`)
3. Constructs a context string from metadata (domain, question type, temporal dynamism)
4. Exports to `crag_eval_dataset.csv` at project root

### Columns in output CSV

| Column            | Source                                                      |
| ----------------- | ----------------------------------------------------------- |
| `question`        | CRAG `query`                                                |
| `context`         | Constructed from domain + question_type + static_or_dynamic |
| `expected_answer` | CRAG `answer`                                               |

### About CRAG

> **CRAG: Comprehensive RAG Benchmark** by Meta AI
> 4,409 questions across 5 domains (Finance, Movie, Music, Open, Sports) and 8 question categories.
> Paper: [arXiv:2406.04744](https://arxiv.org/abs/2406.04744)
> HF Dataset: [`Quivr/CRAG`](https://huggingface.co/datasets/Quivr/CRAG)

### Next steps

After generating the CSV, upload it in PromptLab:

1. Go to **Datasets** → **Upload**
2. Name: `CRAG Benchmark`
3. Domain tag: `rag`
4. Select `crag_eval_dataset.csv`
5. Click **Upload Dataset**
