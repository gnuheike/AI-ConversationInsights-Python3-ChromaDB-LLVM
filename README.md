# Telegram Analyzer

Python application for analyzing Telegram chat messages using ChromaDB and LLMs.
Application IS INTENDED TO USE AT THE LOCAL ENVIRONMENT, without sending data to ANY cloud providers ensuring security and confidentiality of the private
conversatoin and sensitive questions.

## Overview

Telegram Analyzer is a tool that allows you to:

1. Parse JSON Telegram message exports
2. Load messages into ChromaDB for semantic search
3. Query the database to ask questions about the conversation
4. Generate answers using Ollama LLM models

## How to use

1. Export your telegram messages to the result.json file (click 3 dots in the telegram chat, export messages to json without any attachments)
2. Process messages to store the vectors to ChromaDB (Loading Data in this readme)
3. Use LLVM to query the messages (examples in the queries folder) using the chromaDB as context (Querying is this readme)

## Installation

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running locally

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telegram-analyzer
   ```

2. Set up your configuration (see [Configuration](#configuration) section)

3. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Pull the required Ollama model (you can refer to https://www.reddit.com/r/LocalLLaMA/comments/16y95hk/a_starter_guide_for_playing_with_your_own_local_ai/ to
   select the model)
   ```bash
   ollama pull deepseek-r1:32b-qwen-distill-q8_0
   ```
   You can configure a different model in `telegram_analyzer/config.py`.

## Usage

The application provides a command-line interface with several commands:

### Loading Data

Load Telegram messages from a JSON export file into ChromaDB:

```bash
python main.py load result.json
```

Options:

- `--collection`: Name of the ChromaDB collection (default: "telegram_messages")
- `--batch-size`: Number of messages to process in each batch (default: 5000)
- `--no-reset`: Don't reset the collection before loading

### Querying

Ask a question about the Telegram messages:

```bash
python main.py query "What topics were most frequently discussed?"
```

Options:

- `--collection`: Name of the ChromaDB collection (default: "telegram_messages")
- `--model`: Name of the Ollama model (default: "deepseek-r1:32b-qwen-distill-q8_0")
- `--top-k`: Number of relevant messages to include in the context (default: 1000)
- `--output`: Path to save the answer (default: print to stdout)

### Batch Processing

Process multiple questions from a file:

```bash
python main.py batch questions.txt --output results.md
```

Options:

- `--collection`: Name of the ChromaDB collection (default: "telegram_messages")
- `--model`: Name of the Ollama model (default: "deepseek-r1:32b-qwen-distill-q8_0")
- `--top-k`: Number of relevant messages to include in the context (default: 1000)
- `--output`: Path to save the answers in markdown format (default: "telegram_analysis_results.md")

### Checking Database

Check the status of the ChromaDB collection:

```bash
python main.py check
```

Options:

- `--collection`: Name of the ChromaDB collection (default: "telegram_messages")

## Configuration

The application uses a configuration file located at `telegram_analyzer/config.py`. To set up your configuration:

1. Copy the example configuration file:
   ```bash
   cp telegram_analyzer/config.example.py telegram_analyzer/config.py
   ```

2. Edit `config.py` to customize the settings according to your needs:
    - **ChromaDB settings**: Change persistence directory or collection name
    - **Sentence Transformer model**: Select a different embedding model or change the device (cpu/cuda/mps)
    - **Query parameters**: Adjust the number of messages to include in context
    - **Ollama model settings**: Change the model or adjust generation parameters (temperature, context size)
    - **Output and logging settings**: Modify output file paths and log levels

The example configuration file includes detailed comments explaining each setting and its possible values.

## Project Structure

```
telegram_analyzer/
├── __init__.py          # Package initialization
├── config.py            # Configuration settings
├── logging.py           # Logging setup
├── data_processing.py   # Telegram data processing
├── database.py          # ChromaDB interaction
├── query.py             # Query processing and answer generation
└── cli.py               # Command-line interface
```

## Improvements

This application has been refactored following modern Python practices:

1. **Modular Architecture**: Code organized into logical modules with clear responsibilities
2. **Type Hints**: All functions and methods include type annotations
3. **Comprehensive Documentation**: Docstrings for all modules, classes, and functions
4. **Error Handling**: Robust error handling throughout the codebase
5. **Logging**: Proper logging instead of print statements
6. **Command-line Interface**: Well-structured CLI with subcommands and help text
7. **Configuration Management**: Centralized configuration with sensible defaults
8. **Batch Processing**: Support for processing multiple questions
9. **Performance Metrics**: Timing and metadata for performance analysis
10. **Code Quality**: Adherence to PEP 8 style guidelines

