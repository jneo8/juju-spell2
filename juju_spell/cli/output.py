"""Output callbacks."""
import pprint

from loguru import logger

from juju_spell.assignment import RunResult


class OutputHandler:
    """Default output handler."""

    results: list[RunResult] = []

    def call(self, result: RunResult) -> None:
        """Callback function for assignment receiver."""
        self.results.append(result)

    def print(self) -> None:
        """Final output."""
        for result in self.results:
            logger.info(pprint.pformat(result))
