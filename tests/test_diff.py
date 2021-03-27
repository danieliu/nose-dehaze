from unittest import TestCase

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from nose_dehaze.diff import (
    assert_bool_diff,
    assert_call_count_diff,
    get_mock_assert_diff,
)


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


class AssertCallCountDiffTest(TestCase):
    def test_called_once_returns_message_with_count_1(self):
        mock_instance = Mock()
        result = assert_call_count_diff(
            "assert_called_once", mock_instance.method, "mock_name"
        )

        expected = "Mock \x1b[1m\x1b[33mmock_name\x1b[0m called 1 times."
        actual = "Mock \x1b[1m\x1b[33mmock_name\x1b[0m called 0 times."
        self.assertEqual((expected, actual, None), result)

    def test_not_called_returns_message_with_count_0(self):
        mock_instance = Mock()
        mock_instance.method()
        mock_instance.method()

        result = assert_call_count_diff(
            "assert_not_called", mock_instance.method, "mock_name"
        )

        expected = "Mock \x1b[1m\x1b[33mmock_name\x1b[0m called 0 times."
        actual = "Mock \x1b[1m\x1b[33mmock_name\x1b[0m called 2 times."
        self.assertEqual((expected, actual, None), result)


class GetMockAssertDiffTest(TestCase):
    def test_assert_called_once_returns_call_count_diff(self):
        assert_method = "assert_called_once"
        mock_instance = Mock(name="original").an_attribute.a_method
        frame_locals = {
            "msg": "Expected 'original.an_attribute.a_method' to have been called once. Called 0 times.",  # noqa: E501
            "self": mock_instance,
        }

        result = get_mock_assert_diff(assert_method, frame_locals)

        expected = (
            "Mock \x1b[1m\x1b[33moriginal.an_attribute.a_method\x1b[0m called 1 times."
        )
        actual = (
            "Mock \x1b[1m\x1b[33moriginal.an_attribute.a_method\x1b[0m called 0 times."
        )
        self.assertEqual((expected, actual, None), result)

    def test_assert_not_called_returns_call_count_diff(self):
        assert_method = "assert_not_called"
        mock_instance = Mock(name="original").an_attribute.a_method
        mock_instance()
        mock_instance()
        frame_locals = {
            "msg": "Expected 'original.an_attribute.a_method' to not have been called. Called 2 times.\nCalls: [call()].",  # noqa: E501
            "self": mock_instance,
        }

        result = get_mock_assert_diff(assert_method, frame_locals)

        expected = (
            "Mock \x1b[1m\x1b[33moriginal.an_attribute.a_method\x1b[0m called 0 times."
        )
        actual = (
            "Mock \x1b[1m\x1b[33moriginal.an_attribute.a_method\x1b[0m called 2 times."
        )
        self.assertEqual((expected, actual, None), result)
