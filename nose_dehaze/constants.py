from functools import partial

from termcolor import colored

PADDED_NEWLINE = "\n{}".format(" " * 10)
MOCK_CALL_COUNT_MSG = "{padding}{label}Mock {mock_name} called {num} times."
TYPE_MISMATCH_HINT_MSG = "{padding}{label} {vtype}"
ASSERT_METHODS = {
    "assertEqual",
    "assertEquals",  # same as assertEqual but "deprecated" and likely still used
    "assertNotEqual",
    "assertDictEqual",  # automatically called by assertEqual but likely called directly
    "assertTrue",
    "assertFalse",
    # mocks
    "assert_called_once",
    "assert_not_called",
    "assert_called_once_with",
    "assert_called_with",
    "assert_has_calls",
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
