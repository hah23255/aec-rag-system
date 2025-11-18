"""
GraphRAG Core Module

Integrates nano-graphrag or LinearRAG for AEC document processing.
Handles graph construction, entity extraction, and two-stage retrieval.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class GraphRAGConfig:
    """Configuration for GraphRAG system"""

    # Framework selection
    framework: str = "nano-graphrag"  # nano-graphrag or linearrag

    # Storage
    working_dir: str = "./data/graphrag"
    graph_storage: str = "networkx"  # networkx (file) or neo4j (database)

    # Models
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    llm_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"

    # Retrieval
    top_k: int = 5
    mode: str = "global"  # local, global, naive
    min_score: float = 0.7

    # Neo4j (optional)
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None


class AECGraphRAG:
    """
    AEC-specific GraphRAG implementation.

    Features:
        - Document ingestion with entity extraction
        - Graph construction (entities + relationships)
        - Two-stage retrieval (entity activation + passage retrieval)
        - Semantic bridging for multi-hop queries
        - Version tracking (SUPERSEDES relationships)
    """

    def __init__(self, config: Optional[GraphRAGConfig] = None):
        """
        Initialize GraphRAG system.

        Args:
            config: GraphRAG configuration
        """
        self.config = config or GraphRAGConfig()
        self.rag = None
        self.initialized = False

        # Create working directory
        working_path = Path(self.config.working_dir)
        working_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Initializing GraphRAG",
            framework=self.config.framework,
            storage=self.config.graph_storage,
            working_dir=self.config.working_dir,
        )

    async def initialize(self) -> None:
        """Initialize the GraphRAG framework"""
        if self.initialized:
            return

        if self.config.framework == "nano-graphrag":
            await self._initialize_nano_graphrag()
        elif self.config.framework == "linearrag":
            await self._initialize_linearrag()
        else:
            raise ValueError(f"Unknown framework: {self.config.framework}")

        self.initialized = True
        logger.info("GraphRAG initialized successfully")

    async def _initialize_nano_graphrag(self) -> None:
        """Initialize nano-graphrag framework"""
        try:
            from nano_graphrag import GraphRAG, QueryParam
            from nano_graphrag._llm import OllamaEmbedding, OllamaLLM
            from nano_graphrag._storage import NetworkXStorage

            # Configure storage backend
            if self.config.graph_storage == "networkx":
                storage_cls = NetworkXStorage
                storage_kwargs = {}
            elif self.config.graph_storage == "neo4j":
                from nano_graphrag._storage import Neo4jStorage

                storage_cls = Neo4jStorage
                storage_kwargs = {
                    "uri": self.config.neo4j_uri,
                    "user": self.config.neo4j_user,
                    "password": self.config.neo4j_password,
                }
            else:
                raise ValueError(f"Unknown storage: {self.config.graph_storage}")

            # Initialize GraphRAG
            self.rag = GraphRAG(
                working_dir=self.config.working_dir,
                embedding_func=OllamaEmbedding(
                    model=self.config.embedding_model,
                    embed_dim=self.config.embedding_dim,
                    base_url=self.config.ollama_base_url,
                ),
                best_model_func=OllamaLLM(
                    model=self.config.llm_model, base_url=self.config.ollama_base_url
                ),
                graph_storage_cls=storage_cls,
                **storage_kwargs,
            )

            logger.info("Initialized nano-graphrag")

        except ImportError as e:
            logger.error("Failed to import nano-graphrag", error=str(e))
            raise RuntimeError("nano-graphrag not installed. Run: pip install nano-graphrag") from e

    async def _initialize_linearrag(self) -> None:
        """Initialize LinearRAG framework"""
        # Placeholder for LinearRAG integration
        logger.warning("LinearRAG integration not yet implemented, using nano-graphrag")
        await self._initialize_nano_graphrag()

    async def insert_document(
        self, document_text: str, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Insert document into graph.

        Args:
            document_text: Document content
            metadata: Optional metadata (drawing number, version, etc.)

        Returns:
            Document ID
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Add metadata to document text for better entity extraction
            if metadata:
                enriched_text = self._enrich_document(document_text, metadata)
            else:
                enriched_text = document_text

            # Insert into graph (nano-graphrag handles entity extraction)
            await self.rag.ainsert(enriched_text)

            logger.info(
                "Inserted document",
                text_length=len(document_text),
                has_metadata=metadata is not None,
            )

            return metadata.get("id", "unknown") if metadata else "unknown"

        except Exception as e:
            logger.error("Failed to insert document", error=str(e))
            raise

    def _enrich_document(self, text: str, metadata: dict[str, Any]) -> str:
        """
        Enrich document text with structured metadata.

        Args:
            text: Original document text
            metadata: Metadata dictionary

        Returns:
            Enriched text
        """
        # Build structured header
        header_parts = []

        if "drawing_number" in metadata:
            header_parts.append(f"Drawing Number: {metadata['drawing_number']}")

        if "version" in metadata:
            header_parts.append(f"Version: {metadata['version']}")

        if "title" in metadata:
            header_parts.append(f"Title: {metadata['title']}")

        if "date" in metadata:
            header_parts.append(f"Date: {metadata['date']}")

        if "discipline" in metadata:
            header_parts.append(f"Discipline: {metadata['discipline']}")

        header = "\n".join(header_parts)

        # Combine header + text
        return f"{header}\n\n{text}"

    async def query(
        self,
        question: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Query the graph with natural language.

        Args:
            question: User question
            mode: Query mode (local, global, naive)
            top_k: Number of results

        Returns:
            Query result with answer and sources
        """
        if not self.initialized:
            await self.initialize()

        try:
            from nano_graphrag import QueryParam

            mode = mode or self.config.mode
            top_k = top_k or self.config.top_k

            # Execute query
            result = await self.rag.aquery(question, param=QueryParam(mode=mode, top_k=top_k))

            logger.info(
                "Executed query",
                question_length=len(question),
                mode=mode,
                top_k=top_k,
                result_length=len(result) if isinstance(result, str) else 0,
            )

            return {"answer": result, "mode": mode, "top_k": top_k}

        except Exception as e:
            logger.error("Failed to execute query", error=str(e), question=question)
            raise

    async def get_version_history(self, drawing_number: str) -> list[dict[str, Any]]:
        """
        Get version history for a drawing.

        Args:
            drawing_number: Drawing number (e.g., "A-101")

        Returns:
            List of versions with metadata
        """
        query = f"What are all the versions of drawing {drawing_number}? List them chronologically."
        result = await self.query(query, mode="global")

        # Parse versions from result (would need more sophisticated parsing in production)
        return [{"answer": result["answer"]}]

    async def analyze_impact(self, change_description: str) -> dict[str, Any]:
        """
        Analyze impact of a design change.

        Args:
            change_description: Description of change

        Returns:
            Impact analysis with affected drawings/components
        """
        query = f"What drawings and components are affected by: {change_description}"
        result = await self.query(query, mode="global", top_k=10)

        return {
            "change": change_description,
            "analysis": result["answer"],
            "mode": "impact_analysis",
        }

    async def check_code_compliance(
        self, component_id: str, requirements: list[str]
    ) -> dict[str, Any]:
        """
        Check code compliance for a component.

        Args:
            component_id: Component identifier
            requirements: List of requirement descriptions

        Returns:
            Compliance check results
        """
        query = f"Does component {component_id} meet the following requirements: {', '.join(requirements)}?"
        result = await self.query(query, mode="local")

        return {
            "component": component_id,
            "requirements": requirements,
            "compliance_check": result["answer"],
        }

    def get_stats(self) -> dict[str, Any]:
        """
        Get GraphRAG statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "framework": self.config.framework,
            "storage": self.config.graph_storage,
            "working_dir": self.config.working_dir,
            "initialized": self.initialized,
            "embedding_model": self.config.embedding_model,
            "llm_model": self.config.llm_model,
        }


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize GraphRAG
        config = GraphRAGConfig(
            framework="nano-graphrag",
            graph_storage="networkx",
            working_dir="./data/test_graphrag",
        )
        graph_rag = AECGraphRAG(config)
        await graph_rag.initialize()

        # Insert sample document
        doc_text = """
        Drawing A-101 Revision 3 (Architectural Floor Plan - Level 1)
        Date: 2025-11-14

        This revision supersedes A-101 Revision 2.
        Changes: Lobby layout expanded from 800 SF to 1200 SF with double entry doors.

        Wall Assembly WA-02 (fire-rated partition) is located in the main lobby.
        WA-02 requires 2-hour fire rating per IBC Section 705.5.
        Construction: Type X Firecode gypsum board on metal studs.

        This change affects Structural Drawing S-203 (beam modifications required).
        """

        metadata = {
            "id": "A-101-v3",
            "drawing_number": "A-101",
            "version": "3",
            "discipline": "A",
            "title": "Level 1 Floor Plan - Lobby Expansion",
            "date": "2025-11-14",
        }

        doc_id = await graph_rag.insert_document(doc_text, metadata)
        print(f"Inserted document: {doc_id}\n")

        # Query examples
        queries = [
            "What is the latest version of drawing A-101?",
            "What changed between A-101 v2 and v3?",
            "What are the fire rating requirements for wall WA-02?",
            "Which structural drawings are affected by the lobby expansion?",
        ]

        for q in queries:
            result = await graph_rag.query(q, mode="global")
            print(f"Q: {q}")
            print(f"A: {result['answer']}\n")

        # Stats
        stats = graph_rag.get_stats()
        print(f"GraphRAG Stats: {stats}")

    asyncio.run(main())
