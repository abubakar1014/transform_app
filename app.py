"""
Contract (read aloud before coding):
- POST /transform
- Required: {"text": <string>}
- Optional: {"language": <string>}
- Extra fields ignored.
- Response: {"original", "normalized", "length", "word_count", "tokens", "language?"}
- Invariants:
  * length == len(original)
  * normalized has no leading/trailing whitespace and collapsed internal whitespace
  * tokens == [] if normalized == "" else normalized.split(" ")
  * word_count == len(tokens)
- Errors: missing/non-string text -> 400 with JSON error message.

"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import re

app = FastAPI(title="Transform API", version="1.0")

TOKEN_RE = re.compile(r'\S+')  # matches sequences of non-whitespace characters

class TransformRequest(BaseModel):
    text: str = Field(description="Text to transform (required)")
    language: Optional[str] = Field(default=None, description="Optional language hint (optional)")

class TransformResponse(BaseModel):
    original: str
    normalized: str
    length: int
    word_count: int
    tokens: List[str]
    language: Optional[str] = None

def normalize_text(s: str) -> str:
    # collapse all whitespace sequences into a single space and trim ends
    # deterministic and unicode-aware
    return re.sub(r'\s+', ' ', s).strip()

@app.post("/transform", response_model=TransformResponse, response_model_exclude_none=True)
def transform(req: TransformRequest):
    # Validate `text` is a string is already enforced by Pydantic.
    original = req.text
    if not isinstance(original, str):
        # Shouldn't happen due to Pydantic but keep defensive check.
        raise HTTPException(status_code=400, detail="Invalid request: 'text' must be a string.")
    normalized = normalize_text(original)
    # Extract tokens as sequences of non-whitespace characters from normalized.
    # Using TOKEN_RE ensures deterministic tokenization.
    tokens = TOKEN_RE.findall(normalized) if normalized else []
    word_count = len(tokens)
    length = len(original)  # character count (Python gives Unicode codepoints)
    resp = {
        "original": original,
        "normalized": normalized,
        "length": length,
        "word_count": word_count,
        "tokens": tokens,
    }
    # Only include language if provided in request to preserve old behavior.
    if req.language is not None:
        resp["language"] = req.language
    return resp