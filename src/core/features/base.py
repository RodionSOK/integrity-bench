from abc import ABC, abstractmethod


class FormatChecker(ABC):
    extensions = set()

    @abstractmethod
    def check(self, data: bytes) -> dict:
        ...