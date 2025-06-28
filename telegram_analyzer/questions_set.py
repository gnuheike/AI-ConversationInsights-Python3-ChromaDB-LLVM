from dataclasses import dataclass
from typing import List


@dataclass
class QuestionsSet:
    title: str
    description: str
    questions: List[str]
