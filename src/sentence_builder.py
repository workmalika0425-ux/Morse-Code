"""Camera-independent state management for decoded Morse text."""

from dataclasses import dataclass


VALID_PUNCTUATION = frozenset(".,?!/():")


@dataclass
class SentenceBuilder:
    """Build text one decoded character at a time with safe edit operations."""

    current_morse: str = ""
    last_character: str | None = None
    current_word: str = ""
    current_sentence: str = ""

    def set_current_morse(self, morse: str) -> None:
        """Store the in-progress dot/dash sequence displayed by the UI."""
        if any(symbol not in ".-" for symbol in morse):
            raise ValueError("Current Morse may contain only '.' and '-'.")
        self.current_morse = morse

    def add_character(self, character: str) -> None:
        """Append one decoded letter, number, or supported punctuation mark."""
        if not isinstance(character, str) or len(character) != 1:
            raise ValueError("A character must be exactly one character long.")
        if not (character.isalnum() or character in VALID_PUNCTUATION):
            raise ValueError(f"Unsupported character: {character!r}")

        character = character.upper()
        self.current_sentence += character
        self.current_word += character
        self.last_character = character
        self.clear_current_morse()

    def add_space(self) -> None:
        """End the current word, without adding duplicate leading/trailing spaces."""
        if not self.current_sentence or self.current_sentence.endswith(" "):
            return
        self.current_sentence += " "
        self.current_word = ""

    def delete_last_character(self) -> None:
        """Remove the last written character or trailing word boundary safely."""
        if not self.current_sentence:
            return
        self.current_sentence = self.current_sentence[:-1]
        self._refresh_text_state()

    def clear_current_morse(self) -> None:
        """Discard only the undecoded dot/dash sequence."""
        self.current_morse = ""

    def clear_current_word(self) -> None:
        """Discard the word currently being assembled, retaining earlier text."""
        if not self.current_word:
            return
        self.current_sentence = self.current_sentence[: -len(self.current_word)]
        self._refresh_text_state()

    def clear_entire_sentence(self) -> None:
        """Reset all sentence-building state."""
        self.current_morse = ""
        self.last_character = None
        self.current_word = ""
        self.current_sentence = ""

    def handle_command(self, command: str) -> None:
        """Execute a UI-ready editing command: SPACE, DELETE, CLEAR, or RESET."""
        normalized = command.upper()
        commands = {
            "SPACE": self.add_space,
            "DELETE": self.delete_last_character,
            "CLEAR": self.clear_current_word,
            "RESET": self.clear_entire_sentence,
        }
        try:
            commands[normalized]()
        except KeyError as error:
            raise ValueError(f"Unsupported command: {command!r}") from error

    def _refresh_text_state(self) -> None:
        """Recalculate derived fields after an edit operation."""
        stripped = self.current_sentence.rstrip()
        self.last_character = stripped[-1] if stripped else None
        self.current_word = "" if self.current_sentence.endswith(" ") else stripped.rsplit(" ", 1)[-1]
