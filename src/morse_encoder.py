"""Convert completed blink durations into 1-unit dots and 3-unit dashes."""

from dataclasses import dataclass
from typing import Optional

from src.config import (
    DASH_MAX_DURATION_SECONDS,
    DASH_MIN_DURATION_SECONDS,
    DOT_MAX_DURATION_SECONDS,
    DOT_MIN_DURATION_SECONDS,
)


@dataclass(frozen=True)
class MorseResult:
    """The result of classifying one completed blink event."""

    duration: float
    signal: Optional[str]
    symbol: Optional[str]
    current_morse: str
    rejection_reason: Optional[str] = None

    @property
    def accepted(self) -> bool:
        return self.symbol is not None


class MorseEncoder:
    """Classify completed blinks using durations derived from one time unit."""

    def __init__(
        self,
        dot_min: float = DOT_MIN_DURATION_SECONDS,
        dot_max: float = DOT_MAX_DURATION_SECONDS,
        dash_min: float = DASH_MIN_DURATION_SECONDS,
        dash_max: float = DASH_MAX_DURATION_SECONDS,
    ) -> None:
        if not (0 <= dot_min <= dot_max < dash_min <= dash_max):
            raise ValueError("Morse timing ranges must be ordered and must not overlap.")

        self.dot_min = dot_min
        self.dot_max = dot_max
        self.dash_min = dash_min
        self.dash_max = dash_max
        self.current_morse = ""

    def encode_blink(self, duration: float) -> MorseResult:
        """Classify one blink duration as a dot, dash, or rejected noise."""
        if self.dot_min <= duration <= self.dot_max:
            signal, symbol = "DOT", "."
        elif self.dash_min <= duration <= self.dash_max:
            signal, symbol = "DASH", "-"
        else:
            if duration < self.dot_min:
                reason = "too short"
            elif duration > self.dash_max:
                reason = "too long"
            else:
                reason = "between dot and dash ranges"
            return MorseResult(duration, None, None, self.current_morse, reason)

        self.current_morse += symbol
        return MorseResult(duration, signal, symbol, self.current_morse)

    def clear(self) -> None:
        """Clear the current signal sequence without decoding it."""
        self.current_morse = ""
