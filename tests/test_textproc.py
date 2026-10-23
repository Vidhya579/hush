import unittest
from hush import textproc


class TestTextprocDictionary(unittest.TestCase):
    def test_multi_word_dictionary_phrase(self):
        text = "I love using hush engine for my voice dictation."
        entries = ["Hush Engine", "FastAPI"]
        cleaned = textproc.clean(text, dictionary=entries)
        self.assertIn("Hush Engine", cleaned)

    def test_devanagari_dictionary_term(self):
        text = "नमस्ते दुनिया और सूर्यवंश"
        entries = ["सूर्यवंश", "नमस्ते"]
        cleaned = textproc.clean(text, dictionary=entries)
        self.assertIn("सूर्यवंश", cleaned)
        self.assertIn("नमस्ते", cleaned)

    def test_single_word_fuzzy_match(self):
        text = "Hello Siryanch how are you"
        entries = ["Suryansh"]
        cleaned = textproc.clean(text, dictionary=entries)
        self.assertIn("Suryansh", cleaned)


if __name__ == "__main__":
    unittest.main()
