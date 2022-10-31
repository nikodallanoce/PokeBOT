from poke_env.environment import Move, Pokemon
from poke_env.player import Player
from battle_utilities import compute_damage, can_out_speed_pokemon


class BestDamagePlayer(Player):

    def choose_move(self, battle):
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon
        if battle.available_moves:
            print("Turn {0}".format(battle.turn))
            print("{0} ability: {1}, held item: {2}".format(bot_pokemon.species, bot_pokemon.ability, bot_pokemon.item))
            print("Types: {0}".format(bot_pokemon.types))
            print("{0} stats changes: {1}\n".format(bot_pokemon.species, bot_pokemon.boosts))
            weather_list = list(battle.weather.keys())  # Weather condition
            field_list = list(battle.fields.keys())  # Terrain condition
            best_move: Move = max(battle.available_moves,
                                  key=lambda move: compute_damage(move, bot_pokemon, opponent_pokemon, weather_list,
                                                                  field_list, True))
            print("Bot pokemon out speed probability {0}".format(can_out_speed_pokemon(bot_pokemon, opponent_pokemon)))
            print("Best move: {0}, type: {1}\n\n".format(best_move.id, best_move.type))
            gimmick = False
            if battle.can_dynamax:
                gimmick = True

            return self.create_order(best_move, dynamax=gimmick)
        else:
            if battle.available_switches:
                max_type_gain = -1
                max_type_gain_pokemon = None
                for pokemon in battle.available_switches:
                    switch_gain = max([opponent_pokemon.damage_multiplier(switch_type)
                                       for switch_type in opponent_pokemon.types if switch_type is not None])
                    if max_type_gain < switch_gain:
                        max_type_gain = switch_gain
                        max_type_gain_pokemon = pokemon

                    print("Pokemon: {0}, Type gain: {1}".format(pokemon, switch_gain))

                print("Switching to: {0}\n\n".format(max_type_gain_pokemon))
                return self.create_order(max_type_gain_pokemon)

            return self.choose_random_move(battle)


class MaxBasePowerPlayer(Player):

    def choose_move(self, battle):
        if battle.available_moves:
            best_move: Move = max(battle.available_moves, key=lambda move: move.base_power)
            gimmick = False
            return self.create_order(best_move, dynamax=gimmick)
        else:
            return self.choose_random_move(battle)
