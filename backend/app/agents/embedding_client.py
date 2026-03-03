"""Resilient Embedding Client — 腾讯混元 (primary) + 智谱 (fallback).

All embeddings produce 1024-dimension vectors for pgvector HNSW indexes.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from functools import lru_cache

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BATCH_SIZE = 16  # 混元 API 每批最大数量
DIMENSION = 1024


@dataclass
class EmbeddingResult:
    embedding: list[float]
    model: str
    tokens_used: int = 0


@dataclass
class BatchEmbeddingResult:
    embeddings: list[list[float]]
    model: str
    total_tokens: int = 0
    failed_indices: list[int] = field(default_factory=list)


class EmbeddingProvider:
    """Base class for embedding providers."""

    name: str = "base"
    api_url: str = ""
    api_key: str = ""
    model: str = ""

    async def embed_single(self, text: str) -> EmbeddingResult:
        raise NotImplementedError

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        raise NotImplementedError


class TencentHunyuanProvider(EmbeddingProvider):
    """腾讯混元 Embedding — primary provider."""

    name = "tencent_hunyuan"

    def __init__(self) -> None:
        self.api_url = settings.EMBEDDING_API_URL
        self.api_key = settings.EMBEDDING_API_KEY
        self.model = settings.EMBEDDING_MODEL

    async def embed_single(self, text: str) -> EmbeddingResult:
        result = await self.embed_batch([text])
        return EmbeddingResult(
            embedding=result.embeddings[0],
            model=self.model,
            tokens_used=result.total_tokens,
        )

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.api_url,
                json={"input": texts, "model": self.model},
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        embeddings = [item["embedding"] for item in data["data"]]
        total_tokens = data.get("usage", {}).get("total_tokens", 0)

        return BatchEmbeddingResult(
            embeddings=embeddings,
            model=self.model,
            total_tokens=total_tokens,
        )


class ZhipuProvider(EmbeddingProvider):
    """智谱 Embedding — fallback provider."""

    name = "zhipu"

    def __init__(self) -> None:
        self.api_url = settings.EMBEDDING_FALLBACK_URL
        self.api_key = settings.EMBEDDING_FALLBACK_KEY
        self.model = settings.EMBEDDING_FALLBACK_MODEL

    async def embed_single(self, text: str) -> EmbeddingResult:
        result = await self.embed_batch([text])
        return EmbeddingResult(
            embedding=result.embeddings[0],
            model=self.model,
            tokens_used=result.total_tokens,
        )

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.api_url,
                json={"input": texts, "model": self.model},
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        embeddings = [item["embedding"] for item in data["data"]]
        total_tokens = data.get("usage", {}).get("total_tokens", 0)

        return BatchEmbeddingResult(
            embeddings=embeddings,
            model=self.model,
            total_tokens=total_tokens,
        )


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic random-vector provider for development/testing.

    Generates 1024-dim float32 vectors seeded by the SHA-256 of the text,
    so the same text always produces the same vector.  Vectors are *not*
    semantically meaningful but allow the full pipeline to run without
    real API keys configured.
    """

    name = "mock"

    def _make_vector(self, text: str) -> list[float]:
        import math
        # Use SHA-256 bytes as unsigned integers to avoid NaN/Inf from float32 interpretation
        digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
        # Tile digest bytes to fill 1024 elements (each element = 1 byte 0-255)
        tiled = (digest * 64)[:DIMENSION]  # 32 * 32 = 1024 bytes
        # Convert to signed floats in range [-0.5, 0.5] — guaranteed no NaN/Inf
        raw = [b / 255.0 - 0.5 for b in tiled]
        # Normalise to unit sphere
        norm = math.sqrt(sum(v * v for v in raw)) or 1.0
        return [v / norm for v in raw]

    async def embed_single(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(embedding=self._make_vector(text), model="mock", tokens_used=0)

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        return BatchEmbeddingResult(
            embeddings=[self._make_vector(t) for t in texts],
            model="mock",
            total_tokens=0,
        )


class ResilientEmbeddingClient:
    """Embedding client with automatic failover and batch processing."""

    def __init__(self) -> None:
        self.primary = TencentHunyuanProvider()
        self.fallback = ZhipuProvider()
        self._mock = MockEmbeddingProvider()
        self._use_mock_fallback = settings.APP_ENV in ("development", "test", "dev")
        self._semaphore = asyncio.Semaphore(5)  # concurrent request limit

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Embed a single text with automatic fallback."""
        async with self._semaphore:
            try:
                return await self.primary.embed_single(text)
            except Exception:
                logger.warning(
                    "Primary embedding (%s) failed, falling back to %s",
                    self.primary.name,
                    self.fallback.name,
                )
                try:
                    return await self.fallback.embed_single(text)
                except Exception:
                    if self._use_mock_fallback:
                        logger.warning(
                            "Both real providers failed — using mock random vectors (development mode)"
                        )
                        return await self._mock.embed_single(text)
                    logger.exception("Both embedding providers failed")
                    raise

    async def embed_texts(self, texts: list[str]) -> list[EmbeddingResult]:
        """Batch embed with chunked requests.

        Splits into batches of BATCH_SIZE, processes with primary provider,
        falls back to fallback provider on failure.
        """
        all_results: list[EmbeddingResult] = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            batch_result = await self._embed_batch_with_fallback(batch)

            for emb in batch_result.embeddings:
                all_results.append(
                    EmbeddingResult(
                        embedding=emb,
                        model=batch_result.model,
                        tokens_used=0,
                    )
                )

        return all_results

    async def _embed_batch_with_fallback(
        self, texts: list[str]
    ) -> BatchEmbeddingResult:
        """Try primary, then fallback for a single batch."""
        async with self._semaphore:
            try:
                return await self.primary.embed_batch(texts)
            except Exception:
                logger.warning(
                    "Primary batch embedding failed, trying fallback (%d texts)",
                    len(texts),
                )
                try:
                    return await self.fallback.embed_batch(texts)
                except Exception:
                    if self._use_mock_fallback:
                        logger.warning(
                            "Both real providers failed — using mock random vectors (development mode)"
                        )
                        return await self._mock.embed_batch(texts)
                    logger.exception("Both providers failed for batch")
                    raise


@lru_cache(maxsize=1)
def get_embedding_client() -> ResilientEmbeddingClient:
    """Singleton factory for the embedding client."""
    return ResilientEmbeddingClient()
