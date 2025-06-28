"""
Message module for the Telegram Analyzer package.

This module provides the Message class for representing Telegram messages.
"""
import datetime
from dataclasses import dataclass


@dataclass
class Message:
    """
    Represents a Telegram message.
    
    Attributes:
        id: The message ID
        text: The message text
        date: The message date
    """
    id: str
    text: str
    date: datetime.datetime

    @classmethod
    def from_chromadb_data(cls, text: str, date: int, msg_id: str) -> 'Message':
        """
        Create a Message instance from ChromaDB data.
        
        Args:
            text: The document text from ChromaDB
            meta: The metadata from ChromaDB
            msg_id: The message ID
            
        Returns:
            A new Message instance
            :param msg_id:
            :param text:
            :param date:
        """
        date_time = datetime.datetime.fromtimestamp(date)
        return cls(id=msg_id, text=text, date=date_time)

    @classmethod
    def many_from_chromadb_data(cls, get_result: dict = None, query_result: list = None) -> list:
        """
        Create a list of Message instances from ChromaDB data.
        Args:
            get_result: Direct ChromaDB result dict from collection.get()
            query_result: List of result dictionaries from query method
        Returns:
            List of Message instances
        Raises:
            ValueError: If both parameters are None or if required data is missing
        """
        if get_result is None and query_result is None:
            raise ValueError("Either get_result or list_result must be provided")

        if get_result is not None and query_result is not None:
            raise ValueError("Only one of get_result or list_result should be provided")

        # Handle get_result (from collection.get())
        if get_result is not None:
            if not get_result.get('ids') or not get_result['ids']:
                raise ValueError("get_result missing 'ids' or ids is empty")
            if not get_result['ids'][0]:
                raise ValueError("get_result ids[0] is empty")
            if not get_result.get('documents') or not get_result['documents']:
                raise ValueError("get_result missing 'documents' or documents is empty")
            if not get_result['documents'][0]:
                raise ValueError("get_result documents[0] is empty")
            if not get_result.get('metadatas') or not get_result['metadatas']:
                raise ValueError("get_result missing 'metadatas' or metadatas is empty")
            if not get_result['metadatas'][0]:
                raise ValueError("get_result metadatas[0] is empty")

            docs = get_result['documents'][0]
            metas = get_result['metadatas'][0]
            msg_ids = [msg_id for msg_id in get_result['ids'][0]]

        # Handle list_result (from query method)
        else:  # list_result is not None
            if not query_result:
                raise ValueError("list_result is empty")

            # Validate that each result has required fields
            for i, result in enumerate(query_result):
                if not isinstance(result, dict):
                    raise ValueError(f"list_result[{i}] is not a dictionary")
                if 'text' not in result:
                    raise ValueError(f"list_result[{i}] missing 'text' field")
                if 'metadata' not in result:
                    raise ValueError(f"list_result[{i}] missing 'metadata' field")
                if 'id' not in result:
                    raise ValueError(f"list_result[{i}] missing 'id' field")

            docs = [result['text'] for result in query_result]
            metas = [result['metadata'] for result in query_result]
            msg_ids = [result['id'] for result in query_result]

        return [cls.from_chromadb_data(doc, meta['date'], msg_id) for doc, meta, msg_id in zip(docs, metas, msg_ids)]

    def __str__(self):
        return f"Message(id={self.id}, text={self.text}, date={self.date})"
