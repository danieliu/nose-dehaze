from unittest import TestCase

try:
    from unittest.mock import Mock, call
except ImportError:
    from mock import call, Mock

from nose_dehaze.diff import (
    assert_bool_diff,
    assert_call_count_diff,
    assert_called_with_diff,
    assert_has_calls_diff,
    assert_is_instance_diff,
    assert_is_none_diff,
    get_assert_equal_diff,
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

    def test_actual_is_falsy_str_returns_with_hint(self):
        frame_locals = {
            "expr": "",
            "msg": "'' is not True",
            "self": Mock(),  # unittest.TestCase instance
        }
        result = assert_bool_diff("assertTrue", frame_locals)

        expected = "True"
        actual = "''"
        hint = "\x1b[1m\x1b[31m''\x1b[0m is \x1b[1m\x1b[31mfalsy\x1b[0m"
        self.assertEqual((expected, actual, hint), result)


class AssertIsNoneDiffTest(TestCase):
    def test_is_none_returns_expected_is_and_actual_is_not(self):
        frame_locals = {
            "msg": None,
            "obj": "hello",
            "self": Mock(),  # unittest.TestCase instance
            "standardMsg": "'hello' is not None",
        }
        result = assert_is_none_diff("assertIsNone", frame_locals)

        expected = "'hello' is None."
        actual = "'hello' is not None."
        hint = None
        self.assertEqual((expected, actual, hint), result)

    def test_is_not_none_returns_expected_is_not_and_actual_is(self):
        frame_locals = {
            "msg": None,
            "obj": None,
            "self": Mock(),  # unittest.TestCase instance
            "standardMsg": "unexpectedly None",
        }
        result = assert_is_none_diff("assertIsNotNone", frame_locals)

        expected = "None is not None."
        actual = "None is None."
        hint = None
        self.assertEqual((expected, actual, hint), result)


class AssertIsInstanceDiffTest(TestCase):
    def test_single_expected_instance(self):
        frame_locals = {
            "cls": dict,
            "msg": None,
            "obj": "hello",
            "self": Mock(),  # unittest.TestCase instance
            "standardMsg": "'hello' is not an instance of <class 'dict'>",
        }
        result = assert_is_instance_diff("assertIsInstance", frame_locals)

        expected = "<class 'dict'>"
        actual = "(<class 'str'>,\n <class 'object'>)"
        hint = None
        self.assertEqual((expected, actual, hint), result)

    def test_multiple_expected_instances(self):
        class SomeClass(object):
            pass

        class Mixin(object):
            pass

        class SubA(SomeClass):
            pass

        class Actual(SubA, Mixin):
            pass

        actual_obj = Actual()

        frame_locals = {
            "cls": (dict, list, int),
            "msg": None,
            "obj": actual_obj,
            "self": Mock(),  # unittest.TestCase instance
            "standardMsg": (
                "<tests.test_diff.AssertIsInstanceDiffTest.test_multiple_expected_instances.<locals>.Actual object at 0x11214e8e0> "  # noqa: E501
                "is not an instance of (<class 'dict'>, <class 'list'>, <class 'int'>)"
            ),
        }
        result = assert_is_instance_diff("assertIsInstance", frame_locals)

        expected = "(<class 'dict'>,\n <class 'list'>,\n <class 'int'>)"
        actual = (
            "(<class 'tests.test_diff.AssertIsInstanceDiffTest.test_multiple_expected_instances.<locals>.Actual'>,\n"  # noqa: E501
            " <class 'tests.test_diff.AssertIsInstanceDiffTest.test_multiple_expected_instances.<locals>.SubA'>,\n"  # noqa: E501
            " <class 'tests.test_diff.AssertIsInstanceDiffTest.test_multiple_expected_instances.<locals>.SomeClass'>,\n"  # noqa: E501
            " <class 'tests.test_diff.AssertIsInstanceDiffTest.test_multiple_expected_instances.<locals>.Mixin'>,\n"  # noqa: E501
            " <class 'object'>)"
        )
        hint = None
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


class AssertCalledWithDiffTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assert_method = "assert_called_with"
        cls.mock_name = "mockname"

    def test_no_actual_calls_but_expected_args_and_kwargs(self):
        mock_instance = Mock(name=self.mock_name)

        frame_locals = {
            "actual": "not called.",
            "args": ("arg1", 2),  # expected args
            "error_message": (
                "Expected call not found.\n"
                "Expected: mockname('arg1', 2, kw_a='value_a', kw_b='value_b')\n"
                "Actual: not called."
            ),
            "expected": "mockname('arg1', 2, kw_a='value_a', kw_b='value_b')",
            "kwargs": {"kw_a": "value_a", "kw_b": "value_b"},  # expected kwargs
            "self": mock_instance,
        }
        result = assert_called_with_diff(
            self.assert_method, mock_instance, self.mock_name, frame_locals
        )
        expected = "mockname('arg1', 2, kw_a='value_a', kw_b='value_b')"
        actual = "[]"
        self.assertEqual((expected, actual, None), result)

    def test_single_actual_call_but_expected_args_and_kwargs_mismatch(self):
        mock_instance = Mock(name=self.mock_name)
        mock_instance("1", 2, kw_a="a", kw_b="b")

        frame_locals = {
            "_error_message": Mock(),  # NonCallableMock._error_message func
            "actual": call("1", 2, kw_a="a", kw_b="b"),  # most recent call on the mock
            "args": ("arg1", 2),  # expected args
            "expected": call(
                "arg1", 2, kw_a="expected_value_a", kw_b="expected_value_b"
            ),
            "kwargs": {
                "kw_a": "expected_value_a",
                "kw_b": "expected_value_b",
            },  # expected kwargs
            "self": mock_instance,
        }
        result = assert_called_with_diff(
            self.assert_method, mock_instance, self.mock_name, frame_locals
        )
        expected = (
            "mockname('arg1', 2, kw_a='expected_value_a', kw_b='expected_value_b')"
        )
        actual = "[mockname('1', 2, kw_a='a', kw_b='b')]"
        self.assertEqual((expected, actual, None), result)

    def test_multiple_actual_calls_but_expected_args_and_kwargs_mismatch(self):
        mock_instance = Mock(name=self.mock_name)
        mock_instance("1", 2, kw_a="a", kw_b="b")
        mock_instance("2", 3, kw_a="a", kw_b="b")

        frame_locals = {
            "_error_message": Mock(),  # NonCallableMock._error_message func
            "actual": call("2", 3, kw_a="a", kw_b="b"),  # most recent call on the mock
            "args": ("arg1", 2),  # expected args
            "expected": call(
                "arg1", 2, kw_a="expected_value_a", kw_b="expected_value_b"
            ),
            "kwargs": {
                "kw_a": "expected_value_a",
                "kw_b": "expected_value_b",
            },  # expected kwargs
            "self": mock_instance,
        }
        result = assert_called_with_diff(
            self.assert_method, mock_instance, self.mock_name, frame_locals
        )
        expected = (
            "mockname('arg1', 2, kw_a='expected_value_a', kw_b='expected_value_b')"
        )
        actual = (
            "[mockname('1', 2, kw_a='a', kw_b='b'),\n"
            " mockname('2', 3, kw_a='a', kw_b='b')]"
        )
        self.assertEqual((expected, actual, None), result)

    def test_no_expected_args_or_kwargs(self):
        mock_instance = Mock(name=self.mock_name)
        mock_instance("1", 2, kw_a="a", kw_b="b")
        frame_locals = {
            "_error_message": Mock(),  # NonCallableMock._error_message func
            "actual": call("1", 2, kw_a="a", kw_b="b"),  # most recent call on the mock
            "args": (),  # expected args
            "expected": call(),
            "kwargs": {},  # expected kwargs
            "self": mock_instance,
        }
        result = assert_called_with_diff(
            self.assert_method, mock_instance, self.mock_name, frame_locals
        )
        expected = "mockname()"
        actual = "[mockname('1', 2, kw_a='a', kw_b='b')]"
        self.assertEqual((expected, actual, None), result)


class AssertHasCallsDiffTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assert_method = "assert_has_calls"
        cls.mock_name = "multi_call"

    def test_call_count_mismatch_no_actual_calls_returns_hint(self):
        mock_instance = Mock(name=self.mock_name)
        frame_locals = {
            "all_calls": [],  # actual calls
            "any_order": False,
            "calls": [call(3, 5), call(3, 5)],  # expected calls
            "cause": None,
            "expected": [call(3, 5), call(3, 5)],  # expected calls
            "problem": "Calls not found.",
            "self": mock_instance,
        }
        result = assert_has_calls_diff(
            self.assert_method, mock_instance, self.mock_name, frame_locals
        )

        expected = "[multi_call(3, 5),\n multi_call(3, 5)]"
        actual = "[]"
        hint = (
            "expected and actual call counts differ\n\n"
            "          \x1b[1m\x1b[33mExpected: \x1b[0mMock \x1b[1m\x1b[33mmulti_call\x1b[0m called \x1b[1m\x1b[31m2\x1b[0m times.\n"  # noqa: E501
            "            \x1b[1m\x1b[33mActual: \x1b[0mMock \x1b[1m\x1b[33mmulti_call\x1b[0m called \x1b[1m\x1b[32m0\x1b[0m times."  # noqa: E501
        )
        self.assertEqual((expected, actual, hint), result)

    def test_call_count_equal_returns_no_hint(self):
        mock_instance = Mock(name=self.mock_name)
        mock_instance(3, 5)
        mock_instance(10, 20)
        frame_locals = {
            "all_calls": [call(3, 5), call(10, 20)],  # actual calls
            "any_order": False,
            "calls": [call(3, 5), call(3, 5)],  # expected calls
            "cause": None,
            "expected": [call(3, 5), call(3, 5)],  # expected calls
            "problem": "Calls not found.",
            "self": mock_instance,
        }
        result = assert_has_calls_diff(
            self.assert_method, mock_instance, self.mock_name, frame_locals
        )

        expected = "[multi_call(3, 5),\n multi_call(3, 5)]"
        actual = "[multi_call(3, 5),\n multi_call(10, 20)]"
        hint = None
        self.assertEqual((expected, actual, hint), result)


class GetAssertEqualDiffTest(TestCase):
    def test_same_types_returns_formatted_expected_and_actual_with_no_hint(self):
        frame_locals = {
            "assertion_func": Mock(),  # TestCase._baseAssertEqual method
            "first": "hello",
            "msg": None,
            "second": "world",
            "self": Mock(),  # TestCase class of current test method
        }
        result = get_assert_equal_diff("assertEqual", frame_locals)
        self.assertEqual(("'hello'", "'world'", None), result)

    def test_different_types_returns_with_hint(self):
        frame_locals = {
            "assertion_func": Mock(),  # TestCase._baseAssertEqual method
            "first": 1234,
            "msg": None,
            "second": "world",
            "self": Mock(),  # TestCase class of current test method
        }
        result = get_assert_equal_diff("assertEqual", frame_locals)
        hint = (
            "expected and actual are different types\n\n"
            "          \x1b[1m\x1b[33mExpected:\x1b[0m \x1b[1m\x1b[31m<class 'int'>\x1b[0m\n"  # noqa: E501
            "            \x1b[1m\x1b[33mActual:\x1b[0m \x1b[1m\x1b[32m<class 'str'>\x1b[0m"  # noqa: E501
        )
        self.assertEqual(("1234", "'world'", hint), result)

    def test_assert_equals_returns_successfully(self):
        frame_locals = {
            "assertion_func": Mock(),  # TestCase._baseAssertEqual method
            "first": "hello",
            "msg": None,
            "second": "world",
            "self": Mock(),  # TestCase class of current test method
        }
        result = get_assert_equal_diff("assertEquals", frame_locals)
        self.assertEqual(("'hello'", "'world'", None), result)

    def test_assert_not_equal_returns_successfully_without_hint(self):
        frame_locals = {
            "first": "hello",
            "msg": "'hello' == 'hello'",
            "second": "hello",
            "self": Mock(),  # TestCase class of current test method
        }
        result = get_assert_equal_diff("assertNotEqual", frame_locals)
        self.assertEqual(("'hello' != 'hello'", "'hello' == 'hello'", None), result)

    def test_assert_dict_equal_pformats_dicts_with_width_1_and_returns_successfully(
        self,
    ):
        frame_locals = {
            "d1": {"hello": "world", "number": 123},
            "d2": {"hello": "universe", "number": 999},
            "diff": (
                "\n"
                "- {'hello': 'world', 'number': 123}\n"
                "?            ^^ ^^             ^^^\n"
                "\n"
                "+ {'hello': 'universe', 'number': 999}\n"
                "?            ^^^^^ ^^             ^^^\n"
            ),
            "msg": None,
            "self": Mock(),  # TestCase class of current test method
            "standardMsg": (
                "{'hello': 'world', 'number': 123} != {'hello': 'universe', "
                "'number': 999}\n"
                "- {'hello': 'world', 'number': 123}\n"
                "?            ^^ ^^             ^^^\n"
                "\n"
                "+ {'hello': 'universe', 'number': 999}\n"
                "?            ^^^^^ ^^             ^^^\n"
            ),
        }
        result = get_assert_equal_diff("assertDictEqual", frame_locals)
        self.assertEqual(
            (
                "{'hello': 'world',\n 'number': 123}",
                "{'hello': 'universe',\n 'number': 999}",
                None,
            ),
            result,
        )

    def test_assert_set_equal(self):
        frame_locals = {
            "difference1": {8, 5, 6},
            "difference2": set(),
            "item": 6,
            "lines": ["Items in the first set but not the second:", "8", "5", "6"],
            "msg": None,
            "self": Mock(),  # TestCase class of current test method
            "set1": {1, 2, 3, 4, 5, 6, 8},
            "set2": {1, 2, 3, 4},
            "standardMsg": "Items in the first set but not the second:\n8\n5\n6",
        }

        result = get_assert_equal_diff("assertSetEqual", frame_locals)
        self.assertEqual(
            (
                "{1, 2, 3, 4, 5, 6, 8}",
                "{1, 2, 3, 4}",
                None,
            ),
            result,
        )

    def test_assert_tuple_equal(self):
        frame_locals = {
            "msg": None,
            "self": Mock(),  # TestCase class of current test method
            "tuple1": (1, 2, 3),
            "tuple2": (2, 3, 4),
        }

        result = get_assert_equal_diff("assertTupleEqual", frame_locals)
        self.assertEqual(
            (
                "(1, 2, 3)",
                "(2, 3, 4)",
                None,
            ),
            result,
        )

    def test_assert_list_equal(self):
        frame_locals = {
            "list1": [1, 2, 3, 5],
            "list2": [1, 2, 3, 4],
            "msg": None,
            "self": Mock(),  # TestCase class of current test method
        }
        result = get_assert_equal_diff("assertListEqual", frame_locals)
        self.assertEqual(
            (
                "[1, 2, 3, 5]",
                "[1, 2, 3, 4]",
                None,
            ),
            result,
        )

    def test_assert_sequence_equal(self):
        frame_locals = {
            "diffMsg": "\n- [1, 2, 3, 4, 5]\n+ [1, 3, 5, 2, 4]",
            "differing": (
                "Sequences differ: [1, 2, 3, 4, 5] != [1, 3, 5, 2, 4]\n\n"
                "First differing element 1:\n"
                "2\n"
                "3\n"
            ),
            "i": 1,
            "item1": 2,
            "item2": 3,
            "len1": 5,
            "len2": 5,
            "msg": (
                "Sequences differ: [1, 2, 3, 4, 5] != [1, 3, 5, 2, 4]\n\n"
                "First differing element 1:\n"
                "2\n"
                "3\n\n"
                "- [1, 2, 3, 4, 5]\n"
                "+ [1, 3, 5, 2, 4]"
            ),
            "self": Mock(),  # TestCase class of current test method
            "seq1": [1, 2, 3, 4, 5],
            "seq2": [1, 3, 5, 2, 4],
            "seq_type": None,
            "seq_type_name": "sequence",
            "standardMsg": (
                "Sequences differ: [1, 2, 3, 4, 5] != [1, 3, 5, 2, 4]\n\n"
                "First differing element 1:\n"
                "2\n"
                "3\n\n"
                "- [1, 2, 3, 4, 5]\n"
                "+ [1, 3, 5, 2, 4]"
            ),
        }
        result = get_assert_equal_diff("assertSequenceEqual", frame_locals)
        self.assertEqual(
            (
                "[1, 2, 3, 4, 5]",
                "[1, 3, 5, 2, 4]",
                None,
            ),
            result,
        )

    def test_assert_is(self):
        frame_locals = {
            "expr1": list,
            "expr2": dict,
            "msg": None,
            "self": Mock(),  # TestCase class of current test method
            "standardMsg": "<class 'list'> is not <class 'dict'>",
        }
        result = get_assert_equal_diff("assertIs", frame_locals)
        self.assertEqual(
            (
                "<class 'list'>",
                "<class 'dict'>",
                None,
            ),
            result,
        )

    def test_assert_is_not(self):
        frame_locals = {
            "expr1": dict,
            "expr2": dict,
            "msg": None,
            "self": Mock(),  # TestCase class of current test method
            "standardMsg": "unexpectedly identical: <class 'dict'>",
        }
        result = get_assert_equal_diff("assertIsNot", frame_locals)
        self.assertEqual(
            (
                "<class 'dict'> is not <class 'dict'>",
                "<class 'dict'> is <class 'dict'>",
                None,
            ),
            result,
        )


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

    def test_assert_called_with_returns_diff(self):
        assert_method = "assert_called_with"
        mock_instance = Mock(name="original").an_attribute.a_method
        mock_instance("1", 2, kw_a="a", kw_b="b")
        frame_locals = {
            "_error_message": Mock(),  # NonCallableMock._error_message func
            "actual": call("1", 2, kw_a="a", kw_b="b"),  # most recent call on the mock
            "args": (),  # expected args
            "expected": call(),
            "kwargs": {},  # expected kwargs
            "self": mock_instance,
        }
        result = get_mock_assert_diff(assert_method, frame_locals)

        expected = "original.an_attribute.a_method()"
        actual = "[original.an_attribute.a_method('1', 2, kw_a='a', kw_b='b')]"
        self.assertEqual((expected, actual, None), result)

    def test_assert_has_calls_returns_diff(self):
        assert_method = "assert_has_calls"
        mock_instance = Mock(name="original").an_attribute.a_method
        mock_instance()
        mock_instance()

        frame_locals = {
            "all_calls": [],  # actual calls
            "any_order": False,
            "calls": [call(3, 5), call(3, 5)],  # expected calls
            "cause": None,
            "expected": [call(3, 5), call(3, 5)],  # expected calls
            "problem": "Calls not found.",
            "self": mock_instance,
        }

        result = get_mock_assert_diff(assert_method, frame_locals)

        expected = (
            "[original.an_attribute.a_method(3, 5),\n"
            " original.an_attribute.a_method(3, 5)]"
        )
        actual = (
            "[original.an_attribute.a_method(),\n original.an_attribute.a_method()]"
        )
        hint = None
        self.assertEqual((expected, actual, hint), result)
