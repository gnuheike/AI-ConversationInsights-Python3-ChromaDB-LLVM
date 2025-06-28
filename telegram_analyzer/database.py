"""
Database module for the Telegram Analyzer package.

This module provides functionality for interacting with ChromaDB,
including loading data, querying, and managing collections.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from telegram_analyzer import config
from telegram_analyzer.logging import logger
from telegram_analyzer.message import Message


class ChromaDBManager:
    """
    Class for managing ChromaDB operations.
    """

    def __init__(
            self,
            persist_directory: Optional[str] = None,
            collection_name: str = config.COLLECTION_NAME,
            model_name: str = config.SENTENCE_MODEL["name"],
            device: str = config.SENTENCE_MODEL["device"]
    ):
        """
        Initialize the ChromaDBManager.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
            model_name: Name of the sentence transformer model
            device: Device to use for the model (cpu, cuda, mps)
        """
        self.persist_directory = persist_directory or config.CHROMADB_SETTINGS["persist_directory"]
        self.collection_name = collection_name
        self.model_name = model_name
        self.device = device

        # Ensure the persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info(f"Using persist directory: {self.persist_directory}")

        # Initialize client
        self.client = chromadb.Client(Settings(
            is_persistent=True,
            persist_directory=self.persist_directory
        ))
        logger.info("ChromaDB client initialized")

        # Initialize model
        self.model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"Sentence transformer model initialized: {self.model_name} on {self.device}")

    def get_or_create_collection(self, reset: bool = False) -> chromadb.Collection:
        """
        Get or create a ChromaDB collection.

        Args:
            reset: If True, delete the collection if it exists before creating a new one

        Returns:
            The ChromaDB collection
        """
        if reset:
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception as e:
                logger.warning(f"Could not delete collection {self.collection_name}: {e}")

        collection = self.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"Using collection: {self.collection_name}")
        return collection

    def load_messages(
            self,
            messages: List[Dict[str, Any]],
            batch_size: int = 5000,
            reset_collection: bool = True
    ) -> int:
        """
        Load messages into ChromaDB.

        Args:
            messages: List of message dictionaries to load
            batch_size: Number of messages to process in each batch
            reset_collection: If True, reset the collection before loading

        Returns:
            The number of messages loaded
        """
        collection = self.get_or_create_collection(reset=reset_collection)
        total_messages = len(messages)
        logger.info(f"Loading {total_messages} messages into ChromaDB")

        try:
            for i in range(0, total_messages, batch_size):
                batch_messages = messages[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_messages + batch_size - 1) // batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_messages)} messages)")

                # Prepare batch data
                texts = [msg['text'] for msg in batch_messages]
                ids = [str(msg['id']) for msg in batch_messages]  # Convert numeric IDs to strings for the batch
                metadatas = [
                    {
                        "date": int(msg["date"])
                    }
                    for msg in batch_messages
                ]

                # Generate embeddings
                logger.info(f"Generating embeddings for batch {batch_num}")
                embeddings = self.model.encode(texts, show_progress_bar=True)

                # Add to collection
                collection.add(
                    documents=texts,
                    embeddings=embeddings.tolist(),
                    metadatas=metadatas,
                    ids=ids
                )

                # Verify batch
                count = collection.count()
                logger.info(f"Batch {batch_num} loaded. Current collection count: {count}")

            # Final verification
            final_count = collection.count()
            logger.info(f"Successfully loaded {final_count} messages into collection {self.collection_name}")

            return final_count

        except Exception as e:
            logger.error(f"Error loading messages into ChromaDB: {e}", exc_info=True)
            raise

    def query(
            self,
            query_text: str,
            top_k: int = config.QUERY_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Query the ChromaDB collection for relevant messages.

        Args:
            query_text: The query text
            top_k: Number of results to return

        Returns:
            A list of relevant messages with their metadata
        """
        logger.info(f"Querying collection {self.collection_name} with: '{query_text}', top_k={top_k}")

        try:
            collection = self.client.get_collection(name=self.collection_name)

            # Generate query embedding
            query_embedding = self.model.encode([query_text])[0]

            logger.info(f"Query embedding generated: {query_embedding}")

            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )

            # Format results
            formatted_results = [
                {'text': doc, 'metadata': meta, 'id': id_val}
                for doc, meta, id_val in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['ids'][0]
                )
            ]

            logger.info(f"Query returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}", exc_info=True)
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the ChromaDB collection.

        Returns:
            A dictionary with collection information
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
            count = collection.count()

            # Get directory size
            dir_size = 0
            dir_path = Path(self.persist_directory)
            for path in dir_path.glob('**/*'):
                if path.is_file():
                    dir_size += path.stat().st_size

            info = {
                'collection_name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory,
                'directory_size_bytes': dir_size,
                'directory_size_gb': dir_size / (1024 ** 3),
                'model_name': self.model_name,
                'device': self.device
            }

            logger.info(f"Collection info: {info}")
            return info

        except Exception as e:
            logger.error(f"Error getting collection info: {e}", exc_info=True)
            raise

    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a message by its ID.

        Args:
            message_id: The ID of the message to retrieve

        Returns:
            The message with its metadata, or None if not found
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)

            # Query the collection for the specific ID
            result = collection.get(ids=[message_id])

            if not result['ids']:
                logger.warning(f"Message with ID {message_id} not found")
                return None

            # Format the result
            message = {
                'text': result['documents'][0],
                'metadata': result['metadatas'][0],
                'id': result['ids'][0]
            }

            return message

        except Exception as e:
            logger.error(f"Error getting message by ID: {e}", exc_info=True)
            raise

    def get_messages_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific date.

        Args:
            date: The date to retrieve messages for (in the format stored in metadata)

        Returns:
            A list of messages with their metadata
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)

            # Query the collection for messages with the specific date
            results = collection.query(
                query_texts=[""],  # Empty query to match all documents
                where={"date": date},  # Filter by date
                n_results=collection.count()  # Get all matching messages
            )

            # Format results
            formatted_results = [
                {'text': doc, 'metadata': meta, 'id': id}
                for doc, meta, id in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['ids'][0]
                )
            ]

            logger.info(f"Found {len(formatted_results)} messages for date {date}")
            return formatted_results

        except Exception as e:
            logger.error(f"Error getting messages by date: {e}", exc_info=True)
            raise

    def _convert_chromadb_get_result_to_messages(self, chromadb_result) -> List[Message]:
        """
        Convert ChromaDB get() result to a list of Message objects.

        Args:
            chromadb_result: Result from collection.get()

        Returns:
            List of Message instances
        """
        try:
            # Check if we have any results
            if not chromadb_result.get('ids') or not chromadb_result['ids']:
                return []

            # ChromaDB get() returns flat lists, not nested lists like query()
            ids = chromadb_result['ids']
            documents = chromadb_result.get('documents', [])
            metadatas = chromadb_result.get('metadatas', [])

            # Ensure we have matching lengths
            if len(ids) != len(documents) or len(ids) != len(metadatas):
                logger.warning(f"Mismatched lengths in ChromaDB result: ids={len(ids)}, docs={len(documents)}, metas={len(metadatas)}")
                return []

            # Convert to Message objects
            messages = []
            for msg_id, doc, meta in zip(ids, documents, metadatas):
                if doc and meta and 'date' in meta:
                    message = Message.from_chromadb_data(doc, meta['date'], msg_id)
                    messages.append(message)

            return messages

        except Exception as e:
            logger.error(f"Error converting ChromaDB result to messages: {e}")
            return []

    def expand_message_results(
            self,
            message: Message,
            n: int = 5
    ) -> List[Message]:
        """
        Get N messages before and N messages after a specific message ID.

        Args:
            message: The reference message
            n: Number of messages to retrieve before and after the reference message

        Returns:
            A list of messages around the reference message, sorted chronologically
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)

            target_timestamp = int(message.date.timestamp())

            # Query for N messages before the target (timestamp < target_timestamp)
            if n > 0:
                query_messages_before = collection.get(
                    where={"date": {"$lt": target_timestamp}},
                    include=['documents', 'metadatas'],
                    limit=n
                )
                # Convert ChromaDB result to the expected format
                messages_before = self._convert_chromadb_get_result_to_messages(query_messages_before)
            else:
                messages_before = []

            # Query for N messages after the target (timestamp > target_timestamp)
            if n > 0:
                query_messages_after = collection.get(
                    where={"date": {"$gt": target_timestamp}},
                    include=['documents', 'metadatas'],
                    limit=n
                )
                # Convert ChromaDB result to the expected format
                messages_after = self._convert_chromadb_get_result_to_messages(query_messages_after)
            else:
                messages_after = []

            # Combine all messages
            all_messages = [message]
            all_messages.extend(messages_before)
            all_messages.extend(messages_after)

            # Sort by timestamp to ensure chronological order
            all_messages.sort(key=lambda msg: msg.date.timestamp())
            return all_messages

        except Exception as e:
            logger.error(f"Error getting messages around message ID {message.id}: {e}", exc_info=True)
            raise


def load_into_chromadb(
        messages: List[Dict[str, Any]],
        collection_name: str = config.COLLECTION_NAME,
        batch_size: int = 5000,
        reset_collection: bool = True
) -> int:
    """
    Load messages into ChromaDB.

    This is a convenience function that creates a ChromaDBManager
    and calls its load_messages method.

    Args:
        messages: List of message dictionaries to load
        collection_name: Name of the ChromaDB collection
        batch_size: Number of messages to process in each batch
        reset_collection: If True, reset the collection before loading

    Returns:
        The number of messages loaded
    """
    db_manager = ChromaDBManager(collection_name=collection_name)
    return db_manager.load_messages(
        messages=messages,
        batch_size=batch_size,
        reset_collection=reset_collection
    )


def query_messages(
        query_text: str,
        collection_name: str = config.COLLECTION_NAME,
        top_k: int = config.QUERY_TOP_K,
        context_n: int = config.QUERY_CONTEXT_N
) -> List[Message]:
    """
    Query ChromaDB for relevant messages and include context messages around each result.

    This function creates a ChromaDBManager, calls its query method to find relevant messages,
    and then for each result, retrieves N messages before and N messages after to provide better context.

    Args:
        query_text: The query text
        collection_name: Name of the ChromaDB collection
        top_k: Number of results to return
        context_n: Number of messages to include before and after each found message for context

    Returns:
        A list of relevant messages with their metadata and context messages
    """
    logger.info(f"Querying messages with: '{query_text}', top_k={top_k}, context_n={context_n}")

    db_manager = ChromaDBManager(collection_name=collection_name)

    # Get initial query results
    initial_results = db_manager.query(query_text=query_text, top_k=top_k)
    logger.info(f"Initial query returned {len(initial_results)} results")

    if not initial_results:
        logger.info("No results found for the query")
        return []

    messages = Message.many_from_chromadb_data(query_result=initial_results)
    del initial_results

    # For each result, get context messages
    results_with_context: List[Message] = []
    for i, message in enumerate(messages):
        logger.debug(f"Processing result {i + 1}/{len(messages)}")
        logger.debug(f"Getting context messages for result {i + 1} with ID {message.id}")

        # Get messages around the date
        context_messages = db_manager.expand_message_results(
            message=message,
            n=context_n
        )

        logger.debug(f"Found {len(context_messages)} context messages around date {message.id}")

        # Add the context messages to the results
        results_with_context.extend(context_messages)

    # Remove duplicates (a message might be in multiple context windows)
    unique_results = []
    seen_ids = set()

    for msg in results_with_context:
        msg_id = msg.id
        if msg_id and msg_id not in seen_ids:
            seen_ids.add(msg_id)
            unique_results.append(msg)
        elif not msg_id:
            # If there's no ID, we can't deduplicate, so just add it
            unique_results.append(msg)

    logger.info(f"Final query with context returned {len(unique_results)} unique messages")
    return unique_results
