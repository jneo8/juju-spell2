"""Utils."""
import typing as t
from collections.abc import Generator
from types import SimpleNamespace

__all__ = ["Namespace", "flatten"]


class Namespace(SimpleNamespace):
    """Namespace for options."""


def flatten(items: list[t.Any]) -> Generator:
    """Flatten arbitrarily nested iterable items."""
    for i in items:
        if hasattr(i, "__iter__"):
            for j in flatten(i):
                yield j
        else:
            yield i
