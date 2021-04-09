from functools import partial

from termcolor import colored

PADDED_NEWLINE = "\n{}".format(" " * 10)
MOCK_CALL_COUNT_MSG = "{padding}{label}Mock {mock_name} called {num} times."
TYPE_MISMATCH_HINT_MSG = "{padding}{label} {vtype}"

FRAME_LOCALS_EXPECTED_ACTUAL_KEYS = {
    "assertEqual": ("first", "second"),
    "assertEquals": ("first", "second"),
    "assertNotEqual": ("first", "second"),
    "assertDictEqual": ("d1", "d2"),
    "assertSetEqual": ("set1", "set2"),
    "assertTupleEqual": ("tuple1", "tuple2"),
    "assertListEqual": ("list1", "list2"),
    "assertSequenceEqual": ("seq1", "seq2"),
    "assertIs": ("expr1", "expr2"),
    "assertIsNot": ("expr1", "expr2"),
}


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
