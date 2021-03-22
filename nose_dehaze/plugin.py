from pprint import pformat

try:
    from unittest.mock import call
except ImportError:
    from mock import call

from nose.plugins import Plugin

from nose_dehaze.constants import (
    MOCK_CALL_COUNT_MSG,
    PADDED_NEWLINE,
    TYPE_MISMATCH_HINT_MSG,
)
from nose_dehaze.diff import (
    Colour,
    build_call_args_diff_output,
    build_split_diff,
    deleted_text,
    diff_intro_text,
    header_text,
    inserted_text,
    utf8_replace,
)
from nose_dehaze.utils import extract_mock_name


class Dehaze(Plugin):
    enabled = False
    enableOpt = "dehaze"
    env_opt = "NOSE_DEHAZE"
    name = "nose-dehaze"
    score = 1020

    def options(self, parser, env):
        parser.add_option(
            "--dehaze",
            action="store_true",
            default=env.get(self.env_opt, False),
            dest="dehaze",
            help="Prettify and colorize test results output. Environment variable: {}".format(
                self.env_opt
            ),
        )

    def formatFailure(self, test, err):
        exc_class, exc_instance, tb = err

        tb2 = tb
        formatted_output = None
        expected = None
        actual = None
        hint = None
        while tb2 and formatted_output is None:
            frame = tb2.tb_frame
            co_name = frame.f_code.co_name

            if co_name == "assertEqual":
                expected = frame.f_locals["first"]
                actual = frame.f_locals["second"]

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
                    expected = pformat(expected, width=1).replace("\n", PADDED_NEWLINE)
                    actual = pformat(actual, width=1).replace("\n", PADDED_NEWLINE)
                elif isinstance(expected, list) and isinstance(actual, list):
                    expected = pformat(expected)
                    actual = pformat(actual)
                else:
                    expected = pformat(expected)
                    actual = pformat(actual)
            elif co_name in {"assertTrue", "assertFalse"}:
                expected = pformat(co_name == "assertTrue")
                expr = frame.f_locals["expr"]
                actual = pformat(expr)

                # add hint when the value being checked isn't a bool
                if not isinstance(expr, bool):
                    booly = "falsy" if co_name == "assertTrue" else "truthy"
                    hint = "{expr} is {booly}".format(
                        expr=deleted_text(actual),
                        booly=deleted_text(booly),
                    )
            elif co_name in {"assert_called_once", "assert_not_called"}:
                mock_instance = frame.f_locals["self"]
                mock_name = header_text(extract_mock_name(mock_instance))
                expected_call_count = {
                    "assert_called_once": 1,
                    "assert_not_called": 0,
                }[co_name]
                expected = MOCK_CALL_COUNT_MSG.format(
                    padding="", mock_name=mock_name, num=expected_call_count
                )
                actual = MOCK_CALL_COUNT_MSG.format(
                    padding="", mock_name=mock_name, num=mock_instance.call_count
                )
            elif co_name == "assert_called_once_with":
                formatted_output = build_call_args_diff_output(
                    frame.f_locals["self"],
                    frame.f_locals["args"],
                    frame.f_locals["kwargs"],
                )
            elif co_name == "assert_called_with":
                mock_instance = frame.f_locals["self"]
                mock_name = extract_mock_name(mock_instance)

                expected_args = frame.f_locals["args"]
                expected_kwargs = frame.f_locals["kwargs"]

                # TODO: diff against and colorize each call individually
                actual = (
                    pformat([c for c in mock_instance.call_args_list], width=1)
                    .replace("call", mock_name)
                    .replace("\n", PADDED_NEWLINE)
                )
                expected = str(call(*expected_args, **expected_kwargs)).replace(
                    "call", mock_name
                )
            elif co_name == "assert_has_calls":
                mock_instance = frame.f_locals["self"]
                mock_name = extract_mock_name(mock_instance)

                expected_calls = frame.f_locals["expected"]

                expected = (
                    pformat([c for c in expected_calls], width=1)
                    .replace("call", mock_name)
                    .replace("\n", PADDED_NEWLINE)
                )
                actual = (
                    pformat([c for c in mock_instance.call_args_list], width=1)
                    .replace("call", mock_name)
                    .replace("\n", PADDED_NEWLINE)
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
                    expected=utf8_replace("\n".join(exp)),
                    actual_label=Colour.stop + diff_intro_text("Actual:"),
                    actual=utf8_replace("\n".join(act)),
                )

            if hint is not None:
                hint_output = "\n\n    {hint_label} {hint}".format(
                    hint_label=Colour.stop + diff_intro_text("hint:"),
                    hint=hint,
                )
                formatted_output += hint_output

            tb2 = tb2.tb_next

        output = formatted_output or exc_instance

        return (exc_class, output, tb)
