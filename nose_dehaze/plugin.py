from pprint import pformat

from nose.plugins import Plugin


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
        while tb2 and formatted_output is None:
            frame = tb2.tb_frame
            co_name = frame.f_code.co_name
            if co_name == "assertEqual":
                expected = frame.f_locals["first"]
                actual = frame.f_locals["second"]
                padded_newline = "\n{}".format(" " * 10)

                if isinstance(expected, dict) and isinstance(actual, dict):
                    expected = pformat(expected, width=1).replace("\n", padded_newline)
                    actual = pformat(actual, width=1).replace("\n", padded_newline)

                formatted_output = (
                    "\n\nExpected: {expected}\n  Actual: {actual}"
                ).format(expected=expected, actual=actual)

            tb2 = tb2.tb_next

        output = formatted_output or exc_instance

        return (exc_class, output, tb)
