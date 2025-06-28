"""
Query module for the Telegram Analyzer package.

This module provides functionality for querying ChromaDB and generating
answers to questions about Telegram messages using LLMs.
"""

import re
import time
from typing import Dict, List, Any, Optional

import ollama

from telegram_analyzer import config
from telegram_analyzer.database import query_messages
from telegram_analyzer.logging import logger
from telegram_analyzer.message import Message


class QueryProcessor:
    """
    Class for processing queries and generating answers.
    """

    def __init__(
            self,
            collection_name: str = config.COLLECTION_NAME,
            model_name: str = config.OLLAMA_MODEL["name"],
            model_options: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the QueryProcessor.

        Args:
            collection_name: Name of the ChromaDB collection
            model_name: Name of the Ollama model
            model_options: Options for the Ollama model
        """
        self.collection_name = collection_name
        self.model_name = model_name
        self.model_options = model_options or config.OLLAMA_MODEL["options"]
        logger.info(f"Initialized QueryProcessor with model: {self.model_name}")

    def clean_response(self, response: str) -> str:
        """
        Clean the response from the LLM.

        Args:
            response: The raw response from the LLM

        Returns:
            The cleaned response
        """
        # Remove content between <think>...</think> tags
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        # Remove "Answer: " prefix if present
        cleaned = re.sub(r'^Answer:\s*', '', cleaned)
        # Trim whitespace
        cleaned = cleaned.strip()
        return cleaned

    def format_context(self, messages: List[Message]) -> str:
        """
        Format messages as context for the LLM.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted context string
        """
        return "\n".join([
            msg.__str__()
            for msg in messages
        ])

    def answer_question(
            self,
            question: str,
            top_k: int = config.QUERY_TOP_K
    ) -> Dict[str, Any]:
        """
        Answer a question about Telegram messages.

        Args:
            question: The question to answer
            top_k: Number of relevant messages to include in the context

        Returns:
            A dictionary containing the question, answer, and metadata
        """
        logger.info(f"Processing question: '{question}'")
        start_time = time.time()

        try:
            # Query for relevant messages
            relevant_messages = query_messages(
                query_text=question,
                collection_name=self.collection_name,
                top_k=top_k
            )

            logger.info(f"Retrieved {len(relevant_messages)} relevant messages")

            if not relevant_messages:
                logger.warning("No relevant messages found for this question")
                return {
                    "question": question,
                    "answer": "No relevant information found to answer this question.",
                    "metadata": {
                        "processing_time": time.time() - start_time,
                        "relevant_messages_count": 0
                    }
                }

            # Format context
            context = self.format_context(relevant_messages)

            # Create prompt
            prompt = config.ANSWER_PROMPT_TEMPLATE.format(
                context=context,
                question=question
            )

            # Generate answer
            logger.info(f"Sending request to Ollama with model: {self.model_name}")
            logger.info(f"Context window size for this question: {len(context)} characters")
            generation_start_time = time.time()

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options=self.model_options
            )

            generation_time = time.time() - generation_start_time
            logger.info(f"Received response from Ollama (length: {len(response['response'])} characters) in {generation_time:.2f} seconds")

            # Clean the response
            cleaned_response = self.clean_response(response['response'])

            # Calculate total processing time
            total_time = time.time() - start_time

            result = {
                "question": question,
                "answer": cleaned_response,
                "metadata": {
                    "processing_time": total_time,
                    "generation_time": generation_time,
                    "relevant_messages_count": len(relevant_messages),
                    "model": self.model_name
                }
            }

            logger.info(f"Question answered in {total_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"Error answering question: {e}", exc_info=True)
            error_time = time.time() - start_time
            return {
                "question": question,
                "answer": f"An error occurred while processing your question: {str(e)}",
                "metadata": {
                    "processing_time": error_time,
                    "error": str(e)
                }
            }


def answer_question(
        question: str,
        collection_name: str = config.COLLECTION_NAME,
        model_name: str = config.OLLAMA_MODEL["name"],
        top_k: int = config.QUERY_TOP_K
) -> str:
    """
    Answer a question about Telegram messages.

    This is a convenience function that creates a QueryProcessor
    and calls its answer_question method.

    Args:
        question: The question to answer
        collection_name: Name of the ChromaDB collection
        model_name: Name of the Ollama model
        top_k: Number of relevant messages to include in the context

    Returns:
        The answer to the question
    """
    processor = QueryProcessor(
        collection_name=collection_name,
        model_name=model_name
    )
    result = processor.answer_question(question=question, top_k=top_k)
    return result["answer"]
