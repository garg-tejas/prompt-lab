"""Tiny client for sending live traces into PromptLab."""

import json
import urllib.request


class PromptLab:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token

    def ingest(
        self,
        prompt_id: str,
        inputs: dict,
        output: str | None = None,
        version: str = "production",
        model_id: str | None = None,
        judge_model_id: str | None = None,
        score: bool = True,
    ) -> dict:
        payload = {
            "prompt_id": prompt_id,
            "version": version,
            "inputs": inputs,
            "output": output,
            "model_id": model_id,
            "judge_model_id": judge_model_id,
            "score": score,
        }
        request = urllib.request.Request(
            f"{self.api_url}/api/v1/ingest",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode())
