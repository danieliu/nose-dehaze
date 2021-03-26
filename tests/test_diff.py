from unittest import TestCase

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from nose_dehaze.diff import assert_bool_diff


class AssertBoolDiffTest(TestCase):
    def test_actual_is_boolean_returns_without_hint(self):
        frame_locals = {
            "expr": False,
            "msg": "False is not True",
            "self": Mock(),  # unittest.TestCase instance
        }
        result = assert_bool_diff("assertTrue", frame_locals)

        expected = "True"
        actual = "False"
        hint = None
        self.assertEqual((expected, actual, hint), result)

    def test_actual_is_falsy_int_returns_with_hint(self):
        frame_locals = {
            "expr": 0,
            "msg": "0 is not True",
            "self": Mock(),  # unittest.TestCase instance
        }
        result = assert_bool_diff("assertTrue", frame_locals)

        expected = "True"
        actual = "0"
        hint = "\x1b[1m\x1b[31m0\x1b[0m is \x1b[1m\x1b[31mfalsy\x1b[0m"
        self.assertEqual((expected, actual, hint), result)
