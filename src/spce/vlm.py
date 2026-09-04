"""VLMバックエンド。

- ClaudeCLIBackend: `claude -p` を子プロセスで呼ぶ。画像を読むために Read ツールだけ許可し、
  それ以外のツール（Bash・書き込み・Web）は使わせない。タイムアウトと再試行つき。
- MockBackend: テスト・オフライン用。画像は見ず、決定的な回答を返す。
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time

from .checklist import KEYS


class VLMError(RuntimeError):
    pass


class ClaudeCLIBackend:
    def __init__(self, model: str = "claude-sonnet-5", timeout: int = 180, retries: int = 1):
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def _once(self, prompt: str) -> str:
        # 親プロセス（Claude Code など）の環境変数を外し、子プロセスの誤動作を防ぐ
        env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "ANTHROPIC_"))}
        cmd = [
            "claude", "-p", "--model", self.model,
            "--tools", "Read",  # 画像を開くための Read のみ許可
            "--output-format", "json",
        ]
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env, start_new_session=True,
        )
        try:
            out, err = proc.communicate(input=prompt, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            raise VLMError(f"timeout after {self.timeout}s")
        if proc.returncode != 0:
            raise VLMError(f"claude exit {proc.returncode}: {err[:300]}")
        try:
            data = json.loads(out)
        except json.JSONDecodeError as e:
            raise VLMError(f"cli output not json: {e}")
        if data.get("is_error"):
            raise VLMError(f"cli error: {str(data.get('result'))[:300]}")
        return str(data.get("result", ""))

    def complete(self, prompt: str) -> str:
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._once(prompt)
            except VLMError as e:
                last = e
                if attempt < self.retries:
                    time.sleep(3)
        raise VLMError(f"gave up after {self.retries + 1} attempts: {last}")


class MockBackend:
    """決定的な模擬VLM。画像は見ない。

    - プロンプトに含まれる画像パスのファイル名から photo id を取り、
      id の数字が偶数なら scaffolding=yes、それ以外は no。
    - hinted 条件なら worker_no_helmet を unclear にする（「観点があると慎重になる」の模擬）。
    - MOCK_INVALID=1 なら壊れたJSONを返す（失敗経路のテスト用）。
    """

    def complete(self, prompt: str) -> str:
        if os.environ.get("MOCK_INVALID") == "1":
            return "{'items': not json"
        first = prompt.splitlines()[0]
        digits = "".join(ch for ch in first.rsplit("/", 1)[-1] if ch.isdigit())
        n = int(digits) if digits else 0
        hinted = "確認観点:" in prompt
        items = {}
        for k in KEYS:
            present = "no"
            if k == "scaffolding" and n % 2 == 0:
                present = "yes"
            if k == "worker_no_helmet" and hinted:
                present = "unclear"
            items[k] = {"present": present, "evidence": "mock"}
        return json.dumps({"items": items, "notable_points": ["mock point"]})
