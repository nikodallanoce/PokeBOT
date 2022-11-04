from poke_env.environment import Move, Pokemon, Battle, Weather, Field, MoveCategory
from poke_env.player import Player
from battle_utilities import compute_damage, outspeed_prob


class RuleBasedPlayer(Player):

    def choose_move(self, battle):
        return None


class BestDamagePlayer(Player):
    verbose = False
    can_switch = False

    def choose_move(self, battle):
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon
        self.matchup_on_types(battle)
        if battle.available_moves:
            if self.verbose:
                print("Turn {0}".format(battle.turn))
                print("{0} ability: {1}, item: {2}".format(bot_pokemon.species, bot_pokemon.ability, bot_pokemon.item))
                print("Types: {0}".format(bot_pokemon.types))
                print("Stats changes: {0}\n".format(bot_pokemon.boosts))

            weather = None if len(battle.weather.keys()) == 0 else next(iter(battle.weather.keys()))
            terrain = None if len(battle.fields.keys()) == 0 else next(iter(battle.fields.keys()))
            best_move: Move = max(battle.available_moves,
                                  key=lambda move: compute_damage(move, bot_pokemon, opponent_pokemon, weather, terrain,
                                                                  True, self.verbose))
            if self.verbose:
                print("Outspeed probability {0}".format(outspeed_prob(bot_pokemon, opponent_pokemon,
                                                                      weather, terrain, self.verbose)))
                print("Best move: {0}, type: {1}\n{2}\n".format(best_move.id, best_move.type, "-" * 100))

            gimmick = False
            if battle.can_dynamax:
                gimmick = True

            return self.create_order(best_move, dynamax=gimmick)
        else:
            if battle.available_switches and self.can_switch:
                max_type_gain = -5
                max_type_gain_pokemon = None
                for pokemon in battle.available_switches:
                    # Consider the bot type match-up
                    bot_type_gain = max([opponent_pokemon.damage_multiplier(switch_type)
                                         for switch_type in pokemon.types if switch_type is not None])

                    # Consider the opponent type match-up
                    opponent_type_gain = max([pokemon.damage_multiplier(opponent_type)
                                              for opponent_type in opponent_pokemon.types if opponent_type is not None])
                    type_gain = bot_type_gain - opponent_type_gain
                    if max_type_gain < type_gain:
                        max_type_gain = type_gain
                        max_type_gain_pokemon = pokemon

                    if self.verbose:
                        print("Pokemon: {0}, Type gain: {1}".format(pokemon, type_gain))

                if self.verbose:
                    print("Switching to: {0}\n{1}\n".format(max_type_gain_pokemon, "-" * 100))
                return self.create_order(max_type_gain_pokemon)

            return self.choose_random_move(battle)

    def matchup_on_types(self, battle):
        # outspeed_p = outspeed_prob(battle.active_pokemon, battle.opponent_active_pokemon)
        bot_type_adv = self.type_advantage(battle.active_pokemon, battle.opponent_active_pokemon)
        opponent_type_adv = self.type_advantage(battle.opponent_active_pokemon, battle.active_pokemon)
        poke_adv = bot_type_adv - opponent_type_adv
        move_adv = self.move_type_advantage(battle.active_pokemon, battle.opponent_active_pokemon, opponent_type_adv)
        return poke_adv + move_adv

    def move_type_advantage(self, bot_pokemon: Pokemon, opponent_pokemon: Pokemon, opponent_type_adv: float) -> float:

        # Consider the bot type match-up
        bot_type_gain = max([opponent_pokemon.damage_multiplier(move_bot)
                             for move_bot in bot_pokemon.moves.values() if
                             move_bot.category is not MoveCategory.STATUS])

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

    def type_advantage(self, attacker: Pokemon, defender: Pokemon) -> float:
        # Consider the bot type match-up
        type_gain = max([defender.damage_multiplier(attacker_type)
                         for attacker_type in attacker.types if attacker_type is not None])
        return type_gain

    def move_with_max_damage(self, attacker: Pokemon, defender: Pokemon, weather: Weather, terrain: Field,
                             is_bot: bool) -> {
        Move: float}:

        max_damage = -1
        max_damage_move = None
        for move in attacker.moves.values():
            damage = compute_damage(move, attacker, defender, weather, terrain, is_bot, verbose=False)
            if damage > max_damage:
                max_damage = damage
                max_damage_move = move

        return {max_damage_move: max_damage}


class MaxBasePowerPlayer(Player):

    def choose_move(self, battle):
        if battle.available_moves:
            best_move: Move = max(battle.available_moves, key=lambda move: move.base_power)
            gimmick = False
            if battle.can_dynamax:
                gimmick = True

            return self.create_order(best_move, dynamax=gimmick)
        else:
            return self.choose_random_move(battle)
