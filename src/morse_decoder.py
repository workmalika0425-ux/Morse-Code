"""Decode timed Morse symbol sequences into characters without crashing."""

from dataclasses import dataclass
import time
from typing import Optional

from src.config import CHARACTER_PAUSE_SECONDS, WORD_PAUSE_SECONDS


INTERNATIONAL_MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--",
    "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--",
    "/": "-..-.", "(": "-.--.", ")": "-.--.-", ":": "---...",
}
MORSE_TO_CHARACTER = {morse: character for character, morse in INTERNATIONAL_MORSE.items()}


@dataclass(frozen=True)
class DecodeResult:
    """A decoder update; fields are populated only when a boundary is crossed."""

    decoded_character: Optional[str] = None
    unknown_morse: Optional[str] = None
    word_completed: bool = False


class MorseDecoder:
    """Collect one Morse character and decode it after its pause boundary."""

    def __init__(
        self,
        character_pause: float = CHARACTER_PAUSE_SECONDS,
        word_pause: float = WORD_PAUSE_SECONDS,
    ) -> None:
        if character_pause <= 0 or word_pause <= character_pause:
            raise ValueError("Word pause must be greater than the character pause.")

        self.character_pause = character_pause
        self.word_pause = word_pause
        self.current_morse = ""
        self.sentence = ""
        self._last_symbol_at: Optional[float] = None
        self._character_completed = False
        self._word_completed = False
        self._blink_in_progress = False

    def begin_blink(self, timestamp: Optional[float] = None) -> DecodeResult:
        """Pause character timing as soon as the next intentional blink starts."""
        now = time.perf_counter() if timestamp is None else timestamp
        result = self.update(now)
        self._blink_in_progress = True
        return result

    def finish_blink(self) -> None:
        """Resume character timing after a blink that was rejected as noise."""
        self._blink_in_progress = False

    def add_symbol(self, symbol: str, timestamp: Optional[float] = None) -> None:
        """Append one classified dot or dash to the character being collected."""
        if symbol not in (".", "-"):
            raise ValueError("A Morse symbol must be '.' or '-'.")

        self.current_morse += symbol
        self._last_symbol_at = time.perf_counter() if timestamp is None else timestamp
        self._character_completed = False
        self._word_completed = False
        self._blink_in_progress = False

    def update(self, timestamp: Optional[float] = None) -> DecodeResult:
        """Finalize a character or word once the relevant pause has elapsed."""
        if self._last_symbol_at is None or self._blink_in_progress:
            return DecodeResult()

        now = time.perf_counter() if timestamp is None else timestamp
        elapsed = now - self._last_symbol_at
        result = DecodeResult()

        if self.current_morse and elapsed >= self.character_pause:
            morse = self.current_morse
            decoded = MORSE_TO_CHARACTER.get(morse)
            if decoded is None:
                self.sentence += "?"
                result = DecodeResult(unknown_morse=morse)
            else:
                self.sentence += decoded
                result = DecodeResult(decoded_character=decoded)
            self.current_morse = ""
            self._character_completed = True

        if (
            self._character_completed
            and not self._word_completed
            and elapsed >= self.word_pause
            and self.sentence
            and not self.sentence.endswith(" ")
        ):
            self.sentence += " "
            self._word_completed = True
            return DecodeResult(
                decoded_character=result.decoded_character,
                unknown_morse=result.unknown_morse,
                word_completed=True,
            )

        return result

    def clear(self) -> None:
        """Clear an in-progress sequence and decoded output."""
        self.current_morse = ""
        self.sentence = ""
        self._last_symbol_at = None
        self._character_completed = False
        self._word_completed = False
        self._blink_in_progress = False

    def clear_current_morse(self) -> None:
        """Discard only the in-progress character without changing the sentence."""
        self.current_morse = ""
        self._last_symbol_at = None
        self._character_completed = False
        self._word_completed = False
        self._blink_in_progress = False
