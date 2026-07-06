from src.core.features.base import FormatChecker

_registry = {}

def register(checker: FormatChecker) -> None:
    for ext in checker.extensions:
        _registry[ext] = checker
        
def get_checker(extension: str) -> FormatChecker | None:
    return _registry.get(extension.lower())