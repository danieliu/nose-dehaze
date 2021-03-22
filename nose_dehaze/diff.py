"""
utils for diffing, completely "borrowed" from pytest-clarity
"""
import difflib
from pprint import pformat
from functools import partial

try:
    from unittest.mock import call
except ImportError:
    from mock import call

import six
from six import text_type
from termcolor import colored

from nose_dehaze.constants import PADDED_NEWLINE
from nose_dehaze.utils import extract_mock_name


def utf8_replace(s):
    try:
        return text_type(s, "utf-8", "replace")
    except TypeError:
        return s


def direct_type_mismatch(lhs, rhs):
    return type(lhs) is not type(rhs)


def display_op_for(pytest_op):
    return "==" if pytest_op == "equal" else pytest_op


def possibly_missing_eq(lhs, rhs):
    try:
        left_dict, right_dict = vars(lhs), vars(rhs)
        return (type(lhs) is type(rhs)) and lhs != rhs and left_dict == right_dict
    except TypeError:
        return False


def has_differing_len(lhs, rhs):
    try:
        return len(lhs) != len(rhs)
    except TypeError:
        return False


def pformat_no_color(s, width):
    if isinstance(s, six.string_types):
        return '"' + s + '"'
    return pformat(s, width=width)


class Colour(object):
    red = "red"
    green = "green"
    cyan = "cyan"
    yellow = "yellow"
    stop = "\033[0m"


class BgColour(object):
    red = "on_red"
    green = "on_green"


class Attr(object):
    bold = "bold"


deleted_text = partial(colored, color=Colour.red, attrs=[Attr.bold])
diff_intro_text = partial(colored, color=Colour.cyan, attrs=[Attr.bold])
inserted_text = partial(colored, color=Colour.green, attrs=[Attr.bold])
header_text = partial(colored, color=Colour.yellow, attrs=[Attr.bold])


def non_formatted(text):
    return Colour.stop + text


def hint_text(text):
    bold_cyan = colored(text, color=Colour.cyan, attrs=[Attr.bold])
    return bold_cyan


def hint_body_text(text):
    bold_red = colored(Colour.stop + text, color=Colour.red, attrs=[Attr.bold])
    return bold_red


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
    expected_result = []
    actual_result = []
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
                    etype=deleted_text(
                        type(expected), atype=inserted_text(type(actual))
                    ),
                )
            )
        else:
            hints.append(None)

        exp, act = build_split_diff(pformat(a), pformat(b))
        expected_result.append("\n".join(exp))
        actual_result.append("\n".join(act))

        i += 1

    # handle different arg lengths
    if i == expected_length and i < actual_length:
        for remaining_arg in actual[i:]:
            actual_result.append(deleted_text(pformat(remaining_arg)))

    if i == actual_length and i < expected_length:
        for remaining_arg in expected[i:]:
            expected_result.append(inserted_text(pformat(remaining_arg)))

    return expected_result, actual_result


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
    args, kwargs = mock_instance.call_args

    expected_result, actual_result = build_args_diff(e_args, args)
    expected_kwargs, actual_kwargs = build_split_diff(
        pformat(e_kwargs), pformat(kwargs)
    )

    extra_padding = " " * (len(mock_name) + 1)
    pad = PADDED_NEWLINE + extra_padding

    sep_e = ",{pad}".format(pad=pad) if e_args and e_kwargs else ""
    sep_a = ",{pad}".format(pad=pad) if args and kwargs else ""
    exp = "{mock_name}({exp}{sep}{ekw})".format(
        mock_name=header_text(mock_name),
        exp=", ".join(expected_result),
        sep=sep_e,
        ekw="\n".join(expected_kwargs) if e_kwargs else "",
    )
    act = "{mock_name}({act}{sep}{akw})".format(
        mock_name=header_text(mock_name),
        act=", ".join(actual_result),
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
