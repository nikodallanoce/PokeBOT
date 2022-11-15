from poke_env.player import Player, cross_evaluate
from poke_env.environment import Pokemon, PokemonType
from typing import Union
from tabulate import tabulate
import pandas as pd


async def send_player_on_ladder(player: Player,
                                n_matches: int = 10,
                                verbose: bool = False,
                                save_results: bool = False) -> None:
    await player.ladder(n_matches)

    # Save useful data
    ratings = [battle.rating for battle in player.battles.values()]
    results = [battle.won for battle in player.battles.values()]
    turns = [battle.turn for battle in player.battles.values()]

    player_type = str(type(player)).split(".")[-1][:-2]
    if verbose:
        wins = sum(result for result in results if result)
        win_ratio = wins / len(results)
        print("Player: {0}, username: {1}".format(player_type, player.username))
        print("Matches played: {0}, Win ratio: {1}, Rating: {2}".format(n_matches, win_ratio, ratings[-1]))

    if save_results:
        battles_dict = {"Rating": ratings, "Turns": turns, "Won": results}
        df_ratings = pd.DataFrame(battles_dict)
        df_ratings.to_csv("bot_data/ladder_{0}_{1}.csv".format(player_type, player.username))


async def challenge_player(player: Player,
                           opponent: str = None,
                           n_matches: int = 10,
                           verbose: bool = False,
                           save_results: bool = False) -> None:
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


async def evaluate_players_locally(players: list[Player], n_matches: int = 100, save_results: bool = False) -> None:
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


def types_to_string(pokemon_types: Union[Pokemon, tuple[PokemonType, PokemonType | None]]) -> str:
    if issubclass(type(pokemon_types), Pokemon):
        types = pokemon_types.types
    else:
        types = pokemon_types

    types = [pokemon_type.name for pokemon_type in types if pokemon_type is not None]
    types = types[0] if len(types) == 1 else "{0}/{1}".format(types[0], types[1])
    return types


def matchups_to_string(matchups: dict[Pokemon, float]) -> str:
    team = ""
    for i, team_matchup in enumerate(matchups.items()):
        team_pokemon, pokemon_matchup = team_matchup
        team += "{0}: {1}".format(team_pokemon.species, pokemon_matchup)
        if i != len(matchups) - 1:
            team += ", "

    return team
