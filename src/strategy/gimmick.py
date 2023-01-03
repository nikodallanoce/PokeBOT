from typing import List
from poke_env.environment import Pokemon


def should_dynamax(bot_pokemon: Pokemon,
                   bot_team: List[Pokemon],
                   matchup: float,
                   max_team_matchup: float = None,
                   best_stats_pokemon: int = None) -> bool:
    """
    Define a simple dynamax strategy considering both active pokémon and the current matchup.
    :param bot_pokemon: the bot's pokémon
    :param bot_team: the bot's not fainted pokémon excluding the active one
    :param matchup: the current pokémon matchup value
    :param max_team_matchup: the highest matchup value in the bot's team
    :param best_stats_pokemon: the sum of the best pokémon's stats
    :return: if the bot should use the dynamax gimmick or not
    """
    # If the pokèmon is the last one alive, use the dynamax
    if len(bot_team) == 0:
        return True

    # If the current pokèmon is the best one in terms of base stats and the matchup is favorable, then dynamax
    if sum(bot_pokemon.base_stats.values()) == best_stats_pokemon \
            and matchup >= 1 and bot_pokemon.current_hp_fraction >= 0.8:
        return True

    if bot_pokemon.current_hp_fraction == 1:
        # If the current pokèmon is the last one at full hp, use dynamax on it
        if len([pokemon for pokemon in bot_team if pokemon.current_hp_fraction == 1]) == 0:
            return True
        else:
            # If the current matchup is the best one, and it's favourable, then dynamax
            if matchup >= max_team_matchup and matchup > 2:
                return True

    if matchup >= max_team_matchup and matchup > 2 and bot_pokemon.current_hp_fraction == 1:
        return True

    return False
