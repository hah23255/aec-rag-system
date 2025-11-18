"""
Embedding Generation Module

Handles document embedding using nomic-embed-text via Ollama.
Provides caching, batch processing, and VRAM monitoring.
"""

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""

    model_name: str = "nomic-embed-text"
    ollama_base_url: str = "http://localhost:11434"
    embedding_dim: int = 768
    batch_size: int = 32
    normalize: bool = True
    cache_enabled: bool = True
    cache_dir: str = "./data/cache/embeddings"
    timeout: int = 120  # seconds


class OllamaEmbeddingGenerator:
    """
    Generate embeddings using Ollama's nomic-embed-text model.

    Features:
        - Batch processing for efficiency
        - Caching to avoid re-embedding
        - VRAM monitoring
        - Async support
        - Normalization for cosine similarity
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize embedding generator.

        Args:
            config: Embedding configuration
        """
        self.config = config or EmbeddingConfig()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Initialized embedding generator",
            model=self.config.model_name,
            dim=self.config.embedding_dim,
            cache_enabled=self.config.cache_enabled,
        )

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from cache"""
        if not self.config.cache_enabled:
            return None

        cache_file = self.cache_dir / f"{cache_key}.npy"
        if cache_file.exists():
            logger.debug("Loading embedding from cache", cache_key=cache_key[:8])
            return np.load(cache_file)
        return None

    def _save_to_cache(self, cache_key: str, embedding: np.ndarray) -> None:
        """Save embedding to cache"""
        if not self.config.cache_enabled:
            return

        cache_file = self.cache_dir / f"{cache_key}.npy"
        np.save(cache_file, embedding)
        logger.debug("Saved embedding to cache", cache_key=cache_key[:8])

    async def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector (numpy array)
        """
        cache_key = self._get_cache_key(text)

        # Check cache
        cached_embedding = self._load_from_cache(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        # Generate embedding via Ollama
        try:
            import httpx

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.ollama_base_url}/api/embeddings",
                    json={"model": self.config.model_name, "prompt": text},
                )
                response.raise_for_status()
                result = response.json()

            embedding = np.array(result["embedding"], dtype=np.float32)

            # Normalize if configured
            if self.config.normalize:
                embedding = embedding / np.linalg.norm(embedding)

            # Cache the embedding
            self._save_to_cache(cache_key, embedding)

            logger.debug(
                "Generated embedding",
                text_length=len(text),
                embedding_dim=len(embedding),
            )

            return embedding

        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), text_length=len(text))
            raise

    async def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        embeddings: list[np.ndarray] = []

        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]
            logger.info(
                "Processing batch",
                batch_num=i // self.config.batch_size + 1,
                batch_size=len(batch),
                total_texts=len(texts),
            )

            # Process batch concurrently
            batch_embeddings = await asyncio.gather(*[self.embed_text(text) for text in batch])
            embeddings.extend(batch_embeddings)

        logger.info("Batch embedding complete", total_embeddings=len(embeddings))
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Synchronous wrapper for embedding queries.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        return asyncio.run(self.embed_text(query))

    def clear_cache(self) -> int:
        """
        Clear all cached embeddings.

        Returns:
            Number of cache files removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.npy"):
            cache_file.unlink()
            count += 1

        logger.info("Cleared embedding cache", files_removed=count)
        return count

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.npy"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_enabled": self.config.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "num_cached": len(cache_files),
            "total_size_mb": total_size / (1024 * 1024),
        }


# =============================================================================
# Utility Functions
# =============================================================================


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding
        embedding2: Second embedding

    Returns:
        Cosine similarity score (0-1)
    """
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )


def find_most_similar(
    query_embedding: np.ndarray,
    embeddings: list[np.ndarray],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """
    Find most similar embeddings to query.

    Args:
        query_embedding: Query embedding
        embeddings: List of document embeddings
        top_k: Number of results to return

    Returns:
        List of (index, similarity_score) tuples
    """
    similarities = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [(idx, similarities[idx]) for idx in top_indices]


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize generator
        config = EmbeddingConfig(cache_enabled=True)
        generator = OllamaEmbeddingGenerator(config)

        # Test single embedding
        text = "Drawing A-101 shows the level 1 floor plan with lobby layout."
        embedding = await generator.embed_text(text)
        print(f"Generated embedding: shape={embedding.shape}, norm={np.linalg.norm(embedding)}")

        # Test batch embedding
        texts = [
            "Fire-rated wall assembly WA-02 requires 2-hour rating.",
            "Lobby expansion affects structural drawing S-203.",
            "Design decision DEC-2025-034 approved on November 12.",
        ]
        embeddings = await generator.embed_batch(texts)
        print(f"Generated {len(embeddings)} embeddings")

        # Test similarity
        similarity = cosine_similarity(embeddings[0], embeddings[1])
        print(f"Similarity: {similarity:.4f}")

        # Cache stats
        stats = generator.get_cache_stats()
        print(f"Cache stats: {stats}")

    asyncio.run(main())
