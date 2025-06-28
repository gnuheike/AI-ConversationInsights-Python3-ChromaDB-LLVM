"""
Data processing module for the Telegram Analyzer package.

This module provides functionality for loading and processing Telegram chat data
from JSON export files.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from telegram_analyzer.logging import logger


class TelegramDataProcessor:
    """
    Class for processing Telegram chat data from JSON export files.
    """

    def __init__(self, json_file: Union[str, Path]):
        """
        Initialize the TelegramDataProcessor.

        Args:
            json_file: Path to the Telegram chat JSON export file
        """
        self.json_file = Path(json_file)
        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_file}")
        logger.info(f"Initialized TelegramDataProcessor with file: {self.json_file}")

    def load_messages(self) -> List[Dict[str, Any]]:
        """
        Load and process messages from the Telegram chat JSON export file.

        Returns:
            A list of processed message dictionaries with standardized fields
        """
        logger.info(f"Loading messages from {self.json_file}")
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            messages = []
            for msg in data.get('messages', []):
                processed_msg = self._process_message(msg)
                
                if processed_msg and processed_msg['text']:
                    messages.append(processed_msg)

            logger.info(f"Successfully loaded {len(messages)} messages")
            return messages
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
            raise

    def _process_message(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single message from the Telegram chat data.

        Args:
            msg: The raw message dictionary from the JSON data

        Returns:
            A processed message dictionary or None if the message should be skipped
        """
        # Skip non-message types or messages without text
        if msg.get('type') != 'message' or not isinstance(msg.get('text'), str):
            return None

        # Extract and standardize message fields
        processed_msg = {
            'id': str(msg.get('id', '')),
            'text': msg.get('text', ''),
            'date': msg.get('date_unixtime', '')
        }

        # Skip empty messages
        if not processed_msg['text'].strip():
            return None

        return processed_msg


def load_telegram_messages(json_file: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load and process messages from a Telegram chat JSON export file.

    This is a convenience function that creates a TelegramDataProcessor
    and calls its load_messages method.

    Args:
        json_file: Path to the Telegram chat JSON export file

    Returns:
        A list of processed message dictionaries with standardized fields
    """
    processor = TelegramDataProcessor(json_file)
    return processor.load_messages()
