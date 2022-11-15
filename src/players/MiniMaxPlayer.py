from poke_env.player import Player
from src.utilities.BattleStatus import BattleStatus
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import *
from src.utilities.stats_utilities import compute_stat


class MiniMaxPlayer(Player):

    def choose_move(self, battle):
        weather, terrains, bot_conditions, opp_conditions = retrieve_battle_status(battle).values()

        opp_max_hp = compute_stat(battle.opponent_active_pokemon, "hp", weather, terrains)
        root_battle_status = BattleStatus(NodePokemon(battle.active_pokemon, moves=battle.available_moves),
                                          NodePokemon(battle.opponent_active_pokemon, current_hp=opp_max_hp),
                                          battle.available_moves,
                                          battle.available_switches, weather, terrains,
                                          opp_conditions, None, Gen8Move('splash'))

        if battle.available_moves:
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

                    damage = compute_damage(mo, battle.active_pokemon, battle.opponent_active_pokemon, weather,
                                            terrains, opp_conditions, True)["ub"]
                    chs_mv = mo.id + " : " + mo.type.name + " dmg: " + str(damage)
                    if mo.id == best_move.id:
                        chs_mv += "♦"
                    # print(chs_mv)

                # print()

            return self.create_order(best_move)
        elif battle.available_switches:
            return self.create_order(battle.available_switches[0])

        return self.choose_random_move(battle)

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
                child_score, child_node = self.minimax(new_state, depth, False)
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
