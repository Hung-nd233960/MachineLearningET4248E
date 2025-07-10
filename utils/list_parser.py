import re
from enum import Enum, auto
from typing import Optional

class AnnotateError(Enum):
    """Enumeration for annotation errors."""
    INVALID_SYNTAX = auto()
    NOT_UNIQUE = auto()
    NOT_ORDERED = auto()
    OUT_OF_BOUNDS = auto()
    INVALID_RANGE = auto()

def is_valid_syntax(input_str: str) -> bool:
    """
    Checks if the input string is syntactically valid.
    Allowed tokens: numbers (e.g., 3), or ranges (e.g., 3-10)
    """
    pattern = r"^\s*(\d+\s*(-\s*\d+)?\s*)(,\s*(\d+\s*(-\s*\d+)?\s*))*$"
    return bool(re.match(pattern, input_str.strip()))

def is_unique_and_ordered(input_str: str) -> bool:
    """ Checks if the input string contains unique numbers in strictly increasing order.
    """
    nums = expand_page_list(input_str)
    seen = set()
    prev = None

    for num in nums:
        if num in seen:
            return False
        if prev is not None and num <= prev:
            return False
        seen.add(num)
        prev = num

    return True

def is_valid_page_range(input_str: str, max_page: int) -> bool:
    """
    Checks if the input string represents a valid page range.
    - All numbers must be within 1 to max_page (inclusive).
    """
    nums = expand_page_list(input_str)

    if not nums:
        return False

    if any(num < 1 or num > max_page for num in nums):
        return False
    
def expand_page_list(input_str: str) -> list[int]:
    """
    Expands the input string into a list of numbers.
    Example: "1,3,5-7" => [1, 3, 5, 6, 7]
    """
    elements = input_str.split(",")
    result = []

    for element in elements:
        element = element.strip()
        if not element:
            continue  # skip empty entries like ""
        
        if "-" in element:
            start_str, end_str = map(str.strip, element.split("-"))
            if not start_str or not end_str:
                raise ValueError(f"Invalid range syntax: '{element}'")
            start, end = int(start_str), int(end_str)
            if start > end:
                raise ValueError(f"Invalid range: {start}-{end}")
            result.extend(range(start, end + 1))
        else:
            result.append(int(element))
    return result


def compress_page_list(numbers: list[int]) -> str:
    """ Compresses a list of numbers into a string representation."""
    if not numbers:
        return ""

    numbers = sorted(set(numbers))
    result = []

    start = numbers[0]
    end = numbers[0]

    for i in range(1, len(numbers)):
        if numbers[i] == end + 1:
            end = numbers[i]
        else:
            # Handle the current cluster before moving on
            result.extend(_format_range(start, end))
            start = end = numbers[i]

    result.extend(_format_range(start, end))  # final group
    return ",".join(result)


def _format_range(start: int, end: int) -> list[str]:
    """
    Helper: return list of one or more strings depending on length of range.
    - 1 number: [5]
    - 2 numbers: [5, 6]
    - 3+ numbers: ["5-7"]
    """
    if start == end:
        return [str(start)]
    if end == start + 1:
        return [str(start), str(end)]
    return [f"{start}-{end}"]

def get_annotation_error(input_str: str, max_page: int) -> Optional[AnnotateError]:
    """
    Validates the input and returns the first encountered error type.
    Returns None if there are no errors.
    """
    if not is_valid_syntax(input_str):
        return AnnotateError.INVALID_SYNTAX
    
    try:
        nums = expand_page_list(input_str)
    except ValueError:
        return AnnotateError.INVALID_RANGE

    # Range is now valid, check uniqueness and order
    seen = set()
    prev = None
    for num in nums:
        if num in seen:
            return AnnotateError.NOT_UNIQUE
        if prev is not None and num <= prev:
            return AnnotateError.NOT_ORDERED
        seen.add(num)
        prev = num

    if any(num < 1 or num > max_page for num in nums):
        return AnnotateError.OUT_OF_BOUNDS

    return None  # Everything is fine

if __name__ == "__main__":
    import unittest
    class TestListParser(unittest.TestCase):
        def test_is_valid_syntax(self):
            self.assertTrue(is_valid_syntax("1, 5, 10"))
            self.assertTrue(is_valid_syntax("2-4, 7-9"))
            self.assertFalse(is_valid_syntax("1 2"))
            self.assertFalse(is_valid_syntax("a,b,c"))

        def test_is_unique_and_ordered(self):
            self.assertTrue(is_unique_and_ordered("1, 2, 5-7"))
            self.assertFalse(is_unique_and_ordered("2, 1, 3"))
            self.assertFalse(is_unique_and_ordered("1, 2, 2"))

        def test_expand_page_list(self):
            self.assertEqual(expand_page_list("1-3"), [1, 2, 3])
            self.assertEqual(expand_page_list("1, 3, 5-7"), [1, 3, 5, 6, 7])
            self.assertEqual(expand_page_list("24, 26, 56"), [24, 26, 56])
            self.assertEqual(expand_page_list(""), [])
            with self.assertRaises(ValueError):
                expand_page_list("5-3")

        def test_compress_page_list(self):
            self.assertEqual(compress_page_list([1, 2, 3]), "1-3")
            self.assertEqual(compress_page_list([1, 3, 5, 6, 7]), "1,3,5-7")
            self.assertEqual(compress_page_list([1, 3, 5, 6, 8]), "1,3,5,6,8")
            self.assertEqual(compress_page_list([]), "")

        def test_get_annotation_error(self):
            self.assertEqual(get_annotation_error("1,2,2", 10), AnnotateError.NOT_UNIQUE)
            self.assertEqual(get_annotation_error("5-3", 10), AnnotateError.INVALID_RANGE)
            self.assertEqual(get_annotation_error("a,b,c", 10), AnnotateError.INVALID_SYNTAX)
            self.assertEqual(get_annotation_error("1,4,3", 10), AnnotateError.NOT_ORDERED)
            self.assertEqual(get_annotation_error("1,2,11", 10), AnnotateError.OUT_OF_BOUNDS)
            self.assertIsNone(get_annotation_error("1,3,5-7", 10))
            self.assertIsNone(get_annotation_error("1,2,3,4,5", 10))



    unittest.main(verbosity=2)
