from poke_env import PlayerConfiguration
from src.players.baseline_player import MaxBasePowerPlayer, BestDamagePlayer
from src.players.rulebased_player import RuleBasedPlayer
from src.players.MiniMaxPlayer import MiniMaxPlayer
from src.utilities.utilities import evaluate_players_locally
from src.utilities.ShowdownHeuristc import ShowdownHeuristic
import argparse
import asyncio


def parse_arguments(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", type=int, default=100, help="the number of challenges that the bot will accept")
    parser.add_argument("--concurrency", type=int, default=10, help="max concurrent battles")
    parser.add_argument("--players", nargs="+", type=str, default=["BD", "RB"],
                        help="the playstyles list, MBP MaxBasePower, BD BestDamage, RB RuleBased, MM MiniMax")
    parser.add_argument("--save", action="store_true", help="save the results into a csv file")
    opt = parser.parse_known_args()[0] if known else parser.parse_args()
    return opt


async def run_bot_local():
    opt_parser = parse_arguments()
    n_matches = opt_parser.matches
    max_concurrency = opt_parser.concurrency
    playstyles = opt_parser.players

    mbp_players = 0
    bd_players = 0
    rb_players = 0
    mm_players = 0
    players = list()

    for playstyle in playstyles:
        if playstyle == "MBP":
            player_username = "MaxBasePower{0}".format(mbp_players)
            player = MaxBasePowerPlayer(player_configuration=PlayerConfiguration(player_username, None),
                                        max_concurrent_battles=max_concurrency)
            mbp_players += 1
        elif playstyle == "BD":
            player_username = "BestDamage{0}".format(bd_players)
            player = BestDamagePlayer(player_configuration=PlayerConfiguration(player_username, None),
                                      max_concurrent_battles=max_concurrency)
            player.can_switch = True
            bd_players += 1
        elif playstyle == "RB":
            player_username = "RuleBased{0}".format(rb_players)
            player = RuleBasedPlayer(player_configuration=PlayerConfiguration(player_username, None),
                                     max_concurrent_battles=max_concurrency)
            rb_players += 1
        elif playstyle == "MM":
            player_username = "MiniMax{0}".format(mm_players)
            heuristic = ShowdownHeuristic()
            player = MiniMaxPlayer(player_configuration=PlayerConfiguration(player_username, None),
                                   max_concurrent_battles=max_concurrency, heuristic=heuristic, max_depth=2)
            mm_players += 1
        else:
            raise ValueError

        players.append(player)

    await evaluate_players_locally(players, n_matches, opt_parser.save)


if __name__ == '__main__':
    run_bot = asyncio.new_event_loop()
    run_bot.run_until_complete(run_bot_local())
