import unittest

from src.morse_decoder import MorseDecoder


class MorseDecoderTests(unittest.TestCase):
    def setUp(self):
        self.decoder = MorseDecoder(character_pause=0.3, word_pause=0.7)
        self.time = 0.0

    def submit_character(self, morse):
        for symbol in morse:
            self.decoder.add_symbol(symbol, self.time)
            self.time += 0.01
        result = self.decoder.update(self.time + 0.3)
        self.time += 0.35
        return result

    def test_a_b_and_c(self):
        self.assertEqual(self.submit_character(".-").decoded_character, "A")
        self.assertEqual(self.submit_character("-...").decoded_character, "B")
        self.assertEqual(self.submit_character("-.-.").decoded_character, "C")

    def test_all_alphabet_letters(self):
        alphabet_morse = (
            ".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....",
            "..", ".---", "-.-", ".-..", "--", "-.", "---", ".--.",
            "--.-", ".-.", "...", "-", "..-", "...-", ".--", "-..-",
            "-.--", "--..",
        )
        for morse in alphabet_morse:
            self.submit_character(morse)
        self.assertEqual(self.decoder.sentence, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def test_hello(self):
        for morse in ("....", ".", ".-..", ".-..", "---"):
            self.submit_character(morse)
        self.assertEqual(self.decoder.sentence, "HELLO")

    def test_sos(self):
        for morse in ("...", "---", "..."):
            self.submit_character(morse)
        self.assertEqual(self.decoder.sentence, "SOS")

    def test_numbers(self):
        for morse in ("-----", ".----", "..---", "...--", "....-"):
            self.submit_character(morse)
        self.assertEqual(self.decoder.sentence, "01234")

    def test_invalid_morse_is_safe(self):
        result = self.submit_character("....-.-")
        self.assertEqual(result.unknown_morse, "....-.-")
        self.assertEqual(self.decoder.sentence, "?")

    def test_word_pause_adds_one_space(self):
        self.submit_character("....")
        result = self.decoder.update(self.time + 0.7)
        self.assertTrue(result.word_completed)
        self.assertEqual(self.decoder.sentence, "H ")
        self.assertFalse(self.decoder.update(self.time + 1.0).word_completed)

    def test_blink_in_progress_preserves_a_symbol_gap(self):
        self.decoder.add_symbol(".", 0.0)
        self.decoder.begin_blink(0.2)  # Standard one-unit symbol gap.
        self.assertFalse(self.decoder.update(0.6).decoded_character)
        self.decoder.add_symbol("-", 0.8)
        result = self.decoder.update(1.1)
        self.assertEqual(result.decoded_character, "A")


if __name__ == "__main__":
    unittest.main()
