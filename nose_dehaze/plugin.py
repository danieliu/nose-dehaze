from nose.plugins import Plugin

from nose_dehaze.constants import ASSERT_METHODS
from nose_dehaze.diff import dehaze


class Dehaze(Plugin):
    enabled = False
    enableOpt = "dehaze"
    env_opt = "NOSE_DEHAZE"
    name = "nose-dehaze"
    score = 1020

    def options(self, parser, env):
        enabled = env.get(self.env_opt, "false").lower() in {"true", "1"}
        parser.add_option(
            "--dehaze",
            action="store_true",
            default=enabled,
            dest=self.enableOpt,
            help="Prettify and colorize test results output. Environment variable: {}".format(  # noqa: E501
                self.env_opt
            ),
        )

    def formatFailure(self, test, err):
        exc_class, exc_instance, trace = err

        _tb = trace
        output = None
        while trace and output is None:
            assert_method = trace.tb_frame.f_code.co_name
            if assert_method in ASSERT_METHODS:
                output = dehaze(assert_method, trace.tb_frame.f_locals)

            trace = trace.tb_next

        return (exc_class, output if output else exc_instance, _tb)
