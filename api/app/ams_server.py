"""AMS model process (OD-8): the only process that loads the embedding model. The API calls it over
HTTP, so stopping this process is how TC-10 switches the AI off while verification keeps working.

Run from api/: uv run fastapi run app/ams_server.py --host 127.0.0.1 --port 8001
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.ams_model import MODEL_VERSION, Embedder

state: dict[str, Embedder] = {}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    state["embedder"] = Embedder()
    yield
    state.clear()


app = FastAPI(title="ProofSkill AMS model", lifespan=lifespan)


class EmbedRequest(BaseModel):
    """Plain texts only: skill labels, aliases, and position requirements, never holder identity."""

    texts: list[str] = Field(min_length=1, max_length=500)


class EmbedResponse(BaseModel):
    vectors: list[list[float]]
    model_version: str


@app.post("/embed")
def embed(body: EmbedRequest) -> EmbedResponse:
    vectors = state["embedder"].embed(body.texts)
    return EmbedResponse(vectors=vectors.tolist(), model_version=MODEL_VERSION)
