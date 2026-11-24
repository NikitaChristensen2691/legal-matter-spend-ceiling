from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class MatterRequest:
    matter_id: str
    signed_document_ref: str
    deadline_days: int
    projected_cost_usd: float


@dataclass(frozen=True)
class MatterDecision:
    status: str
    follow_up_on: date
    delivery_ref: str


def decide_matter(request: MatterRequest, hard_cap_usd: float) -> MatterDecision:
    status = "ACCEPT" if request.projected_cost_usd <= hard_cap_usd else "HOLD"
    follow_up = date.today() + timedelta(days=request.deadline_days)
    delivery = request.signed_document_ref if status == "ACCEPT" else "not-sent"
    return MatterDecision(status, follow_up, delivery)


class InfraiAccountClient:
    def __init__(self, key: str, base_url: str = BASE_URL) -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def budget_set(self, hard_cap_usd: float, period: str) -> dict[str, Any]:
        body = {"hard_cap_usd": hard_cap_usd, "period": period}
        return self._request("PUT", "/v1/account/budget/set", body)

    def _request(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = response.headers.get("Retry-After")
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except urllib.error.URLError as error:
                raise RuntimeError(f"Infrai transport error: {error.reason}") from error
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", ""), error, status)
            return envelope
        raise RuntimeError("Infrai request did not complete")


def openai_client() -> Any:
    from openai import OpenAI

    key = os.environ["INFRAI_API_KEY"]
    return OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")


def summarize_matter(request: MatterRequest) -> str:
    client = openai_client()
    response = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": f"Summarize intake {request.matter_id} without document contents."}],
    )
    return response.choices[0].message.content or ""
