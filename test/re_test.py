import re
import unittest

# Regex that supports opinion types with underscores
REGEX = re.compile(r"^(.+)_([a-zA-Z0-9-]+)_labeler$")


def parse_opinion_key(key: str):
    """Extract (type, uuid) from opinion key, or return None."""
    match = REGEX.match(key)
    if match:
        return match.group(1), match.group(2)
    return None


class TestOpinionKeyRegex(unittest.TestCase):
    def test_valid_cases(self):
        self.assertEqual(
            parse_opinion_key("basel_img_userabc_labeler"),
            ("basel_img", "userabc")
        )
        self.assertEqual(
            parse_opinion_key("corona_score_1234_labeler"),
            ("corona_score", "1234")
        )
        self.assertEqual(
            parse_opinion_key("aspects_score_550e8400-e29b_labeler"),
            ("aspects_score", "550e8400-e29b")
        )
        self.assertEqual(
            parse_opinion_key("a_b_c_d_1234-labeler_labeler"),
            ("a_b_c_d", "1234-labeler")
        )

    def test_invalid_cases(self):
        self.assertIsNone(parse_opinion_key("invalid_labeler"))
        self.assertIsNone(parse_opinion_key("opinion_1234_labeler_extra"))
        self.assertIsNone(parse_opinion_key("no_uuid_suffix"))
        self.assertIsNone(parse_opinion_key("just_labeler"))

    def test_edge_cases(self):
        self.assertEqual(
            parse_opinion_key("score_1234_labeler"),
            ("score", "1234")
        )
        self.assertEqual(
            parse_opinion_key("long_type_with_underscores_and_dashes_abc123-labeler_labeler"),
            ("long_type_with_underscores_and_dashes", "abc123-labeler")
        )


if __name__ == "__main__":
    unittest.main()
