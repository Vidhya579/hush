import unittest
from hush import textproc


class TestEllipsisAndSpacing(unittest.TestCase):
    def test_ellipsis_preserved(self):
        text = "Wait a minute... let me see."
        cleaned = textproc.clean(text)
        self.assertIn("...", cleaned)

    def test_unicode_ellipsis_normalized(self):
        text = "Thinking… okay I know."
        cleaned = textproc.clean(text)
        self.assertIn("...", cleaned)

    def test_doubled_punctuation_collapsed(self):
        text = "Hello,, world!! Are you there??"
        cleaned = textproc.clean(text)
        self.assertNotIn(",,", cleaned)
        self.assertNotIn("!!", cleaned)
        self.assertNotIn("??", cleaned)

    def test_comma_number_spacing(self):
        text = "Items 1,2,3 are ready."
        cleaned = textproc.clean(text)
        self.assertIn("1, 2, 3", cleaned)

    def test_decimal_not_broken(self):
        text = "The value of pi is 3.14 approximately."
        cleaned = textproc.clean(text)
        self.assertIn("3.14", cleaned)


if __name__ == "__main__":
    unittest.main()
