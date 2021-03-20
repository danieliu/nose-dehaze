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
