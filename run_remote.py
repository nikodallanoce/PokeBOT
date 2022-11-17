import argparse
import os
import asyncio
from poke_env import PlayerConfiguration, ShowdownServerConfiguration
from src.players.baseline_player import MaxBasePowerPlayer, BestDamagePlayer
from src.players.rulebased_player import RuleBasedPlayer
from src.players.MiniMaxPlayer import MiniMaxPlayer
from src.utilities.utilities import challenge_player
from src.utilities.ShowdownHeuristc import ShowdownHeuristic


def parse_arguments(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, default="", help="the bot's username")
    parser.add_argument("--password", type=str, default="", help="the bot's password")
    parser.add_argument("--matches", type=int, default=1, help="the number of challenges that the bot will accept")
    parser.add_argument("--player", type=str, default="RB",
                        help="the bot's playstyle, MBP MaxBasePower, BD BestDamage, RB RuleBased, MM MiniMax")
    parser.add_argument("--verbose", action="store_true", help="let the bot print its status at each turn")
    parser.add_argument("--save", action="store_true", help="save the battle results in a csv file")
    opt = parser.parse_known_args()[0] if known else parser.parse_args()
    return opt


async def run_bot_online():
    opt_parser = parse_arguments()
    bot_username = opt_parser.user
    bot_password = opt_parser.password
    n_matches = opt_parser.matches
    playstyle = opt_parser.player
    save_results = opt_parser.save

    if bot_username == "":
        bot_username = os.getenv("BotAIF_username")

    if bot_password == "":
        bot_password = os.getenv("BotAIF_password")

    player_config = PlayerConfiguration(bot_username, bot_password)
    if playstyle == "MBP":
        player = MaxBasePowerPlayer(player_configuration=player_config, server_configuration=ShowdownServerConfiguration)
    elif playstyle == "BD":
        player = BestDamagePlayer(player_configuration=player_config, server_configuration=ShowdownServerConfiguration)
    elif playstyle == "RB":
        player = RuleBasedPlayer(player_configuration=player_config, server_configuration=ShowdownServerConfiguration)
    elif playstyle == "MM":
        heuristic = ShowdownHeuristic()
        player = MiniMaxPlayer(player_configuration=player_config, server_configuration=ShowdownServerConfiguration, heuristic=heuristic, max_depth=2)
    else:
        raise ValueError

    player.verbose = opt_parser.verbose

    await challenge_player(player, None, n_matches, False, save_results)


if __name__ == '__main__':
    run_bot = asyncio.new_event_loop()
    run_bot.run_until_complete(run_bot_online())
