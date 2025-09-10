from cogs.help import HelpCog
from cogs.joined import JoinedCog
from cogs.setup import SetupCog
from cogs.team import TeamCog
from cogs.schedule import ScheduleCog


def get_cogs(bot):
    return [
        HelpCog(bot),
        JoinedCog(bot),
        SetupCog(bot),
        TeamCog(bot),
        ScheduleCog(bot)
    ]