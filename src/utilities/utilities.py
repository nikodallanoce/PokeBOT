from poke_env.player import Player
from poke_env.environment import Pokemon, PokemonType
from typing import Union
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
