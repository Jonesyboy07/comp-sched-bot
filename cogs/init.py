from cogs.help import HelpCog
from cogs.joined import JoinedCog
from cogs.setup import SetupCog


def get_cogs(bot):
    return [
        HelpCog(bot),
        JoinedCog(bot),
        SetupCog(bot)
    ]