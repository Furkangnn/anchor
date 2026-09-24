import unittest

from anchor.chain import build_chain


class ChainTest(unittest.TestCase):
    def test_refund_is_cited(self):
        answer = build_chain().invoke("When is a missed pickup refunded?")
        self.assertIn("5 days", answer)
        self.assertIn("[Refunds]", answer)

    def test_unknown_is_refused(self):
        answer = build_chain().invoke("What is the CEO's favorite lunch?")
        self.assertEqual(answer, "Not in the documents.")


if __name__ == "__main__":
    unittest.main()
