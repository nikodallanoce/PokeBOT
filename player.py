from poke_env.environment import Move, Pokemon
from poke_env.player import Player
from battle_utilities import compute_damage


class BestDamagePlayer(Player):

    def choose_move(self, battle):
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon
        if battle.available_moves:
            weather_list = list(battle.weather.keys())
            field_list = list(battle.fields.keys())
            best_move: Move = max(battle.available_moves,
                                  key=lambda move: compute_damage(move, bot_pokemon, opponent_pokemon,
                                                                  weather_list, field_list, True))
            gimmick = False
            if battle.can_dynamax:
                gimmick = True

            return self.create_order(best_move, dynamax=gimmick)
        else:
            return self.choose_random_move(battle)


class MaxBasePowerPlayer(Player):

    def choose_move(self, battle):
        if battle.available_moves:
            best_move: Move = max(battle.available_moves, key=lambda move: move.base_power)
            gimmick = False
            return self.create_order(best_move, dynamax=gimmick)
        else:
            return self.choose_random_move(battle)
