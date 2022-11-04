from poke_env import PlayerConfiguration, ShowdownServerConfiguration
import asyncio
from poke_env.player import cross_evaluate, baselines
from tabulate import tabulate
from player import BestDamagePlayer, MaxBasePowerPlayer
import sys
import argparse


def parse_arguments(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', action="store_true", help='let the bot play on a remote server')
    opt = parser.parse_known_args()[0] if known else parser.parse_args()
    return opt


async def run_bot_local():
    # Create the players
    first_player = BestDamagePlayer(player_configuration=PlayerConfiguration("BestDamage", None),
                                    max_concurrent_battles=10)
    first_player.can_switch = True
    second_player = BestDamagePlayer(player_configuration=PlayerConfiguration("BestDamageNoSwitch", None),
                                     max_concurrent_battles=10)
    baseline = baselines.SimpleHeuristicsPlayer(player_configuration=PlayerConfiguration("Baseline", None),
                                                max_concurrent_battles=10)
    players = [baseline, second_player]
    # Let them challenge each other
    cross_evaluation = await cross_evaluate(players, n_challenges=1)

    # Display the results
    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation.items():
        table.append([p_1] + [str(cross_evaluation[p_1][p_2]) for p_2 in results])

    print(tabulate(table))


async def run_bot_online():
    # Retrieve bot username and password
    bot_username = sys.argv[1]
    bot_password = sys.argv[2]

    # Set up the bot
    player_config = PlayerConfiguration(bot_username, bot_password)
    player = BestDamagePlayer(player_configuration=player_config, server_configuration=ShowdownServerConfiguration)
    player.verbose = True
    player.can_switch = True

    # Accept all challenges regardless the user
    await player.accept_challenges(None, 1)


if __name__ == '__main__':
    remote_server = True
    run_bot = asyncio.new_event_loop()
    if remote_server:
        run_bot.run_until_complete(run_bot_online())
    else:
        run_bot.run_until_complete(run_bot_local())
