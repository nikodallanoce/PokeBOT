from poke_env.environment import Move, Pokemon
from poke_env.player import Player
# from poke_env.player import ForfeitBattleOrder


class PlayerAIF(Player):

    def choose_move(self, battle):
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon
        # forfeit = ForfeitBattleOrder()
        # print(opponent_pokemon.types)
        if battle.available_moves:
            best_move: Move = max(battle.available_moves, key=lambda move: move.base_power)
            gimmick = False
            if battle.can_dynamax:
                gimmick = True
            
            return self.create_order(best_move, dynamax=gimmick)
        else:
            return self.choose_random_move(battle)
