import csv
import io
import json
from typing import List

from fastapi import UploadFile, File, HTTPException


def parse_csv_file(content: bytes) -> List[dict]:
    try:
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            rows.append({
                "question": row.get("question", "").strip(),
                "context": row.get("context", "").strip(),
                "expected_answer": row.get("expected_answer", "").strip() or None,
            })
        return rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")


def parse_json_file(content: bytes) -> List[dict]:
    try:
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, dict):
            data = data.get("data", data.get("rows", []))
        if not isinstance(data, list):
            raise ValueError("JSON must contain a list of objects")
        rows = []
        for item in data:
            rows.append({
                "question": str(item.get("question", "")).strip(),
                "context": str(item.get("context", "")).strip(),
                "expected_answer": str(item.get("expected_answer", "")).strip() or None,
            })
        return rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")


async def parse_upload_file(file: UploadFile) -> List[dict]:
    content = await file.read()
    filename = file.filename or ""
    if filename.endswith(".csv"):
        return parse_csv_file(content)
    elif filename.endswith(".json"):
        return parse_json_file(content)
    else:
        raise HTTPException(status_code=400, detail="File must be .csv or .json")
