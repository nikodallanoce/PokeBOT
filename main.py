from poke_env import PlayerConfiguration, ShowdownServerConfiguration
import asyncio
from poke_env.player import RandomPlayer, cross_evaluate, baselines
from tabulate import tabulate
from player import BestDamagePlayer, MaxBasePowerPlayer
import os
import argparse


def parse_arguments(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', action="store_true", help='let the bot play on a remote server')
    opt = parser.parse_known_args()[0] if known else parser.parse_args()
    return opt


async def run_bot_local():
    # Create the players
    players = [BestDamagePlayer(max_concurrent_battles=10), MaxBasePowerPlayer(max_concurrent_battles=10),
               baselines.SimpleHeuristicsPlayer(max_concurrent_battles=10), RandomPlayer(max_concurrent_battles=10)]

    # Let them challenge each other
    cross_evaluation = await cross_evaluate(players, n_challenges=100)
    print("All battles ended, wait for the results")

    # Display the results
    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation.items():
        table.append([p_1] + [str(cross_evaluation[p_1][p_2]) for p_2 in results])

    print(tabulate(table))


async def run_bot_online():
    # Retrieve bot username and password
    bot_username = os.getenv('BotAIF_username')
    bot_password = os.environ.get('BotAIF_password')

    # Set up the bot
    player_config = PlayerConfiguration(bot_username, bot_password)
    player = BestDamagePlayer(player_configuration=player_config, server_configuration=ShowdownServerConfiguration)

    # Accept all challenges regardless the user
    await player.accept_challenges(None, 1)


if __name__ == '__main__':
    opt_parser = parse_arguments()
    remote_server = opt_parser.remote
    if remote_server:
        asyncio.get_event_loop().run_until_complete(run_bot_online())
    else:
        asyncio.get_event_loop().run_until_complete(run_bot_local())
