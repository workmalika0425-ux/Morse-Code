import unittest

from src.sentence_builder import SentenceBuilder


class SentenceBuilderTests(unittest.TestCase):
    def add_text(self, builder, text):
        for character in text:
            builder.add_character(character)

    def test_hello(self):
        builder = SentenceBuilder()
        builder.set_current_morse("....")
        self.add_text(builder, "HELLO")
        self.assertEqual(builder.current_sentence, "HELLO")
        self.assertEqual(builder.current_word, "HELLO")
        self.assertEqual(builder.last_character, "O")
        self.assertEqual(builder.current_morse, "")

    def test_hello_world(self):
        builder = SentenceBuilder()
        self.add_text(builder, "HELLO")
        builder.add_space()
        self.add_text(builder, "WORLD")
        self.assertEqual(builder.current_sentence, "HELLO WORLD")
        self.assertEqual(builder.current_word, "WORLD")

    def test_deletion(self):
        builder = SentenceBuilder()
        self.add_text(builder, "HELLO")
        builder.handle_command("DELETE")
        self.assertEqual(builder.current_sentence, "HELL")
        self.assertEqual(builder.current_word, "HELL")
        self.assertEqual(builder.last_character, "L")

    def test_spaces_do_not_duplicate(self):
        builder = SentenceBuilder()
        builder.handle_command("SPACE")
        builder.add_character("A")
        builder.handle_command("SPACE")
        builder.handle_command("SPACE")
        self.assertEqual(builder.current_sentence, "A ")
        self.assertEqual(builder.current_word, "")

    def test_reset(self):
        builder = SentenceBuilder(current_morse=".-", current_sentence="HELLO", current_word="HELLO", last_character="O")
        builder.handle_command("RESET")
        self.assertEqual(builder.current_morse, "")
        self.assertEqual(builder.current_sentence, "")
        self.assertEqual(builder.current_word, "")
        self.assertIsNone(builder.last_character)

    def test_invalid_input(self):
        builder = SentenceBuilder()
        with self.assertRaises(ValueError):
            builder.add_character("AB")
        with self.assertRaises(ValueError):
            builder.add_character(" ")
        with self.assertRaises(ValueError):
            builder.set_current_morse(".-x")
        with self.assertRaises(ValueError):
            builder.handle_command("UNDO")


if __name__ == "__main__":
    unittest.main()
