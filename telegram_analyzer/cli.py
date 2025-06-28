"""
Command-line interface module for the Telegram Analyzer package.

This module provides command-line interfaces for the main functionality
of the application, including loading data, querying, checking the database,
and processing queries from the queries folder.

Available commands:
- load: Load Telegram messages into ChromaDB
- query: Query ChromaDB and answer a question
- check: Check the status of the ChromaDB collection
- batch: Process a batch of questions from a file
- process-queries: Process queries from the 'queries' folder
"""

import argparse
import importlib.util
import sys
from pathlib import Path

from telegram_analyzer import config
from telegram_analyzer.data_processing import load_telegram_messages
from telegram_analyzer.database import ChromaDBManager, load_into_chromadb
from telegram_analyzer.logging import logger
from telegram_analyzer.query import QueryProcessor


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.

    Returns:
        An ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Telegram Analyzer - Process and query Telegram chat data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Load data command
    load_parser = subparsers.add_parser(
        "load",
        help="Load Telegram messages into ChromaDB"
    )
    load_parser.add_argument(
        "json_file",
        help="Path to the Telegram chat JSON export file"
    )
    load_parser.add_argument(
        "--collection",
        default=config.COLLECTION_NAME,
        help="Name of the ChromaDB collection"
    )
    load_parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Number of messages to process in each batch"
    )
    load_parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't reset the collection before loading"
    )

    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query ChromaDB and answer a question"
    )
    query_parser.add_argument(
        "question",
        help="Question to answer"
    )
    query_parser.add_argument(
        "--collection",
        default=config.COLLECTION_NAME,
        help="Name of the ChromaDB collection"
    )
    query_parser.add_argument(
        "--model",
        default=config.OLLAMA_MODEL["name"],
        help="Name of the Ollama model"
    )
    query_parser.add_argument(
        "--top-k",
        type=int,
        default=config.QUERY_TOP_K,
        help="Number of relevant messages to include in the context"
    )
    query_parser.add_argument(
        "--output",
        help="Path to save the answer (default: print to stdout)"
    )

    # Check DB command
    check_parser = subparsers.add_parser(
        "check",
        help="Check the status of the ChromaDB collection"
    )
    check_parser.add_argument(
        "--collection",
        default=config.COLLECTION_NAME,
        help="Name of the ChromaDB collection"
    )

    # Batch query command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Process a batch of questions from a file"
    )
    batch_parser.add_argument(
        "questions_file",
        help="Path to a file containing questions (one per line)"
    )
    batch_parser.add_argument(
        "--collection",
        default=config.COLLECTION_NAME,
        help="Name of the ChromaDB collection"
    )
    batch_parser.add_argument(
        "--model",
        default=config.OLLAMA_MODEL["name"],
        help="Name of the Ollama model"
    )
    batch_parser.add_argument(
        "--top-k",
        type=int,
        default=config.QUERY_TOP_K,
        help="Number of relevant messages to include in the context"
    )
    batch_parser.add_argument(
        "--output",
        default=config.OUTPUT_FILE,
        help="Path to save the answers in markdown format"
    )

    # Process queries command
    process_queries_parser = subparsers.add_parser(
        "process-queries",
        help="Process queries from the 'queries' folder"
    )
    process_queries_parser.add_argument(
        "--file",
        help="Specific query file to process (default: process all Python files in the queries folder)"
    )
    process_queries_parser.add_argument(
        "--collection",
        default=config.COLLECTION_NAME,
        help="Name of the ChromaDB collection"
    )
    process_queries_parser.add_argument(
        "--model",
        default=config.OLLAMA_MODEL["name"],
        help="Name of the Ollama model"
    )
    process_queries_parser.add_argument(
        "--top-k",
        type=int,
        default=config.QUERY_TOP_K,
        help="Number of relevant messages to include in the context"
    )
    process_queries_parser.add_argument(
        "--output",
        default=config.OUTPUT_FILE,
        help="Path to save the answers in markdown format"
    )

    return parser


def handle_load(args: argparse.Namespace) -> int:
    """
    Handle the load command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        logger.info(f"Loading messages from {args.json_file}")
        messages = load_telegram_messages(args.json_file)
        logger.info(f"Loaded {len(messages)} messages from JSON file")

        count = load_into_chromadb(
            messages=messages,
            collection_name=args.collection,
            batch_size=args.batch_size,
            reset_collection=not args.no_reset
        )

        logger.info(f"Successfully loaded {count} messages into collection {args.collection}")
        return 0
    except Exception as e:
        logger.error(f"Error loading messages: {e}", exc_info=True)
        return 1


def handle_query(args: argparse.Namespace) -> int:
    """
    Handle the query command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        processor = QueryProcessor(
            collection_name=args.collection,
            model_name=args.model
        )

        result = processor.answer_question(
            question=args.question,
            top_k=args.top_k
        )

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Question\n\n{args.question}\n\n# Answer\n\n{result['answer']}\n")

            logger.info(f"Answer saved to {output_path}")
        else:
            print("\n" + "=" * 80)
            print(f"Question: {args.question}")
            print("=" * 80)
            print(f"Answer: {result['answer']}")
            print("=" * 80)
            print(f"Processing time: {result['metadata']['processing_time']:.2f} seconds")
            print(f"Relevant messages: {result['metadata']['relevant_messages_count']}")
            print("=" * 80 + "\n")

        return 0
    except Exception as e:
        logger.error(f"Error querying: {e}", exc_info=True)
        return 1


def handle_check(args: argparse.Namespace) -> int:
    """
    Handle the check command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        db_manager = ChromaDBManager(collection_name=args.collection)
        info = db_manager.get_collection_info()

        print("\n" + "=" * 80)
        print(f"Collection: {info['collection_name']}")
        print(f"Document count: {info['document_count']}")
        print(f"Persist directory: {info['persist_directory']}")
        print(f"Directory size: {info['directory_size_gb']:.2f} GB")
        print(f"Model: {info['model_name']}")
        print(f"Device: {info['device']}")
        print("=" * 80 + "\n")

        return 0
    except Exception as e:
        logger.error(f"Error checking database: {e}", exc_info=True)
        return 1


def handle_batch(args: argparse.Namespace) -> int:
    """
    Handle the batch command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Read questions from file
        questions_path = Path(args.questions_file)
        if not questions_path.exists():
            logger.error(f"Questions file not found: {questions_path}")
            return 1

        with open(questions_path, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]

        logger.info(f"Loaded {len(questions)} questions from {questions_path}")

        # Create output file if it doesn't exist
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not output_path.exists() or output_path.stat().st_size == 0:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Telegram Chat Analysis Results\n\n")
            logger.info(f"Created new output file: {output_path}")

        # Initialize query processor
        processor = QueryProcessor(
            collection_name=args.collection,
            model_name=args.model
        )

        # Process each question
        for i, question in enumerate(questions, 1):
            logger.info(f"Processing question {i}/{len(questions)}: '{question}'")

            try:
                result = processor.answer_question(
                    question=question,
                    top_k=args.top_k
                )

                # Append the answer to the output file
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(f"## {question}\n\n{result['answer']}\n\n")

                logger.info(f"Answer for question {i} saved to {output_path}")

                # Print progress
                print(f"Processed {i}/{len(questions)}: '{question[:50]}...' ({result['metadata']['processing_time']:.2f}s)")

            except Exception as e:
                logger.error(f"Error processing question {i}: {e}", exc_info=True)

                # Append the error to the output file
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(f"## {question}\n\nError: {str(e)}\n\n")

        logger.info(f"All questions processed. Results saved to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error in batch processing: {e}", exc_info=True)
        return 1


def handle_process_queries(args: argparse.Namespace) -> int:
    """
    Handle the process-queries command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get the queries folder path
        queries_folder = Path("queries")
        if not queries_folder.exists() or not queries_folder.is_dir():
            logger.error(f"Queries folder not found: {queries_folder}")
            return 1

        # Find query files
        query_files = list(queries_folder.glob("*.py"))
        if not query_files:
            logger.error(f"No Python query files found in {queries_folder}")
            return 1

        logger.info(f"Found {len(query_files)} query file(s) to process")

        # If a specific file is provided, filter to just that file
        if args.file:
            file_path = queries_folder / args.file
            if not file_path.exists():
                logger.error(f"Query file not found: {file_path}")
                return 1
            query_files = [file_path]

        # Dictionary to store query sets
        query_sets = {}

        # Load all query sets
        for query_file in query_files:
            try:
                # Import the module dynamically
                module_name = query_file.stem
                spec = importlib.util.spec_from_file_location(module_name, query_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Extract questionsSet from the module
                if hasattr(module, "questionsSet"):
                    query_sets[module_name] = module.questionsSet
                    logger.info(f"Found query set '{module.questionsSet.title}' in {query_file}")
                else:
                    logger.warning(f"No 'questionsSet' found in {query_file}")
            except Exception as e:
                logger.error(f"Error loading query file {query_file}: {e}", exc_info=True)

        if not query_sets:
            logger.error("No valid query sets found")
            return 1

        # If no specific file was provided, let the user select a query set
        selected_set = None
        if not args.file:
            print("\nAvailable query sets:")
            for i, (name, query_set) in enumerate(query_sets.items(), 1):
                print(f"{i}. {query_set.title} ({name})")
                print(f"   {query_set.description}")
                print()

            while True:
                try:
                    choice = input("Select a query set (number) or 'q' to quit: ")
                    if choice.lower() == 'q':
                        return 0

                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(query_sets):
                        selected_name = list(query_sets.keys())[choice_idx]
                        selected_set = query_sets[selected_name]
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(query_sets)}")
                except ValueError:
                    print("Please enter a valid number")
        else:
            # If a specific file was provided, use that query set
            selected_name = query_files[0].stem
            selected_set = query_sets[selected_name]

        # Initialize query processor
        processor = QueryProcessor(
            collection_name=args.collection,
            model_name=args.model
        )

        # Create a timestamp for the filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d")

        # Create output file with query set name and timestamp
        output_filename = f"{selected_name}_results_{timestamp}.md"
        output_path = Path(output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {selected_set.title}\n\n")
            f.write(f"{selected_set.description}\n\n")
            f.write(f"Analysis date: {timestamp}\n\n")

        logger.info(f"Created output file: {output_path}")

        total_queries = len(selected_set.questions)
        processed_queries = 0

        # Process each question in the selected query set
        for i, question in enumerate(selected_set.questions, 1):
            logger.info(f"Processing question {i}/{total_queries}: '{question}'")

            try:
                result = processor.answer_question(
                    question=question,
                    top_k=args.top_k
                )

                # Append the answer to the output file
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(f"## {question}\n\n{result['answer']}\n\n")

                logger.info(f"Answer for question {i} saved to {output_path}")
                processed_queries += 1

                # Print progress
                print(f"Processed {i}/{total_queries}: '{question[:50]}...' ({result['metadata']['processing_time']:.2f}s)")

            except Exception as e:
                logger.error(f"Error processing question {i}: {e}", exc_info=True)

                # Append the error to the output file
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(f"## {question}\n\nError: {str(e)}\n\n")

        logger.info(f"Query set processed. Processed {processed_queries}/{total_queries} questions. Results saved to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error in process-queries command: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    command_handlers = {
        "load": handle_load,
        "query": handle_query,
        "check": handle_check,
        "batch": handle_batch,
        "process-queries": handle_process_queries
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
