import argparse
import asyncio
from poke_env.player import cross_evaluate
from src.players.baseline_player import MaxBasePowerPlayer, BestDamagePlayer
from src.players.rulebased_player import RuleBasedPlayer
from src.players.MiniMaxPlayer import MiniMaxPlayer
from tabulate import tabulate


def parse_arguments(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", type=int, default=1, help="the number of challenges that the bot will accept")
    parser.add_argument("--concurrency", type=int, default=10, help="max concurrent battles")
    parser.add_argument("--players", type=str, default="MBP,BD",
                        help="the bot's playstyle list: e.g: RB,MBP,MM. Recall MBP MaxBasePower, BD BestDamage, RB RuleBased, MM MiniMax")
    opt = parser.parse_known_args()[0] if known else parser.parse_args()
    return opt


async def run_bot_local():
    opt_parser = parse_arguments()
    n_matches = opt_parser.matches
    max_concurrency = opt_parser.concurrency
    players_string = opt_parser.players
    players_list = players_string.split(",")

    players = []
    for playstyle in players_list:
        if playstyle == "MBP":
            player = MaxBasePowerPlayer(max_concurrent_battles=max_concurrency)
        elif playstyle == "BD":
            player = BestDamagePlayer(max_concurrent_battles=max_concurrency)
        elif playstyle == "RB":
            player = RuleBasedPlayer(max_concurrent_battles=max_concurrency)
        elif playstyle == "MM":
            player = MiniMaxPlayer(max_concurrent_battles=max_concurrency)
        else:
            raise ValueError
        players.append(player)

    # Let them challenge each other
    cross_evaluation = await cross_evaluate(players, n_challenges=n_matches)

    # Display the results
    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation.items():
        table.append([p_1] + [str(cross_evaluation[p_1][p_2]) for p_2 in results])

    print(tabulate(table))


if __name__ == '__main__':
    run_bot = asyncio.new_event_loop()
    run_bot.run_until_complete(run_bot_local())