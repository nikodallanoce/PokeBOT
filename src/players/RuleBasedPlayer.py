from poke_env.player import Player
from poke_env.teambuilder import Teambuilder
from poke_env import PlayerConfiguration, ServerConfiguration
from src.engine.move_effects import compute_healing
from src.engine.battle_utilities import *
from src.engine.useful_data import *
from src.engine.stats import compute_stat
from src.engine.damage import compute_damage
from src.strategy.gimmick import should_dynamax
from src.strategy.matchup import matchup_on_types
from src.strategy.switch import should_switch, compute_best_switch
from src.utilities.utilities import matchups_to_string
from typing import Optional, Union


class RuleBasedPlayer(Player):

    def __init__(self,
                 player_configuration: Optional[PlayerConfiguration] = None,
                 *,
                 avatar: Optional[int] = None,
                 battle_format: str = "gen8randombattle",
                 log_level: Optional[int] = None,
                 max_concurrent_battles: int = 1,
                 save_replays: Union[bool, str] = False,
                 server_configuration: Optional[ServerConfiguration] = None,
                 # start_timer_on_battle_start: bool = False,
                 start_listening: bool = True,
                 ping_interval: Optional[float] = 20.0,
                 ping_timeout: Optional[float] = 20.0,
                 team: Optional[Union[str, Teambuilder]] = None,
                 ):
        super(RuleBasedPlayer, self).__init__(player_configuration=player_configuration, avatar=avatar,
                                              battle_format=battle_format, log_level=log_level,
                                              max_concurrent_battles=max_concurrent_battles, save_replays=save_replays,
                                              server_configuration=server_configuration,
                                              start_timer_on_battle_start=True,
                                              start_listening=start_listening,
                                              ping_interval=ping_interval, ping_timeout=ping_timeout, team=team)
        self.verbose = False
        self.best_stats_pokemon = 0
        self.previous_pokemon = None
        self.max_team_matchup = -8
        self.toxic_turn = 0

    @staticmethod
    def __compute_opponent_damage(bot_pokemon: Pokemon,
                                  opp_pokemon: Pokemon,
                                  weather: Weather,
                                  terrains: list[Field],
                                  bot_conditions: list[SideCondition]) -> int:
        # Retrieve all the non-status moves
        opp_damage = [opp_move for opp_move in opp_pokemon.moves.values()
                      if opp_move.category is not MoveCategory.STATUS]

        # Retrieve the type of all the non-status moves
        opp_moves_types = [opp_move.type for opp_move in opp_pokemon.moves.values()
                           if opp_move.category is not MoveCategory.STATUS]
        for opp_type in opp_pokemon.types:
            if len(opp_pokemon.moves) < 4 and opp_type and opp_type not in opp_moves_types:
                if opp_pokemon.base_stats["atk"] >= opp_pokemon.base_stats["spa"]:
                    opp_damage.append(DEFAULT_MOVES_IDS[opp_type][MoveCategory.PHYSICAL])
                else:
                    opp_damage.append(DEFAULT_MOVES_IDS[opp_type][MoveCategory.SPECIAL])

        opp_damage = max(compute_damage(opp_move, opp_pokemon, bot_pokemon, weather,
                                        terrains, bot_conditions)["ub"] for opp_move in opp_damage)
        return opp_damage

    def choose_move(self, battle):
        # Retrieve both active pokémon
        bot_pokemon: Pokemon = battle.active_pokemon
        opp_pokemon: Pokemon = battle.opponent_active_pokemon

        # Retrieve all the other pokémon in the team that are still alive
        bot_team = [pokemon for pokemon in battle.team.values()
                    if pokemon is not bot_pokemon and not pokemon.fainted]

        # Compute matchup scores for every remaining pokémon in the team
        bot_matchup = matchup_on_types(bot_pokemon, opp_pokemon)
        team_matchups = dict()
        for pokemon in bot_team:
            team_matchups.update({pokemon: matchup_on_types(pokemon, opp_pokemon)})

        # Compute the best base stats, this is useful for dynamax
        if battle.turn == 1:
            self.best_stats_pokemon = max([sum(pokemon.base_stats.values()) for pokemon in battle.team.values()])

        # If we switched pokémon, then update the bot's infos
        if not self.previous_pokemon:
            self.previous_pokemon = bot_pokemon
        elif bot_pokemon.species != self.previous_pokemon.species:
            self.previous_pokemon = bot_pokemon
            self.toxic_turn = 0
        else:
            bot_pokemon._first_turn = False
            if bot_pokemon.status is Status.TOX:
                self.toxic_turn += 1

        # Retrieve weather, terrains and side conditions
        battle_status = retrieve_battle_status(battle)
        weather: Weather = battle_status["weather"]
        terrains: list[Field] = battle_status["terrains"]
        bot_conditions: list[SideCondition] = battle_status["bot_conditions"]
        opp_conditions: list[SideCondition] = battle_status["opp_conditions"]

        # Compute the best pokémon the bot can switch to
        self.max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
        best_switch = compute_best_switch(team_matchups, opp_pokemon, weather, terrains, self.max_team_matchup)

        # Compute the hp of both pokémon
        bot_hp = bot_pokemon.current_hp
        opp_max_hp = compute_stat(opp_pokemon, "hp", weather, terrains)
        opp_hp = int(opp_max_hp * opp_pokemon.current_hp_fraction)

        if self.verbose and bot_pokemon.current_hp != 0:
            print("Turn {0}\n".format(battle.turn))
            print(bot_status_to_string(bot_pokemon, opp_pokemon, weather, terrains))
            print("Current matchup: {0}\nTeam matchups: {1}".format(bot_matchup, matchups_to_string(team_matchups)))

        # Choose one available move
        if battle.available_moves:
            # Moves will be saved inside a specific dict with their most useful infos
            bot_damage_moves = dict()
            bot_protecting_moves = list()
            bot_healing_moves = dict()
            bot_status_moves = list()
            bot_boost_moves = list()
            bot_retaliation_moves = list()
            bot_hazard_moves = list()
            available_moves_ids = [move.id for move in battle.available_moves]
            sleep_talk = "rest" in available_moves_ids and "sleeptalk" in available_moves_ids

            # Compute how much damage the opponent would deal
            opp_damage = self.__compute_opponent_damage(bot_pokemon, opp_pokemon, weather, terrains, bot_conditions)

            # Compute the probability of outpseeding the opponent pokémon
            outspeed_p, opp_spe_lb, opp_spe_ub = outspeed_prob(bot_pokemon, opp_pokemon, weather, terrains).values()
            if self.verbose:
                print("{0} outspeeds {1} (spe stat from {2} to {3}) with probability: {4}\n"
                      .format(bot_pokemon.species, opp_pokemon.species, opp_spe_lb, opp_spe_ub, outspeed_p))
                if battle.available_moves:
                    print("Available moves")

            move: Move
            for move in battle.available_moves:
                # Compute the move lower and upper bound of the move damage and its power and, possibly, new type
                damage_dict = compute_damage(move, bot_pokemon, opp_pokemon, weather, terrains, opp_conditions,
                                             is_bot=True)
                power, damage_lb, damage_ub, move_type = damage_dict.values()

                # Compute the accuracy of the move and save it
                accuracy = compute_move_accuracy(move, bot_pokemon, opp_pokemon, weather, terrains, False)

                # Update the moves dict
                bot_damage_moves.update({move: {"power": power, "damage_lb": damage_lb, "damage_ub": damage_ub,
                                         "accuracy": accuracy, "move_type": move_type, "priority": move.priority,
                                                "recoil": move.recoil}})

                # Put the status move in the right dict
                if power == 0:
                    if move.category is MoveCategory.STATUS:
                        if move.is_protect_move:
                            bot_protecting_moves.append(move)

                        if move.heal > 0:
                            heal, heal_percentage = compute_healing(bot_pokemon, opp_pokemon, move,
                                                                    weather, terrains, True)
                            bot_healing_moves.update({move: {"heal": heal, "heal_percentage": heal_percentage}})

                        if move.status and move.target != "self":
                            bot_status_moves.append(move)

                        if move.boosts and move.target == "self":
                            bot_boost_moves.append(move)

                        if move.id in ENTRY_HAZARDS:
                            bot_hazard_moves.append(move)

                    if move.id in ["counter", "mirrorcoat"]:
                        bot_retaliation_moves.append(move)

                if self.verbose:
                    print("Move: {0:16} | Type: {1:8} | Category: {2:8} "
                          "| Power: {3:3} | Damage: {4:3} - {5:3} | Accuracy: {6:4}"
                          .format(move.id, move_type.name, move.category.name, power, damage_lb, damage_ub, accuracy))

            # Keep those moves with the max damage
            max_damage = max([damage_accuracy["damage_lb"] for move, damage_accuracy in bot_damage_moves.items()
                              if move.id not in ["selfdestruct", "explosion"]])
            max_damage_moves = {move: bot_move["accuracy"] for move, bot_move in bot_damage_moves.items()
                                if bot_move["damage_lb"] == max_damage}

            # Choose the move with the best accuracy
            best_damage_move = max(max_damage_moves, key=lambda move_accuracy: max_damage_moves[move_accuracy])

            # Some moves work only when the pokémon has just been switched in
            if bot_pokemon.first_turn and Field.PSYCHIC_TERRAIN not in terrains:
                if "fakeout" in available_moves_ids and PokemonType.GHOST not in opp_pokemon.types \
                        and not opp_pokemon.is_dynamaxed:
                    if self.verbose:
                        print("\nChosen move: {0}\n{1}".format("fakeout", "-" * 110))

                    return self.create_order(Gen8Move("fakeout"))
                elif "firstimpression" in available_moves_ids:
                    if self.verbose:
                        print("\nChosen move: {0}\n{1}".format("firstimpression", "-" * 110))

                    return self.create_order(Gen8Move("firstimpression"))

            # Use the move "explosion" only if convenient
            if "explosion" in available_moves_ids and PokemonType.GHOST not in opp_pokemon.types and \
                    (bot_pokemon.item == "normalgem" or bot_pokemon.current_hp_fraction <= 0.5 and outspeed_p > 0.5):
                if self.verbose:
                    print("\nChosen move: {0}\n{1}".format("explosion", "-" * 110))

                return self.create_order(Gen8Move("explosion"))

            # If the current pokémon outspeeds the opponent's pokémon, then deal the final hit if possible
            if (outspeed_p >= 0.9 or opp_damage / bot_hp < 0.3) and max_damage > opp_hp:
                if self.verbose:
                    print("\nChosen move: {0}\n{1}".format(best_damage_move.id, "-" * 110))

                return self.create_order(best_damage_move)

            # If the current pokémon can defeat the opponent with a priority move, then use it
            priority_moves: dict[Move, int] = {move: infos["damage_lb"] for move, infos in bot_damage_moves.items()
                                               if infos["damage_lb"] > 0 and infos["priority"] > 0}
            for priority_move, damage in priority_moves.items():
                if damage > opp_hp:
                    if self.verbose:
                        print("\nChosen move: {0}\n{1}".format(priority_move.id, "-" * 110))

                    return self.create_order(priority_move)

            # Deal with pokémon that are defined as sleep-talkers
            if sleep_talk:
                if bot_matchup > -1:
                    if bot_pokemon.status is not Status.SLP:
                        if bot_pokemon.current_hp_fraction < 0.5:
                            if self.verbose:
                                print("\nChosen move: {0}\n{1}".format("rest", "-" * 110))

                            return self.create_order(Gen8Move("rest"))
                    else:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format("sleeptalk", "-" * 110))

                        return self.create_order(Gen8Move("sleeptalk"))
                elif battle.available_switches and bot_matchup < self.max_team_matchup:
                    self.previous_pokemon = bot_pokemon
                    if self.verbose:
                        print("\nSwitching to {0}\n{1}".format(best_switch.species, "-" * 110))

                    return self.create_order(best_switch)
                else:
                    if self.verbose:
                        print("\nChosen move: {0}\n{1}".format(best_damage_move.id, "-" * 110))

                    return self.create_order(best_damage_move)

            # Deal with stall pokémon
            if "toxic" in available_moves_ids and len(bot_healing_moves) > 0:
                if battle.available_switches and should_switch(bot_pokemon, bot_matchup, outspeed_p,
                                                               self.max_team_matchup, self.toxic_turn):
                    self.previous_pokemon = bot_pokemon
                    if self.verbose:
                        print("\nSwitching to {0}\n{1}".format(best_switch.species, "-" * 110))

                    return self.create_order(best_switch)

            # Switch out if there are available switches and the bot gains in terms of matchup by doing so
            if battle.available_switches and should_switch(bot_pokemon, bot_matchup, outspeed_p,
                                                           self.max_team_matchup, self.toxic_turn):
                self.previous_pokemon = bot_pokemon
                if self.verbose:
                    print("\nSwitching to {0}\n{1}".format(best_switch.species, "-" * 110))

                return self.create_order(best_switch)

            # Set up a trick room if possible, it means that our team will benefit from having such terrain
            if "trickroom" in available_moves_ids and Field.TRICK_ROOM not in terrains and bot_matchup >= 0:
                if self.verbose:
                    print("\nChosen move: {0}\n{1}".format("trickroom", "-" * 110))

                return self.create_order(Gen8Move("trickroom"))

            # If we don't know any move of the opponent, the matchup is slightly against, then use a protecting move
            if bot_protecting_moves and len(opp_pokemon.moves) == 0 and bot_matchup <= -0.5\
                    and bot_pokemon.protect_counter == 0:
                if self.verbose:
                    print("\nChosen move: {0}\n{1}".format(bot_protecting_moves[0].id, "-" * 110))

                return self.create_order(bot_protecting_moves[0])

            # We can use a move that puts an entry hazard if it isn't already present
            opponent_team_size = 6 - len([pokemon for pokemon in battle.opponent_team.values() if pokemon.fainted])
            for hazard_move in bot_hazard_moves:
                if opponent_team_size >= 3 and ENTRY_HAZARDS[hazard_move.id] not in opp_conditions and bot_matchup >= 1:
                    if self.verbose:
                        print("\nChosen move: {0}\n{1}".format(hazard_move.id, "-" * 110))

                    return self.create_order(hazard_move)

            # We can boost our stats if the matchup is in our favor
            if bot_boost_moves and bot_matchup >= 0 and sum(bot_pokemon.boosts.values()) == 0\
                    and bot_pokemon.current_hp_fraction >= 0.8 and (outspeed_p > 0.5 or opp_damage < bot_hp / 2):
                if self.verbose:
                    print("\nChosen move: {0}\n{1}".format(bot_boost_moves[0].id, "-" * 110))

                return self.create_order(bot_boost_moves[0])

            # We can use a status move is the matchup is in our favor
            if bot_status_moves and bot_matchup >= 0 and not opp_pokemon.status:
                for status_move in bot_status_moves:
                    if status_move.status is Status.BRN \
                            and opp_pokemon.base_stats["atk"] >= opp_pokemon.base_stats["spa"] \
                            and "guts" not in opp_pokemon.possible_abilities \
                            and PokemonType.FIRE not in opp_pokemon.types:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(status_move.id, "-" * 110))

                        return self.create_order(status_move)

                    if (status_move.status is Status.PSN or status_move.status is Status.TOX) \
                            and PokemonType.POISON not in opp_pokemon.types \
                            and PokemonType.STEEL not in opp_pokemon.types:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(status_move.id, "-" * 110))

                        return self.create_order(status_move)

                    if status_move.status is Status.PAR and outspeed_p < 0.5 \
                            and PokemonType.ELECTRIC not in opp_pokemon.types:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(status_move.id, "-" * 110))

                        return self.create_order(status_move)

                    if status_move.status is Status.SLP and outspeed_p < 0.5 and opp_pokemon.ability != "insomnia":
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(status_move.id, "-" * 110))

                        return self.create_order(status_move)

            # Restore hp if convenient
            if bot_healing_moves and bot_pokemon.current_hp_fraction <= 0.6:
                for healing_move, healing_dict in bot_healing_moves.items():
                    healing = healing_dict["heal"]
                    if opp_damage / (bot_hp + healing) < 1 and opp_damage < healing and outspeed_p > 0.6:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(healing_move.id, "-" * 110))

                        return self.create_order(next(iter(bot_healing_moves.keys())))

            # Use a retaliation move if not too risky
            if bot_retaliation_moves and bot_pokemon.current_hp_fraction > 0.4 and opp_damage * 2 > max_damage:
                for retaliation_move in bot_retaliation_moves:
                    if retaliation_move.category is MoveCategory.PHYSICAL \
                            and opp_pokemon.base_stats["atk"] > opp_pokemon.base_stats["spa"]:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(retaliation_move.id, "-" * 110))

                        return self.create_order(retaliation_move)

                    elif retaliation_move.category is MoveCategory.SPECIAL \
                            and opp_pokemon.base_stats["atk"] < opp_pokemon.base_stats["spa"]:
                        if self.verbose:
                            print("\nChosen move: {0}\n{1}".format(retaliation_move.id, "-" * 110))

                        return self.create_order(retaliation_move)

            # If we can't do enough damage, then switch out if possible
            if max_damage < 50 and battle.available_switches and max_damage < opp_hp \
                    and bot_matchup <= self.max_team_matchup:
                self.previous_pokemon = bot_pokemon
                if self.verbose:
                    print("\nSwitching to {0}\n{1}".format(best_switch.species, "-" * 110))

                return self.create_order(best_switch)

            # Use the dynamax if convenient
            dynamax = False
            if battle.can_dynamax:
                dynamax = should_dynamax(bot_pokemon, bot_team, bot_matchup,
                                         self.max_team_matchup, self.best_stats_pokemon)

            if self.verbose:
                if self.verbose:
                    print("\nChosen move: {0}\n{1}".format(best_damage_move.id, "-" * 110))

            return self.create_order(best_damage_move, dynamax=dynamax)
        elif battle.available_switches:
            # Update the matchup for each remaining pokèmon in the team
            for pokemon in bot_team:
                team_matchups.update({pokemon: matchup_on_types(pokemon, opp_pokemon)})

            # Choose the new active pokèmon
            self.max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
            best_switch = compute_best_switch(team_matchups, opp_pokemon, weather, terrains, self.max_team_matchup)
            self.previous_pokemon = bot_pokemon
            if self.verbose:
                print("Switching to {0}\n{1}".format(best_switch.species, "-" * 110))

            return self.create_order(best_switch)

        return self.choose_random_move(battle)
