"""
utils for diffing, completely "borrowed" from pytest-clarity
"""
import difflib
import pprint
from functools import partial

import six
from six import text_type
from termcolor import colored


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
    return pprint.pformat(s, width=width)


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
