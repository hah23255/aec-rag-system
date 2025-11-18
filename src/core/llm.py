"""
LLM Integration Module

Handles LLM inference using Llama-3.1-8B via Ollama.
Provides prompt templating, streaming, and token usage tracking.
"""

import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
import structlog
from enum import Enum

logger = structlog.get_logger(__name__)


class PromptTemplate(str, Enum):
    """Pre-defined prompt templates for AEC RAG queries"""

    FACTUAL = """You are an expert assistant for an AEC (Architecture, Engineering, Construction) design management system.

Context from project documents:
{context}

User question: {question}

Provide a factual answer based ONLY on the context above. If the context doesn't contain the answer, say "I don't have enough information to answer this question."

Answer:"""

    IMPACT_ANALYSIS = """You are analyzing design change impacts in an AEC project.

Context:
{context}

Design change: {question}

Analyze which drawings, components, or systems will be affected by this change. List specific impacts and their severity (minor, moderate, major).

Impact Analysis:"""

    VERSION_COMPARISON = """You are comparing different versions of an architectural drawing.

Version Information:
{context}

Question: {question}

Compare the versions and explain what changed between them. Focus on functional changes, not administrative details.

Comparison:"""

    CODE_COMPLIANCE = """You are reviewing code compliance for building components.

Building Codes and Requirements:
{context}

Component/Question: {question}

Determine if the component meets applicable building codes. Cite specific code sections.

Compliance Analysis:"""

    QUERY_ROUTING = """Analyze this user query and determine its intent.

Query: {question}

Classify the intent as one of:
- factual: Simple fact retrieval
- impact_analysis: Understanding effects of changes
- version_comparison: Comparing drawing versions
- code_compliance: Code requirement questions
- multi_hop: Requires reasoning across multiple documents

Intent:"""


@dataclass
class LLMConfig:
    """Configuration for LLM generation"""

    model_name: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 1024
    timeout: int = 120  # seconds
    stream: bool = False


class OllamaLLM:
    """
    LLM wrapper for Ollama (Llama-3.1-8B).

    Features:
        - Prompt templating
        - Streaming support
        - Token usage tracking
        - Temperature control
        - Async generation
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM wrapper.

        Args:
            config: LLM configuration
        """
        self.config = config or LLMConfig()
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        logger.info(
            "Initialized LLM",
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

    def format_prompt(
        self,
        question: str,
        context: str,
        template: PromptTemplate = PromptTemplate.FACTUAL,
    ) -> str:
        """
        Format prompt using template.

        Args:
            question: User question
            context: Retrieved context
            template: Prompt template to use

        Returns:
            Formatted prompt string
        """
        return template.value.format(context=context, question=question)

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion for prompt.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text
        """
        try:
            import httpx

            temp = temperature if temperature is not None else self.config.temperature
            max_tok = max_tokens if max_tokens is not None else self.config.max_tokens

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.ollama_base_url}/api/generate",
                    json={
                        "model": self.config.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temp,
                            "top_p": self.config.top_p,
                            "num_predict": max_tok,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()

            generated_text = result["response"]

            # Track token usage (approximation)
            prompt_tokens = len(prompt.split())  # Rough estimate
            completion_tokens = len(generated_text.split())
            self.token_usage["prompt_tokens"] += prompt_tokens
            self.token_usage["completion_tokens"] += completion_tokens
            self.token_usage["total_tokens"] += prompt_tokens + completion_tokens

            logger.info(
                "Generated completion",
                prompt_length=len(prompt),
                response_length=len(generated_text),
                estimated_tokens=prompt_tokens + completion_tokens,
            )

            return generated_text

        except Exception as e:
            logger.error("Failed to generate completion", error=str(e))
            raise

    async def generate_stream(
        self,
        prompt: str,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming.

        Args:
            prompt: Input prompt
            temperature: Override default temperature

        Yields:
            Generated text chunks
        """
        try:
            import httpx

            temp = temperature if temperature is not None else self.config.temperature

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.config.ollama_base_url}/api/generate",
                    json={
                        "model": self.config.model_name,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": temp,
                            "top_p": self.config.top_p,
                            "num_predict": self.config.max_tokens,
                        },
                    },
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line:
                            import json

                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]

        except Exception as e:
            logger.error("Failed to generate streaming completion", error=str(e))
            raise

    async def generate_with_context(
        self,
        question: str,
        context_chunks: List[str],
        template: PromptTemplate = PromptTemplate.FACTUAL,
        max_context_tokens: int = 2048,
    ) -> str:
        """
        Generate answer using retrieved context.

        Args:
            question: User question
            context_chunks: Retrieved context chunks
            template: Prompt template
            max_context_tokens: Maximum tokens for context

        Returns:
            Generated answer
        """
        # Combine context chunks (respecting token limit)
        context = "\n\n".join(context_chunks[:10])  # Limit to top 10 chunks

        # Truncate context if too long (rough estimate)
        if len(context.split()) > max_context_tokens:
            words = context.split()[:max_context_tokens]
            context = " ".join(words) + "..."

        # Format prompt
        prompt = self.format_prompt(question, context, template)

        # Generate answer
        answer = await self.generate(prompt)

        logger.info(
            "Generated answer with context",
            question_length=len(question),
            context_chunks=len(context_chunks),
            answer_length=len(answer),
        )

        return answer

    def get_token_usage(self) -> Dict[str, int]:
        """
        Get cumulative token usage.

        Returns:
            Dictionary with token counts
        """
        return self.token_usage.copy()

    def reset_token_usage(self) -> None:
        """Reset token usage counters"""
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        logger.info("Reset token usage counters")


# =============================================================================
# Utility Functions
# =============================================================================


async def classify_query_intent(llm: OllamaLLM, question: str) -> str:
    """
    Classify user query intent.

    Args:
        llm: LLM instance
        question: User question

    Returns:
        Intent classification
    """
    prompt = PromptTemplate.QUERY_ROUTING.value.format(question=question, context="")
    result = await llm.generate(prompt, temperature=0.0, max_tokens=50)

    # Parse intent from result
    intent = result.strip().split("\n")[0].strip().lower()

    # Validate intent
    valid_intents = ["factual", "impact_analysis", "version_comparison", "code_compliance", "multi_hop"]
    for valid in valid_intents:
        if valid in intent:
            return valid

    return "factual"  # Default


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize LLM
        config = LLMConfig(temperature=0.1, max_tokens=512)
        llm = OllamaLLM(config)

        # Test simple generation
        prompt = "What are the benefits of using GraphRAG for AEC projects?"
        answer = await llm.generate(prompt)
        print(f"Answer: {answer}\n")

        # Test with context
        question = "What is the fire rating requirement for wall WA-02?"
        context_chunks = [
            "Wall Assembly WA-02 is a fire-rated partition wall.",
            "Per IBC Section 705.5, fire walls require 2-hour fire resistance rating.",
            "WA-02 uses Type X Firecode gypsum board on metal studs to achieve 2-hour rating.",
        ]

        answer = await llm.generate_with_context(
            question, context_chunks, template=PromptTemplate.CODE_COMPLIANCE
        )
        print(f"Question: {question}")
        print(f"Answer: {answer}\n")

        # Test query classification
        intent = await classify_query_intent(llm, "What drawings are affected by the lobby expansion?")
        print(f"Query intent: {intent}\n")

        # Token usage
        usage = llm.get_token_usage()
        print(f"Token usage: {usage}")

    asyncio.run(main())
