from pprint import pformat

from nose.plugins import Plugin

from nose_dehaze.diff import Colour, build_split_diff, deleted_text, diff_intro_text, utf8_replace


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

                if isinstance(expected, dict) and isinstance(actual, dict):
                    # pad newlines to align to first line with "expected"
                    padded_newline = "\n{}".format(" " * 10)
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
                if not isinstance(expr, bool):
                    booly = "falsy" if co_name == "assertTrue" else "truthy"
                    hint = "{expr} is {booly}".format(
                        expr=deleted_text(actual),
                        booly=deleted_text(booly),
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
