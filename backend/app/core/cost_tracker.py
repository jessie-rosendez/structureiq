from dataclasses import dataclass, field
from threading import Lock

# Gemini 2.0 Flash pricing
_INPUT_COST_PER_M = 1.25
_OUTPUT_COST_PER_M = 5.00


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        return calculate_cost(self.input_tokens, self.output_tokens)


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * _INPUT_COST_PER_M
    output_cost = (output_tokens / 1_000_000) * _OUTPUT_COST_PER_M
    return round(input_cost + output_cost, 6)


class SessionCostTracker:
    """Thread-safe session-level cost accumulator."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._total_input = 0
        self._total_output = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        with self._lock:
            self._total_input += input_tokens
            self._total_output += output_tokens

    @property
    def total_cost_usd(self) -> float:
        with self._lock:
            return calculate_cost(self._total_input, self._total_output)

    @property
    def total_tokens(self) -> dict[str, int]:
        with self._lock:
            return {"input": self._total_input, "output": self._total_output}

    def reset(self) -> None:
        with self._lock:
            self._total_input = 0
            self._total_output = 0


# Module-level session tracker; reset per document session
_session_tracker = SessionCostTracker()


def record_usage(input_tokens: int, output_tokens: int) -> float:
    """Record token usage and return cost for this call."""
    _session_tracker.record(input_tokens, output_tokens)
    return calculate_cost(input_tokens, output_tokens)


def session_total_cost() -> float:
    return _session_tracker.total_cost_usd


def session_total_tokens() -> dict[str, int]:
    return _session_tracker.total_tokens


def reset_session() -> None:
    _session_tracker.reset()
