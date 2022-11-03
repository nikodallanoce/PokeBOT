from poke_env.environment import Move, Pokemon
from poke_env.player import Player
from battle_utilities import compute_damage, outspeed_prob, compute_move_accuracy


class RuleBasedPlayer(Player):

    def choose_move(self, battle):
        return None


class BestDamagePlayer(Player):

    verbose = False
    can_switch = False

    def choose_move(self, battle):
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon
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
