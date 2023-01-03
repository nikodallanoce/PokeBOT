from poke_env.player import Player, cross_evaluate
from poke_env.environment import Pokemon, PokemonType
from typing import Union, List, Tuple, Dict
from tabulate import tabulate
import os
import pandas as pd


async def send_player_on_ladder(player: Player,
                                n_matches: int = 10,
                                verbose: bool = False,
                                save_results: bool = False) -> None:
    """
    Let the bot play on online classified matches
    :param player: the player we want to send on the ladder
    :param n_matches: the number of matches the bot will play
    :param verbose: print useful infos
    :param save_results: Save the results in a csv file
    """
    for i in range(n_matches):
        # Save useful data
        await player.ladder(1)
        ratings = [battle.rating for battle in player.battles.values()]
        results = [battle.won for battle in player.battles.values()]
        turns = [battle.turn for battle in player.battles.values()]

        player_type = str(type(player)).split(".")[-1][:-2]
        if verbose:
            wins = sum(result for result in results if result)
            win_ratio = wins / len(results)
            print("Match: {0}, Won: {1}, Win ratio: {2}, Rating: {3}".format(i, results[-1], win_ratio, ratings[-1]))

        if save_results:
            csv_name = "bot_data/ladder_{0}_{1}.csv".format(player_type, player.username)
            battles_dict = {"Rating": [ratings[-1]], "Turns": [turns[-1]], "Won": [results[-1]]}
            if os.path.isfile(csv_name):
                df_ratings = pd.read_csv(csv_name, index_col=0)
                df_ratings = pd.concat([df_ratings, pd.DataFrame(battles_dict)], ignore_index=True)
            else:
                df_ratings = pd.DataFrame(battles_dict)

            df_ratings.to_csv(csv_name)


async def challenge_player(player: Player,
                           opponent: str = None,
                           n_matches: int = 10,
                           verbose: bool = False,
                           save_results: bool = False) -> None:
    """
    Let the bot challenge a player on the remote server
    :param player: the chosen player
    :param opponent: the opponent's name
    :param n_matches: the number of matches the bot will play
    :param verbose: print useful infos
    :param save_results: Save the results in a csv file
    """
    await player.accept_challenges(opponent, n_matches)

    # Save useful data
    results = [battle.won for battle in player.battles.values()]
    turns = [battle.turn for battle in player.battles.values()]

    player_type = str(type(player)).split(".")[-1][:-2]
    if verbose:
        wins = sum(result for result in results if result)
        win_ratio = wins / len(results)
        print("Player: {0}, username: {1}".format(player_type, player.username))
        print("Matches played: {0}, Win ratio: {1}".format(n_matches, win_ratio))

    if save_results:
        battles_dict = {"Turns": turns, "Won": results}
        df_ratings = pd.DataFrame(battles_dict)
        df_ratings.to_csv("bot_data/{0}_{1}.csv".format(player_type, player.username))


async def evaluate_players_locally(players: List[Player], n_matches: int = 100, save_results: bool = False) -> None:
    """
    Test the various bot's playstyles on a local server
    :param players: list of players we want to test
    :param n_matches: the number of matches the players will play against each other
    :param save_results: Save the results in a csv file
    """
    # Let the players challenge each other
    cross_evaluation = await cross_evaluate(players, n_challenges=n_matches)

    # Show the results
    players_table = [["-"] + [player.username for player in players]]
    for p_1, results in cross_evaluation.items():
        players_table.append([p_1] + [str(cross_evaluation[p_1][p_2]) for p_2 in results])

    print(tabulate(players_table))
    if save_results:
        players_table[0][0] = "Player"
        df_results = pd.DataFrame(players_table[1:], columns=players_table[0])
        df_results.to_csv("bot_data/local_results_{0}_matches.csv".format(n_matches))


def types_to_string(pokemon_types: Union[Pokemon, Tuple[PokemonType, PokemonType | None]]) -> str:
    """
    Translate a Pokémon's types into a string
    :param pokemon_types: Pokémon under consideration or a tuple of types
    :return: String of a Pokémon types
    """
    if issubclass(type(pokemon_types), Pokemon):
        types = pokemon_types.types
    else:
        types = pokemon_types

    types = [pokemon_type.name for pokemon_type in types if pokemon_type is not None]
    types = types[0] if len(types) == 1 else "{0}/{1}".format(types[0], types[1])
    return types


def matchups_to_string(matchups: Dict[Pokemon, float]) -> str:
    """
    Translate a matchup dict into a string
    :param matchups: dict of matchup values
    :return: String of matchup values.
    """
    team = ""
    for i, team_matchup in enumerate(matchups.items()):
        team_pokemon, pokemon_matchup = team_matchup
        team += "{0}: {1}".format(team_pokemon.species, pokemon_matchup)
        if i != len(matchups) - 1:
            team += ", "

    return team
