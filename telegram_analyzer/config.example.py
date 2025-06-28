"""
Configuration module for the Telegram Analyzer package.

This module contains all configuration settings for the application,
including ChromaDB settings, model configurations, and query parameters.

HOW TO USE:
1. Copy this file to config.py
2. Adjust the settings according to your needs and environment
3. Make sure to set the correct paths and model settings for your system
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Base directory for data storage
# This automatically sets the base directory to the parent directory of this file
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Directory for storing data files
DATA_DIR = BASE_DIR / "data"

# ChromaDB settings
# These settings control how ChromaDB stores and manages your vector database
CHROMADB_SETTINGS: Dict[str, Any] = {
    # Whether to persist the database to disk (set to False for in-memory only)
    "is_persistent": True,
    # Directory where ChromaDB will store its data
    "persist_directory": str(BASE_DIR / "chromadb_data")
}
# Name of the collection in ChromaDB where telegram messages will be stored
COLLECTION_NAME: str = "telegram_messages"

# Sentence Transformer model settings
# These settings control which embedding model is used and how it's run
SENTENCE_MODEL: Dict[str, str] = {
    # The model to use for generating embeddings
    # You can use other models from https://huggingface.co/models?library=sentence-transformers
    "name": "mixedbread-ai/mxbai-embed-large-v1",
    # Device to run the model on:
    # - 'cpu': Use CPU (works on all systems but slower)
    # - 'cuda': Use NVIDIA GPU (requires CUDA setup)
    # - 'mps': Use Apple Silicon GPU (for M1/M2 Macs)
    "device": "mps"
}

# Query settings
# How many relevant messages from the conversation should be attached as context to the model prompt
# Higher values provide more context but may slow down processing
QUERY_TOP_K: int = 200
# How many messages to include before and after each found message for better context
# This helps maintain conversation flow in the context
QUERY_CONTEXT_N: int = 4

# Ollama model settings
# Note: You need to perform "ollama pull <model name>" before using
OLLAMA_MODEL: Dict[str, Any] = {
    # The name of the model to use
    # You can see available models with "ollama list"
    "name": "deepseek-r1:32b-qwen-distill-q8_0",
    # Model generation options
    "options": {
        # Controls randomness: higher values (e.g., 0.8) make output more random,
        # lower values (e.g., 0.2) make it more deterministic
        "temperature": 0.6,
        # Nucleus sampling: only consider tokens with top_p cumulative probability
        # Higher values (0.95) include more low-probability tokens
        "top_p": 0.95,
        # Maximum context length (in tokens)
        # This should match your model's context window size
        "num_ctx": 32768
    }
}

# Output settings
# Default file path for saving analysis results
OUTPUT_FILE: str = str(BASE_DIR / "telegram_analysis_results.md")

# Logging settings
# Log level determines which messages are recorded (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = "INFO"
# Format for log messages
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# File to save logs (set to None to disable file logging)
LOG_FILE: Optional[str] = str(BASE_DIR / "telegram_analyzer.log")

# Prompt templates
# Template for generating answers from the LLM
# {context} will be replaced with relevant messages
# {question} will be replaced with the user's question
ANSWER_PROMPT_TEMPLATE: str = """
You are an assistant analyzing Telegram messages. 
Use the provided context to answer the question accurately and concisely. 
Consider the nature of messaging platforms. 
Don't make assumptions; base your answer only on the provided information. 
If the answer is unclear, state this and provide a reasonable answer based on logical analysis. 
Include the date of the conversation if relevant.
Please provide your answer in Russian language.

Context:
{context}

Question: 
{question}

Answer:"""
