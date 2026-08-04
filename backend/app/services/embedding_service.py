"""Embedding 服务：支持远程 API 和本地模型两种方式"""
import httpx
from app.core.config import settings


class EmbeddingService:
    """文本向量化服务

    优先使用远程 Embedding API（通义千问），
    如果未配置 API Key 则尝试加载本地模型，
    本地模型加载失败则使用模拟向量。
    """

    _model = None
    _model_failed = False

    def _get_model(self):
        """延迟加载本地模型"""
        if EmbeddingService._model_failed:
            return None
        if EmbeddingService._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                import os
                os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "5"
                EmbeddingService._model = SentenceTransformer(
                    "BAAI/bge-small-zh-v1.5", device="cpu",
                )
            except Exception:
                EmbeddingService._model_failed = True
                return None
        return EmbeddingService._model

    async def embed_text(self, text: str) -> list[float]:
        """将文本转为向量（优先使用远程 API）"""
        # 1. 远程 API（通义千问）
        if settings.EMBEDDING_API_KEY and settings.EMBEDDING_API_KEY != "你的阿里云DashScope密钥":
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        settings.EMBEDDING_API_URL,
                        headers={
                            "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": settings.EMBEDDING_MODEL,
                            "input": text[:8000],
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["data"][0]["embedding"]
            except Exception as e:
                print(f"[Embedding API Error] {e}")

        # 2. 本地模型
        model = self._get_model()
        if model is not None:
            try:
                vec = model.encode(text[:8000], normalize_embeddings=True).tolist()
                return vec
            except Exception as e:
                print(f"[Local Embedding Error] {e}")

        # 3. 模拟向量（384维）
        return self._mock_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        results = []
        for text in texts:
            vec = await self.embed_text(text)
            results.append(vec)
        return results

    def _mock_embedding(self, text: str) -> list[float]:
        """生成模拟向量（384维，与 bge-small-zh 维度一致）"""
        import hashlib
        hash_val = hashlib.md5(text.encode()).hexdigest()
        seed = int(hash_val[:8], 16)
        import random
        rng = random.Random(seed)
        return [rng.random() * 2 - 1 for _ in range(384)]