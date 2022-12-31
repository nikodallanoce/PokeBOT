from poke_env.environment import Pokemon, MoveCategory


def __type_advantage(attacker: Pokemon, defender: Pokemon) -> float:
    type_gain = max([defender.damage_multiplier(attacker_type)
                     for attacker_type in attacker.types if attacker_type is not None])
    return type_gain


def __move_type_advantage(bot_pokemon: Pokemon, opponent_pokemon: Pokemon, opponent_type_adv: float) -> float:
    # Consider the bot move-type match-up
    bot_type_gain = [opponent_pokemon.damage_multiplier(move_bot)
                     for move_bot in bot_pokemon.moves.values() if
                     move_bot.category is not MoveCategory.STATUS]
    bot_type_gain = max(bot_type_gain) if len(bot_type_gain) > 0 else 1

    # Consider the opponent move-type match-up
    opponent_type_gain = 0
    if len(opponent_pokemon.moves) > 0:
        for move_opp in opponent_pokemon.moves.values():
            if move_opp.category is not MoveCategory.STATUS:
                opponent_type_gain_iter = bot_pokemon.damage_multiplier(move_opp)
                if opponent_type_gain_iter > opponent_type_gain:
                    opponent_type_gain = opponent_type_gain_iter

    if opponent_type_gain < opponent_type_adv and len(opponent_pokemon.moves) < 4:
        return bot_type_gain - opponent_type_adv

    return bot_type_gain - opponent_type_gain


def matchup_on_types(bot_pokemon: Pokemon, opponent_pokemon: Pokemon) -> float:
    bot_type_adv = __type_advantage(bot_pokemon, opponent_pokemon)
    opponent_type_adv = __type_advantage(opponent_pokemon, bot_pokemon)
    poke_adv = bot_type_adv - opponent_type_adv
    move_adv = __move_type_advantage(bot_pokemon, opponent_pokemon, opponent_type_adv)
    return poke_adv + move_adv
