"""
diff utils to extract assert values and build colorized diff output
"""
import difflib
from functools import partial
from pprint import pformat
from typing import TYPE_CHECKING

try:
    from unittest.mock import call
except ImportError:
    from mock import call

from six import text_type

from nose_dehaze.constants import (
    MOCK_CALL_COUNT_MSG,
    PADDED_NEWLINE,
    TYPE_MISMATCH_HINT_MSG,
    Colour,
    deleted_text,
    diff_intro_text,
    header_text,
    inserted_text,
)
from nose_dehaze.utils import extract_mock_name

if TYPE_CHECKING:
    from mock import Mock


def utf8_replace(s):
    try:
        return text_type(s, "utf-8", "replace")
    except TypeError:
        return s


def build_split_diff(lhs_repr, rhs_repr):
    # type: (str, str) -> tuple
    """
    Copy pasted from pytest-clarity.

    Compares string representations of expected and actual, building the colorized
    diff output for consumption.

    :param lhs_repr: the string representation of the "left" i.e. expected
    :param rhs_repr: the string representation of the "right" i.e. actual
    :return: tuple of the "left" and "right" colorized newline separated strings
    """
    lhs_out, rhs_out = "", ""

    matcher = difflib.SequenceMatcher(None, lhs_repr, rhs_repr)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():

        lhs_substring_lines = lhs_repr[i1:i2].splitlines()
        rhs_substring_lines = rhs_repr[j1:j2].splitlines()

        for i, lhs_substring in enumerate(lhs_substring_lines):
            if op == "replace":
                lhs_out += inserted_text(lhs_substring)
            elif op == "delete":
                lhs_out += inserted_text(lhs_substring)
            elif op == "insert":
                lhs_out += Colour.stop + lhs_substring
            elif op == "equal":
                lhs_out += Colour.stop + lhs_substring

            if i != len(lhs_substring_lines) - 1:
                lhs_out += "\n"

        for j, rhs_substring in enumerate(rhs_substring_lines):
            if op == "replace":
                rhs_out += deleted_text(rhs_substring)
            elif op == "insert":
                rhs_out += deleted_text(rhs_substring)
            elif op == "equal":
                rhs_out += Colour.stop + rhs_substring

            if j != len(rhs_substring_lines) - 1:
                rhs_out += "\n"

    return lhs_out.splitlines(), rhs_out.splitlines()


def build_args_diff(expected, actual):
    # type: (tuple, tuple) -> tuple
    """
    Loops through expected/actual arg tuples and builds out the diff between each
    individual pair of args.

    :param expected: the expected called args tuple
    :param actual: the actual called args tuple
    :return: colorized, formatted diff str
    """
    i = 0
    expected_args = []
    actual_args = []
    hints = []

    expected_length = len(expected)
    actual_length = len(actual)

    while not (i == expected_length or i == actual_length):
        a = expected[i]
        b = actual[i]

        if type(expected) is not type(actual):
            hints.append(
                "Arg {num} expected type: {etype}, actual type: {atype}".format(
                    num=i + 1,
                    etype=deleted_text(type(expected)),
                    atype=inserted_text(type(actual)),
                )
            )

        act, exp = build_split_diff(pformat(b), pformat(a))
        expected_args.append("\n".join(exp))
        actual_args.append("\n".join(act))

        i += 1

    # handle different arg lengths
    if i == actual_length and i < expected_length:
        for remaining_arg in expected[i:]:
            expected_args.append(deleted_text(pformat(remaining_arg)))

    if i == expected_length and i < actual_length:
        for remaining_arg in actual[i:]:
            actual_args.append(inserted_text(pformat(remaining_arg)))

    return expected_args, actual_args


def build_call_args_diff_output(mock_instance, e_args, e_kwargs):
    # type: (Mock, tuple, dict) -> str
    """
    Creates the formatted, colorized output for mock.assert_called_with failures.

    Handles both assert_called_once_with checks
    1. call count
    2. args & kwargs

    :param mock_instance: the Mock instance asserted upon
    :param e_args: the expected function args the mock was called with
    :param e_kwargs: the expected function kwargs the mock was called with
    """
    mock_name = extract_mock_name(mock_instance)

    args = ()
    kwargs = {}
    if mock_instance.call_args is not None:
        args, kwargs = mock_instance.call_args

    extra_padding = " " * (len(mock_name) + 1)
    pad = PADDED_NEWLINE + extra_padding

    kwarg_str = ",{}".format(pad).join(
        ["{k}={v}".format(k=k, v=pformat(v)) for k, v in kwargs.items()]
    )
    e_kwarg_str = ",{}".format(pad).join(
        ["{k}={v}".format(k=k, v=pformat(v)) for k, v in e_kwargs.items()]
    )

    expected_args, actual_args = build_args_diff(e_args, args)
    actual_kwargs, expected_kwargs = build_split_diff(kwarg_str, e_kwarg_str)

    sep_e = ",{pad}".format(pad=pad) if e_args and e_kwargs else ""
    sep_a = ",{pad}".format(pad=pad) if args and kwargs else ""
    exp = "{mock_name}({exp}{sep}{ekw})".format(
        mock_name=header_text(mock_name),
        exp=", ".join(expected_args),
        sep=sep_e,
        ekw="\n".join(expected_kwargs) if e_kwargs else "",
    )
    act = "{mock_name}({act}{sep}{akw})".format(
        mock_name=header_text(mock_name),
        act=", ".join(actual_args),
        sep=sep_a,
        akw="\n".join(actual_kwargs) if kwargs else "",
    )

    formatted_output = (
        "\n\n{expected_label} {expected}\n  {actual_label} {actual}"
    ).format(
        expected_label=Colour.stop + diff_intro_text("Expected:"),
        expected=utf8_replace(exp),
        actual_label=Colour.stop + diff_intro_text("Actual:"),
        actual=utf8_replace(act),
    )

    return formatted_output


def assert_bool_diff(assert_method, frame_locals):
    # type: (str, dict) -> tuple
    hint = None
    expected = assert_method == "assertTrue"
    actual = frame_locals["expr"]

    if not isinstance(actual, bool):
        booly = "falsy" if assert_method == "assertTrue" else "truthy"
        hint = "{expr} is {booly}".format(
            expr=deleted_text(pformat(actual)),
            booly=deleted_text(booly),
        )

    return pformat(expected), pformat(actual), hint


def assert_call_count_diff(assert_method, mock_instance, mock_name):
    # type: (str, Mock, str) -> tuple
    expected_call_count = {
        "assert_called_once": 1,
        "assert_not_called": 0,
    }[assert_method]
    actual_call_count = mock_instance.call_count

    message = partial(
        "Mock {mock_name} called {count} times.".format,
        mock_name=header_text(mock_name),
    )
    expected = message(count=expected_call_count)
    actual = message(count=actual_call_count)

    return expected, actual, None


def assert_called_with_diff(assert_method, mock_instance, mock_name, frame_locals):
    # type: (str, Mock, str, dict) -> tuple
    expected_args = frame_locals["args"]
    expected_kwargs = frame_locals["kwargs"]

    # TODO: diff against and colorize each call individually
    expected = str(call(*expected_args, **expected_kwargs)).replace("call", mock_name)
    actual = pformat([c for c in mock_instance.call_args_list], width=1).replace(
        "call", mock_name
    )

    return expected, actual, None


def assert_has_calls_diff(assert_method, mock_instance, mock_name, frame_locals):
    # type: (str, Mock, str, dict) -> tuple
    hint = None
    expected_calls = frame_locals["expected"]

    # expected is a normal list, mock call_args_list is a CallList so we coerce to a
    # normal list for consistent formatting
    expected = pformat(expected_calls, width=1).replace("call", mock_name)
    actual = pformat(list(mock_instance.call_args_list), width=1).replace(
        "call", mock_name
    )

    if not mock_instance.call_count == len(expected_calls):
        expected_line = MOCK_CALL_COUNT_MSG.format(
            padding=PADDED_NEWLINE,
            label=header_text("Expected: "),
            mock_name=header_text(mock_name),
            num=deleted_text(len(expected_calls)),
        )
        actual_line = MOCK_CALL_COUNT_MSG.format(
            padding=" " * 12,
            label=header_text("Actual: "),
            mock_name=header_text(mock_name),
            num=inserted_text(mock_instance.call_count),
        )
        hint = "\n".join(
            [
                "expected and actual call counts differ",
                expected_line,
                actual_line,
            ]
        )

    return expected, actual, hint


def get_assert_equal_diff(assert_method, frame_locals):
    # type: (str, dict) -> tuple
    expected_key, actual_key = {
        "assertEqual": ("first", "second"),
        "assertEquals": ("first", "second"),
        "assertNotEqual": ("first", "second"),
        "assertDictEqual": ("d1", "d2"),
        "assertSetEqual": ("set1", "set2"),
        "assertTupleEqual": ("tuple1", "tuple2"),
        "assertListEqual": ("list1", "list2"),
    }[assert_method]

    hint = None
    expected_value = frame_locals[expected_key]
    actual_value = frame_locals[actual_key]

    expected_type = type(expected_value)
    actual_type = type(actual_value)

    expected_pformat_kwargs = {}  # type: dict
    actual_pformat_kwargs = {}  # type: dict

    if assert_method == "assertNotEqual":
        comparison = partial(
            "{expected} {op} {actual}".format,
            expected=pformat(expected_value),
            actual=pformat(actual_value),
        )
        expected = comparison(op="!=")
        actual = comparison(op="==")
        return expected, actual, hint

    if isinstance(expected_value, dict):
        expected_pformat_kwargs["width"] = 1
    if isinstance(actual_value, dict):
        actual_pformat_kwargs["width"] = 1

    if expected_type is not actual_type:
        hint_expected = TYPE_MISMATCH_HINT_MSG.format(
            padding=PADDED_NEWLINE,
            label=header_text("Expected:"),
            vtype=deleted_text(expected_type),
        )
        hint_actual = TYPE_MISMATCH_HINT_MSG.format(
            padding=" " * 12,
            label=header_text("Actual:"),
            vtype=inserted_text(actual_type),
        )
        hint = "\n".join(
            [
                "expected and actual are different types",
                hint_expected,
                hint_actual,
            ]
        )

    expected = pformat(expected_value, **expected_pformat_kwargs)
    actual = pformat(actual_value, **actual_pformat_kwargs)

    return expected, actual, hint


def get_mock_assert_diff(assert_method, frame_locals):
    # type: (str, dict) -> tuple
    mock_instance = frame_locals["self"]
    mock_name = extract_mock_name(mock_instance)

    assert_diff_func = {
        "assert_called_once": partial(
            assert_call_count_diff, assert_method, mock_instance, mock_name
        ),
        "assert_not_called": partial(
            assert_call_count_diff, assert_method, mock_instance, mock_name
        ),
        "assert_called_once_with": None,
        "assert_called_with": partial(
            assert_called_with_diff,
            assert_method,
            mock_instance,
            mock_name,
            frame_locals,
        ),
        "assert_has_calls": partial(
            assert_has_calls_diff,
            assert_method,
            mock_instance,
            mock_name,
            frame_locals,
        ),
    }[assert_method]

    return assert_diff_func()


def dehaze(assert_method, frame_locals):
    # type: (str, dict) -> str
    """
    Given a test assert method, e.g. assertEqual, extracts the corresponding relevant
    local variables needed to reconstruct the reason for assertion failure and render
    a "dehazed" output with coloring and formatting for readability.

    :param assert_method: the test assertion method
    :param frame_locals: the traceback frame local variables
    :return: the dehazed (colorized, formatted) output string
    """
    expected = None
    actual = None
    hint = None
    formatted_output = None

    diff_func = {
        # equal
        "assertEqual": get_assert_equal_diff,
        "assertEqual": get_assert_equal_diff,
        "assertEquals": get_assert_equal_diff,
        "assertNotEqual": get_assert_equal_diff,
        "assertDictEqual": get_assert_equal_diff,
        "assertSetEqual": get_assert_equal_diff,
        "assertTupleEqual": get_assert_equal_diff,
        "assertListEqual": get_assert_equal_diff,
        # bool
        "assertTrue": assert_bool_diff,
        "assertFalse": assert_bool_diff,
        # mock
        "assert_called_once": get_mock_assert_diff,
        "assert_not_called": get_mock_assert_diff,
        "assert_called_with": get_mock_assert_diff,
        "assert_has_calls": get_mock_assert_diff,
    }.get(assert_method)

    if diff_func is not None:
        expected, actual, hint = diff_func(assert_method, frame_locals)
    elif assert_method == "assert_called_once_with":
        formatted_output = build_call_args_diff_output(
            frame_locals["self"],
            frame_locals["args"],
            frame_locals["kwargs"],
        )

    if expected and actual and not formatted_output:
        act, exp = build_split_diff(actual, expected)
        formatted_output = (
            "\n\n{expected_label} {expected}\n  {actual_label} {actual}"
        ).format(
            expected_label=Colour.stop + diff_intro_text("Expected:"),
            expected=utf8_replace(PADDED_NEWLINE.join(exp)),
            actual_label=Colour.stop + diff_intro_text("Actual:"),
            actual=utf8_replace(PADDED_NEWLINE.join(act)),
        )

    if hint is not None:
        hint_output = "\n\n    {hint_label} {hint}".format(
            hint_label=Colour.stop + diff_intro_text("hint:"),
            hint=hint,
        )
        formatted_output += hint_output
    return formatted_output
