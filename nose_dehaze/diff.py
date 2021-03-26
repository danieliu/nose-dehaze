"""
utils for diffing, completely "borrowed" from pytest-clarity
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
from termcolor import colored

from nose_dehaze.constants import (
    MOCK_CALL_COUNT_MSG,
    PADDED_NEWLINE,
    TYPE_MISMATCH_HINT_MSG,
)
from nose_dehaze.utils import extract_mock_name

if TYPE_CHECKING:
    from mock import Mock


def utf8_replace(s):
    try:
        return text_type(s, "utf-8", "replace")
    except TypeError:
        return s


class Colour(object):
    red = "red"
    green = "green"
    cyan = "cyan"
    yellow = "yellow"
    stop = "\033[0m"


class Attr(object):
    bold = "bold"


deleted_text = partial(colored, color=Colour.red, attrs=[Attr.bold])
diff_intro_text = partial(colored, color=Colour.cyan, attrs=[Attr.bold])
inserted_text = partial(colored, color=Colour.green, attrs=[Attr.bold])
header_text = partial(colored, color=Colour.yellow, attrs=[Attr.bold])


def non_formatted(text):
    return Colour.stop + text


def build_split_diff(lhs_repr, rhs_repr):
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


def build_unified_diff(lhs_repr, rhs_repr):
    differ = difflib.Differ()
    lines_lhs, lines_rhs = lhs_repr.splitlines(), rhs_repr.splitlines()
    diff = differ.compare(lines_lhs, lines_rhs)

    output = []
    for line in diff:
        # Differ instructs us how to transform left into right, but we want
        # our colours to indicate how to transform right into left
        if line.startswith("- "):
            output.append(inserted_text(" L " + line[2:]))
        elif line.startswith("+ "):
            output.append(deleted_text(" R " + line[2:]))
        elif line.startswith("? "):
            # We can use this to find the index of change in the
            # line above if required in the future
            pass
        else:
            output.append(non_formatted(line))

    return output


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
        else:
            hints.append(None)

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
    # type: (str, Mock, str, dict) -> tuple
    hint = None
    expected = assert_method == "assertTrue"
    actual = frame_locals["expr"]

    if not isinstance(actual, bool):
        booly = "falsy" if assert_method == "assertTrue" else "truthy"
        hint = "{expr} is {booly}".format(
            expr=deleted_text(actual),
            booly=deleted_text(booly),
        )

    return pformat(expected), pformat(actual), hint


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

    if assert_method in {"assertEqual", "assertEquals"}:
        expected = frame_locals["first"]
        actual = frame_locals["second"]

        # add hint when types differ
        if type(expected) is not type(actual):
            expected_line = TYPE_MISMATCH_HINT_MSG.format(
                padding=PADDED_NEWLINE,
                label=header_text("Expected:"),
                vtype=deleted_text(type(expected)),
            )
            actual_line = TYPE_MISMATCH_HINT_MSG.format(
                padding=" " * 12,
                label=header_text("Actual:"),
                vtype=inserted_text(type(actual)),
            )
            hint = "\n".join(
                [
                    "expected and actual are different types",
                    expected_line,
                    actual_line,
                ]
            )

        if isinstance(expected, dict) and isinstance(actual, dict):
            # pad newlines to align to "Expected: "
            expected = pformat(expected, width=1)
            actual = pformat(actual, width=1)
        elif isinstance(expected, list) and isinstance(actual, list):
            expected = pformat(expected)
            actual = pformat(actual)
        else:
            expected = pformat(expected)
            actual = pformat(actual)
    elif assert_method == "assertNotEqual":
        first = pformat(frame_locals["first"])
        second = pformat(frame_locals["second"])
        comparison = partial("{first} {op} {second}".format, first=first, second=second)
        expected = comparison(op="!=")
        actual = comparison(op="==")
    elif assert_method == "assertDictEqual":
        expected = pformat(frame_locals["d1"], width=1)
        actual = pformat(frame_locals["d2"], width=1)
    elif assert_method in {"assertTrue", "assertFalse"}:
        expected = pformat(assert_method == "assertTrue")
        expr = frame_locals["expr"]
        actual = pformat(expr)

        # add hint when the value being checked isn't a bool
        if not isinstance(expr, bool):
            booly = "falsy" if assert_method == "assertTrue" else "truthy"
            hint = "{expr} is {booly}".format(
                expr=deleted_text(actual),
                booly=deleted_text(booly),
            )
    elif assert_method in {"assert_called_once", "assert_not_called"}:
        mock_instance = frame_locals["self"]
        mock_name = header_text(extract_mock_name(mock_instance))
        expected_call_count = {
            "assert_called_once": 1,
            "assert_not_called": 0,
        }[assert_method]
        expected = MOCK_CALL_COUNT_MSG.format(
            padding="",
            label="",
            mock_name=mock_name,
            num=expected_call_count,
        )
        actual = MOCK_CALL_COUNT_MSG.format(
            padding="",
            label="",
            mock_name=mock_name,
            num=mock_instance.call_count,
        )
    elif assert_method == "assert_called_once_with":
        formatted_output = build_call_args_diff_output(
            frame_locals["self"],
            frame_locals["args"],
            frame_locals["kwargs"],
        )
    elif assert_method == "assert_called_with":
        mock_instance = frame_locals["self"]
        mock_name = extract_mock_name(mock_instance)

        expected_args = frame_locals["args"]
        expected_kwargs = frame_locals["kwargs"]

        # TODO: diff against and colorize each call individually
        actual = pformat([c for c in mock_instance.call_args_list], width=1).replace(
            "call", mock_name
        )
        expected = str(call(*expected_args, **expected_kwargs)).replace(
            "call", mock_name
        )
    elif assert_method == "assert_has_calls":
        mock_instance = frame_locals["self"]
        mock_name = extract_mock_name(mock_instance)

        expected_calls = frame_locals["expected"]

        expected = pformat([c for c in expected_calls], width=1).replace(
            "call", mock_name
        )
        actual = pformat([c for c in mock_instance.call_args_list], width=1).replace(
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
