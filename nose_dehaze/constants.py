PADDED_NEWLINE = "\n{}".format(" " * 10)

MOCK_CALL_COUNT_MSG = "{padding}{label}Mock {mock_name} called {num} times."
TYPE_MISMATCH_HINT_MSG = "{padding}{label} {vtype}"

ASSERT_METHODS = {
    "assertEqual",
    "assertEquals",  # same as assertEqual but "deprecated" and likely still used
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
