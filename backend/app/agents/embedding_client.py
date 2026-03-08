"""Resilient Embedding Client — 腾讯混元 (primary) + 智谱 (fallback).

All embeddings produce 1024-dimension vectors for pgvector HNSW indexes.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from functools import lru_cache

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
    """腾讯混元 Embedding — primary provider (via tencentcloud SDK)."""

    name = "tencent_hunyuan"

    def __init__(self) -> None:
        self.secret_id = settings.HUNYUAN_SECRET_ID
        self.secret_key = settings.HUNYUAN_SECRET_KEY
        self.model = settings.EMBEDDING_MODEL

    def _get_client(self):
        from tencentcloud.common import credential
        from tencentcloud.hunyuan.v20230901 import hunyuan_client
        cred = credential.Credential(self.secret_id, self.secret_key)
        return hunyuan_client.HunyuanClient(cred, "")

    async def embed_single(self, text: str) -> EmbeddingResult:
        result = await self.embed_batch([text])
        return EmbeddingResult(
            embedding=result.embeddings[0],
            model=self.model,
            tokens_used=result.total_tokens,
        )

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        from tencentcloud.hunyuan.v20230901 import models as hunyuan_models
        client = self._get_client()
        loop = asyncio.get_event_loop()

        req = hunyuan_models.GetEmbeddingRequest()
        req.InputList = texts

        resp = await loop.run_in_executor(None, client.GetEmbedding, req)
        all_embeddings = [list(item.Embedding) for item in resp.Data]
        total_tokens = (resp.Usage.TotalTokens or 0) if resp.Usage else 0

        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            model="hunyuan-embedding",
            total_tokens=total_tokens,
        )


class ZhipuProvider(EmbeddingProvider):
    """智谱 Embedding — fallback provider (via zhipuai SDK)."""

    name = "zhipu"

    def __init__(self) -> None:
        self.api_key = settings.ZHIPU_API_KEY
        self.model = settings.EMBEDDING_FALLBACK_MODEL

    def _get_client(self):
        from zhipuai import ZhipuAI
        return ZhipuAI(api_key=self.api_key)

    async def embed_single(self, text: str) -> EmbeddingResult:
        result = await self.embed_batch([text])
        return EmbeddingResult(
            embedding=result.embeddings[0],
            model=self.model,
            tokens_used=result.total_tokens,
        )

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        client = self._get_client()
        loop = asyncio.get_event_loop()

        def _call():
            resp = client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=1024,
            )
            embeddings = [item.embedding for item in resp.data]
            total = getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0
            return embeddings, total

        embeddings, total_tokens = await loop.run_in_executor(None, _call)
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


class HunyuanTranslator:
    """使用腾讯混元 Chat API 将中文查询翻译为英文，用于提升英文文档的向量检索准确率。"""

    def __init__(self) -> None:
        self.secret_id = settings.HUNYUAN_SECRET_ID
        self.secret_key = settings.HUNYUAN_SECRET_KEY

    def _get_client(self):
        from tencentcloud.common import credential
        from tencentcloud.hunyuan.v20230901 import hunyuan_client
        cred = credential.Credential(self.secret_id, self.secret_key)
        return hunyuan_client.HunyuanClient(cred, "")

    async def translate_zh_to_en(self, text: str) -> str:
        """将中文招标相关查询翻译为英文。失败时静默返回原文。"""
        from tencentcloud.hunyuan.v20230901 import models as hunyuan_models
        client = self._get_client()
        loop = asyncio.get_event_loop()

        req = hunyuan_models.ChatCompletionsRequest()
        req.Model = "hunyuan-lite"
        req.Stream = False
        msg_system = hunyuan_models.Message()
        msg_system.Role = "system"
        msg_system.Content = (
            "You are a professional translator specializing in procurement and "
            "bidding documents. Translate the following Chinese text to English "
            "concisely, preserving technical terms accurately. Output only the "
            "English translation, nothing else."
        )
        msg_user = hunyuan_models.Message()
        msg_user.Role = "user"
        msg_user.Content = text
        req.Messages = [msg_system, msg_user]

        resp = await loop.run_in_executor(None, client.ChatCompletions, req)
        translated: str = resp.Choices[0].Message.Content.strip()
        return translated if translated else text


@lru_cache(maxsize=1)
def get_embedding_client() -> ResilientEmbeddingClient:
    """Singleton factory for the embedding client."""
    return ResilientEmbeddingClient()


@lru_cache(maxsize=1)
def get_translator() -> HunyuanTranslator:
    """Singleton factory for the Hunyuan translator."""
    return HunyuanTranslator()
