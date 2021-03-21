from pprint import pformat

try:
    from unittest.mock import call
except ImportError:
    from mock import call

from nose.plugins import Plugin

from nose_dehaze.diff import (
    Colour,
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
        padded_newline = "\n{}".format(" " * 10)
        while tb2 and formatted_output is None:
            frame = tb2.tb_frame
            co_name = frame.f_code.co_name

            if co_name == "assertEqual":
                expected = frame.f_locals["first"]
                actual = frame.f_locals["second"]

                # add hint when types differ
                if type(expected) is not type(actual):
                    expected_line = "{padding}{label} {expected_type}".format(
                        padding=" " * 10,
                        label=header_text("Expected:"),
                        expected_type=deleted_text(type(expected)),
                    )
                    actual_line = "{padding}{label} {actual_type}".format(
                        padding=" " * 12,
                        label=header_text("Actual:"),
                        actual_type=inserted_text(type(actual)),
                    )
                    hint = "\n".join(
                        [
                            "expected and actual are different types",
                            expected_line,
                            actual_line,
                        ]
                    )

                if isinstance(expected, dict) and isinstance(actual, dict):
                    # pad newlines to align to newlines with first line "expected"
                    expected = pformat(expected, width=1).replace("\n", padded_newline)
                    actual = pformat(actual, width=1).replace("\n", padded_newline)
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
                message = (
                    "Mock {mock_name}".format(mock_name=mock_name)
                    + " called {num} times."
                )
                expected_call_count = {
                    "assert_called_once": 1,
                    "assert_not_called": 0,
                }[co_name]
                expected = message.format(num=expected_call_count)
                actual = message.format(num=mock_instance.call_count)
            elif co_name == "assert_called_once_with":
                mock_instance = frame.f_locals["self"]
                mock_name = header_text(extract_mock_name(mock_instance))

                expected_args = frame.f_locals["args"]
                expected_kwargs = frame.f_locals["kwargs"]

                actual = str(mock_instance.call_args).replace("call", mock_name)
                expected = str(call(*expected_args, **expected_kwargs)).replace(
                    "call", mock_name
                )
            elif co_name == "assert_called_with":
                mock_instance = frame.f_locals["self"]
                mock_name = header_text(extract_mock_name(mock_instance))

                expected_args = frame.f_locals["args"]
                expected_kwargs = frame.f_locals["kwargs"]

                # TODO: diff against and colorize each call individually
                actual = (
                    pformat([c for c in mock_instance.call_args_list], width=1)
                    .replace("call", mock_name)
                    .replace("\n", padded_newline)
                )
                expected = str(call(*expected_args, **expected_kwargs)).replace(
                    "call", mock_name
                )

            if expected and actual:
                exp, act = build_split_diff(expected, actual)
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
