from typing import Union, Awaitable

from poke_env.environment import Pokemon, Battle, Move, MoveCategory, Weather, Field, Status, SideCondition, \
    AbstractBattle, Gen8Move
from poke_env.player import Player, BattleOrder

from src.utilities.BattleStatus import BattleStatus
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import compute_damage
from src.utilities.stats_utilities import compute_stat, estimate_stat


class MiniMaxPlayer(Player):

    def choose_move(self, battle: Battle):
        weather = None if len(battle.weather.keys()) == 0 else next(iter(battle.weather.keys()))
        terrain = None if len(battle.fields.keys()) == 0 else next(iter(battle.fields.keys()))

        opp_poke_max_hp = estimate_stat(battle.opponent_active_pokemon, "hp")
        root_battle_status = BattleStatus(NodePokemon(battle.active_pokemon, moves=battle.available_moves),
                                          NodePokemon(battle.opponent_active_pokemon, current_hp=opp_poke_max_hp),
                                          battle.available_moves,
                                          battle.available_switches, weather, terrain, None, Gen8Move('splash'))

        if battle.active_pokemon.current_hp == 0:
            return self.create_order(battle.available_switches[0])
        ris = self.minimax(root_battle_status, 2, True)  # notato che faceva mosse per recuperare vita e basta
        node: BattleStatus = ris[1]
        best_move = self.choose_random_move(battle)  # il bot ha fatto U-turn e node diventava none
        if node is not None:
            best_move = node.move  # self.choose_random_move(battle)
            curr_node = node
            while curr_node.ancestor is not None:
                best_move = curr_node.move
                curr_node = curr_node.ancestor
            for mo in battle.available_moves:

                damage = compute_damage(mo, battle.active_pokemon, battle.opponent_active_pokemon, weather, terrain,
                                        True)
                chs_mv = mo.id + " : " + mo.type.name + " dmg: " + str(damage)
                if mo.id == best_move.id:
                    chs_mv += "♦"
                print(chs_mv)
            print()

        return self.create_order(best_move)

    def minimax(self, node: BattleStatus, depth: int, is_my_turn: bool) -> tuple[float, BattleStatus]:
        if depth == 0:
            score = node.compute_score()
            node.score = score
            return node.score, node
        if is_my_turn:
            score = float('-inf')
            ret_node = node
            for poss_act in node.act_poke_avail_actions():
                new_state = node.simulate_turn(poss_act, is_my_turn)
                child_score, child_node = self.minimax(new_state, depth - 1, False)
                if score < child_score:
                    ret_node = child_node
                score = max(score, child_score)
                node.score = score
            return score, ret_node
        else:
            score = float('inf')
            ret_node = node
            for poss_act in node.opp_poke_avail_actions():
                new_state = node.simulate_turn(poss_act, not is_my_turn)
                child_score, child_node = self.minimax(new_state, depth - 1, True)
                if score > child_score:
                    ret_node = child_node
                score = min(score, child_score)
                node.score = score
            return score, ret_node
