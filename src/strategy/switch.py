from poke_env.environment import Pokemon, Weather, Field, Status
from src.engine.battle_utilities import outspeed_prob
from typing import Union
import numpy as np


def should_switch(bot_pokemon: Pokemon,
                  matchup: float,
                  outspeed_p: float,
                  max_team_matchup: int,
                  toxic_turn: int = 0) -> bool:
    """
    Defines a switch strategy for the bot taking into account the matchup of its active pokémon and all the other not
    fainted pokémon in the team, the outspeed probability and the number of toxic turns that have passed.
    :param bot_pokemon: the bot's pokémon
    :param matchup: the bot's pokémon matchup
    :param outspeed_p: the outspeed probability of the bot's pokémon against the opponent's.
    :param max_team_matchup: the highest matchup value in the bot's team
    :param toxic_turn: the number of turns that the current pokémon has passed with the toxic status
    :return: Boolean that the bot if it should switch out or not.
    """
    # Do not switch out the pokèmon if it is dynamaxed unless there is a very bad matchup
    if bot_pokemon.is_dynamaxed:
        if matchup <= -4:
            return True

        return False

    # We can switch out if there are matchups better than the current one
    if max_team_matchup > matchup:
        # The "toxic" status is one of the worst status, we need to attenuate its effects by switching
        if bot_pokemon.status is Status.TOX and matchup - toxic_turn <= -2:
            return True

        # If one of the defense stat was decreased too much, switch out to not take heavy hits
        if bot_pokemon.boosts["def"] <= -2 or bot_pokemon.boosts["spd"] <= -2:
            return True

        # If the attack stat was decreased too much and the pokèmon is a physical attacker, switch out
        if bot_pokemon.base_stats["atk"] > bot_pokemon.boosts["spa"]:
            if matchup <= -1.5 or bot_pokemon.boosts["atk"] <= -2:
                return True

        # If the special attack stat was decreased too much and the pokèmon is a special attacker, switch out
        if bot_pokemon.base_stats["spa"] > bot_pokemon.boosts["atk"]:
            if matchup <= -1.5 or bot_pokemon.boosts["spa"] <= -2:
                return True

        # Switch out if the matchup is on the opponent's favor
        if matchup <= -1.5:
            return True
        elif matchup <= -1 and outspeed_p <= 0.5:
            return True

    return False


def compute_best_switch(team_matchups: dict[Pokemon, float],
                        opp_pokemon: Pokemon,
                        weather: Weather,
                        terrains: list[Field],
                        max_team_matchup: int) -> Union[Pokemon | None]:
    """
    Computes the best not fainted pokémon to switch in.
    :param team_matchups: all the matchup values for the not fainted pokémon in the bot's team
    :param opp_pokemon: the opponent's pokémon
    :param weather: the current weather
    :param terrains: the current active fields
    :param max_team_matchup: the highest matchup value in the bot's team
    :return: The best pokémon to switch in.
    """
    if team_matchups:
        # Retrieve all the pokémon in the team with the best matchup
        best_switches = {pokemon: pokemon.stats for pokemon, matchup in team_matchups.items()
                         if matchup == max_team_matchup}

        # Keep those pokémon that can outspeed the opponent's pokémon
        outspeed_opp = [pokemon for pokemon, _ in best_switches.items()
                        if outspeed_prob(pokemon, opp_pokemon, weather, terrains)["outspeed_p"] > 0.6]
        if outspeed_opp:
            # If there are pokémon that can outspeed the opponent, then choose one randomly
            switch_choice = np.random.randint(0, len(outspeed_opp))
            return outspeed_opp[switch_choice]
        else:
            # Choose a pokémon randomly from the team
            best_switches = list(best_switches.keys())
            switch_choice = np.random.randint(0, len(best_switches))
            return best_switches[switch_choice]
    else:
        return None
