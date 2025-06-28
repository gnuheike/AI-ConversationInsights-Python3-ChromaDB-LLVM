![Telegram Analyze](https://raw.githubusercontent.com/gnuheike/llvm_telegram_analyzer/refs/heads/main/logo.jpg "Telegram Analyzer")

# Telegram Analyzer

A Python application for analyzing Telegram chat messages using ChromaDB and LLMs. This tool analyzes Telegram chat exports to answer questions about
conversation patterns using embeddings and locally-run LLMs.

## Project Purpose

Telegram Analyzer is designed to help users extract insights from their Telegram conversations without compromising privacy. It processes JSON exports of
Telegram chats, stores them in a vector database (ChromaDB), and allows users to ask natural language questions about the content. The tool runs entirely
locally, ensuring that sensitive conversation data never leaves your machine.

## Overview

Telegram Analyzer is a tool that allows you to:

1. Parse JSON Telegram message exports
2. Load messages into ChromaDB for semantic search
3. Query the database to ask questions about the conversation
4. Generate answers using Ollama LLM models

## Features

- **Semantic Search**: Uses embeddings to find relevant messages based on meaning, not just keywords
- **Local Execution**: Runs entirely on your machine with no data sent to external services
- **Batch Processing**: Process multiple questions at once for efficient analysis
- **Customizable Models**: Works with various Ollama models to balance speed and accuracy
- **Privacy-Focused**: Designed with data privacy as a core principle
- **Detailed Output**: Provides answers with metadata about processing time and relevant message count

## How to use

1. Export your Telegram messages to a JSON file (click 3 dots in the Telegram chat, export messages to JSON without any attachments)
2. Process messages to store the vectors in ChromaDB (see "Loading Data" section below)
3. Use LLMs to query the messages using ChromaDB as context (see "Querying" section below)

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

To load Telegram messages from a JSON export file into ChromaDB:

```bash
python main.py load result.json --collection my_chat --batch-size 1000
```

This will process the messages in batches of 1000 and store them in a ChromaDB collection named "my_chat". The process includes:

1. Parsing the JSON file to extract messages
2. Converting messages to embeddings using a sentence transformer model
3. Storing the embeddings and original messages in ChromaDB for semantic search

You'll see progress logs as the data is processed, and a final confirmation when loading is complete:

```
INFO: Loading messages from result.json
INFO: Loaded 15423 messages from JSON file
INFO: Processing batch 1/16 (1000 messages)
...
INFO: Successfully loaded 15423 messages into collection my_chat
```

Options:

- `--collection`: Name of the ChromaDB collection (default: "telegram_messages")
- `--batch-size`: Number of messages to process in each batch (default: 5000)
- `--no-reset`: Don't reset the collection before loading (useful for adding new messages to an existing collection)

### Querying

To ask a question about the messages:

```bash
python main.py query "What topics were most frequently discussed?" --collection my_chat --output answer.md
```

This will:

1. Find the most relevant messages related to your question
2. Use the Ollama LLM to generate a comprehensive answer based on those messages
3. Save the answer to answer.md

Example output in the terminal:

```
================================================================================
Question: What topics were most frequently discussed?
================================================================================
Answer: Based on the conversation history, the most frequently discussed topics include:

1. Project planning and development - There are numerous discussions about timelines, 
   feature implementation, and development progress.

2. Technical issues - The conversation contains many exchanges about debugging problems, 
   code reviews, and technical solutions.

3. Meeting coordination - Team members frequently discuss scheduling meetings, 
   sharing agendas, and following up on action items.
...
================================================================================
Processing time: 5.23 seconds
Relevant messages: 1000
================================================================================
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

### Processing Query Sets

Process predefined sets of questions from Python files in the 'queries' folder:

```bash
python main.py process-queries
```

This command will:

1. Scan the 'queries' folder for Python files containing question sets
2. Allow you to select a specific query set or process a specified file
3. Process each question in the selected set using the QueryProcessor
4. Save the results to a Markdown file with the query set name and date

Example output in the terminal:

```
Found 10 query file(s) to process

Available query sets:
1. Couple Queries (couple)
   Queries for analyzing relationships between two people.

2. Team Queries (team)
   Queries for analyzing team communication and dynamics.

...

Select a query set (number) or 'q' to quit: 1
Created output file: couple_results_2023-11-15.md
Processing question 1/55: 'What did the husband and wife discuss regarding dinner plans?'
Processed 1/55: 'What did the husband and wife discuss regarding dinner...' (3.45s)
...
Query set processed. Processed 55/55 questions. Results saved to couple_results_2023-11-15.md
```

The output file will contain:
- The title and description of the query set
- The date of analysis
- Each question followed by its answer

Options:

- `--file`: Specific query file to process (default: interactive selection)
- `--collection`: Name of the ChromaDB collection (default: "telegram_messages")
- `--model`: Name of the Ollama model (default: "deepseek-r1:32b-qwen-distill-q8_0")
- `--top-k`: Number of relevant messages to include in the context (default: 1000)

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

## Data Privacy

This tool is designed to run entirely locally and does not send data to any cloud providers. All processing happens on your machine, ensuring that your
sensitive conversation data remains private. Key privacy features include:

- **Local Execution**: All data processing and LLM inference runs on your local machine
- **No Data Transmission**: No data is sent to external servers or APIs
- **Persistent Storage Control**: You control where the data is stored on your system
- **No Account Required**: No need to create accounts or authenticate with external services

Users are responsible for ensuring that sensitive data is not uploaded to public repositories or shared inappropriately. Always be cautious when sharing
analysis results that might contain private information.

## Limitations

Current limitations of the tool include:

- **JSON Format Only**: Currently supports only JSON exports from Telegram Desktop
- **Text-Only Analysis**: Media files (images, videos, audio) are not processed
- **Local LLM Dependency**: Requires Ollama to be installed and running locally
- **Resource Intensive**: Processing large chat histories may require significant memory and storage
- **English-Centric**: Works best with English language content, though other languages are supported

## Contributing

Contributions are welcome! If you'd like to improve Telegram Analyzer, please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For bug reports, feature requests, or questions, please open an issue in the repository.

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
