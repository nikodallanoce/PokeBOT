from poke_env.environment import Pokemon, Battle, Move, MoveCategory, Weather, Field, Status, SideCondition
from poke_env.player import Player
from src.utilities.battle_utilities import compute_damage, outspeed_prob, compute_move_accuracy,\
    PROTECTING_MOVES, ENTRY_HAZARDS, ANTI_HAZARDS_MOVES


class RuleBasedPlayer(Player):

    verbose = False
    best_stats_pokemon = 0
    current_pokemon = None
    previous_pokemon = None
    toxic_turn = 0

    @staticmethod
    def __type_advantage(attacker: Pokemon, defender: Pokemon) -> float:
        type_gain = max([defender.damage_multiplier(attacker_type)
                         for attacker_type in attacker.types if attacker_type is not None])
        return type_gain

    @staticmethod
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

    @staticmethod
    def __move_with_max_damage(attacker: Pokemon, defender: Pokemon, weather: Weather, terrain: Field,
                               is_bot: bool) -> {Move: float}:
        max_damage = -1
        max_damage_move = None
        for move in attacker.moves.values():
            damage = compute_damage(move, attacker, defender, weather, terrain, is_bot, verbose=False)
            if damage > max_damage:
                max_damage = damage
                max_damage_move = move

        return {max_damage_move: max_damage}

    def __matchup_on_types(self, bot_pokemon: Pokemon, opponent_pokemon: Pokemon) -> float:
        # outspeed_p = outspeed_prob(bot_pokemon, opponent_pokemon)
        bot_type_adv = self.__type_advantage(bot_pokemon, opponent_pokemon)
        opponent_type_adv = self.__type_advantage(opponent_pokemon, bot_pokemon)
        poke_adv = bot_type_adv - opponent_type_adv
        move_adv = self.__move_type_advantage(bot_pokemon, opponent_pokemon, opponent_type_adv)
        # hp_adv = bot_pokemon.current_hp_fraction - opponent_pokemon.current_hp_fraction
        return poke_adv + move_adv  # + hp_adv

    def __should_switch(self, bot_pokemon: Pokemon, matchup: float, team_matchups: dict, outspeed_p: float) -> bool:
        max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8

        # Do not switch out the pokèmon if it is dynamaxed unless there is a very bad matchup
        if bot_pokemon.is_dynamaxed:
            if matchup <= -4:
                return True

            return False

        # The "toxic" status is one of the worst and gets by each turn, we need to attenuate its effects by switching
        if bot_pokemon.status is Status.TOX and matchup - self.toxic_turn < -2:
            return True

        # We can switch out if there are matchups better than the current one
        if max_team_matchup > matchup:
            # If one of the defense stat was decreased too much, switch out to not take heavy hits
            if bot_pokemon.boosts["def"] <= -2 or bot_pokemon.boosts["spd"] <= -2:
                return True

            # If the attack stat was decreased too much and the pokèmon is a physical attacker, switch out
            if bot_pokemon.base_stats["atk"] > bot_pokemon.boosts["spa"]:
                if matchup <= -1.5 or bot_pokemon.boosts["atk"] <= -2:
                    return True

            # If the special attack stat was decreased too much and the pokèmon is a special attacker, switch out
            if bot_pokemon.base_stats["spa"] > bot_pokemon.boosts["atk"]:
                if matchup <= -1.5 or bot_pokemon.boosts["spa"] <= -2:
                    return True

            # Switch out if the matchup is on the opponent's favor
            if matchup <= -2:
                return True
            elif matchup <= -1 and outspeed_p <= 0.5:
                return True

        return False

    def __should_dynamax(self, bot_pokemon: Pokemon, bot_team: list, matchup: float, team_matchups: dict) -> bool:
        max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8

        # If the pokèmon is the last one alive, use the dynamax
        if len(bot_team) == 0:
            return True

        # If the current pokèmon is the best one in terms of base stats and the matchup is favorable, then dynamax
        if sum(bot_pokemon.base_stats.values()) == self.best_stats_pokemon and matchup >= 1:
            return True

        if bot_pokemon.current_hp_fraction == 1:
            # If the current pokèmon is the last one at full hp, use dynamax on it
            if len([pokemon for pokemon in bot_team if pokemon.current_hp_fraction == 1]) == 0:
                return True
            else:
                # If the current matchup is the best one, and it's favourable, then dynamax
                if matchup >= max_team_matchup and matchup > 2:
                    return True

        if matchup >= max_team_matchup and matchup > 2:
            return True

        return False

    def choose_move(self, battle: Battle):
        # Retrieve both active pokèmon
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon

        # Retrieve the conditions on the opponent's side
        opponent_conditions = list(battle.opponent_side_conditions.keys())

        # Compute the best base stats, this is useful for dynamax
        if self.best_stats_pokemon == 0:
            self.best_stats_pokemon = max([sum(pokemon.base_stats.values()) for pokemon in battle.team.values()])

        # Deal with the effect of toxic
        self.current_pokemon = bot_pokemon
        if self.current_pokemon is not self.previous_pokemon:
            self.toxic_turn = 0
        elif bot_pokemon.status is Status.TOX:
            self.toxic_turn += 1

        # Retrieve weather and terrain
        weather = None if len(battle.weather.keys()) == 0 else next(iter(battle.weather.keys()))
        terrain = None if len(battle.fields.keys()) == 0 else next(iter(battle.fields.keys()))

        # Retrieve all the other pokèmon in the team that are still alive
        bot_team = [pokemon for pokemon in battle.team.values()
                    if pokemon is not bot_pokemon and not pokemon.fainted]

        # Compute matchup scores for every remaining pokèmon in the team
        bot_matchup = self.__matchup_on_types(bot_pokemon, opponent_pokemon)
        team_matchups = dict()
        for pokemon in bot_team:
            team_matchups.update({pokemon: self.__matchup_on_types(pokemon, opponent_pokemon)})

        # Switch out if there are available switches and the bot gains in terms of matchup by doing so
        outpseed_p = outspeed_prob(bot_pokemon, opponent_pokemon, weather, terrain)
        if battle.available_switches and self.__should_switch(bot_pokemon, bot_matchup, team_matchups, outpseed_p):
            switch = max(team_matchups, key=lambda pokemon: team_matchups[pokemon])
            self.previous_pokemon = bot_pokemon
            return self.create_order(switch)

        # Choose one available move
        if battle.available_moves:
            bot_moves = dict()
            for move in battle.available_moves:
                # If we don't know any move of the opponent, the matchup is slightly against, then use a protecting move
                if move.id in PROTECTING_MOVES and len(opponent_pokemon.moves) == 0 and bot_matchup <= -0.5:
                    return self.create_order(move)

                # We can use a move that puts an entry hazard if it isn't already present
                opponent_team_size = 6 - len([pokemon for pokemon in battle.opponent_team.values() if pokemon.fainted])
                if move.id in ENTRY_HAZARDS and opponent_team_size >= 4\
                        and ENTRY_HAZARDS[move.id] not in opponent_conditions and bot_matchup >= 0:
                    return self.create_order(move)

                # We can remove any entry hazard on our side if we have enough pokèmon remaining on our team
                if move.id in ANTI_HAZARDS_MOVES and len(bot_team) >= 1 and len(battle.side_conditions) > 0:
                    return self.create_order(move)

                # We can boost our stats if the matchup is in our favor
                stat_boost = None if not move.boosts else list(move.boosts.keys())
                if stat_boost and bot_matchup >= 1 and sum(bot_pokemon.boosts[stat] for stat in stat_boost) == 0:
                    return self.create_order(move)

                # In any other case, compute the damage and accuracy of the move
                damage = compute_damage(move, bot_pokemon, opponent_pokemon, weather, terrain, True, self.verbose)

                # Some side conditions on the opponent's side halve the move's damage
                if SideCondition.REFLECT in opponent_conditions and move.category is MoveCategory.PHYSICAL:
                    damage *= 0.5

                if SideCondition.AURORA_VEIL in opponent_conditions:
                    damage *= 0.5

                if SideCondition.LIGHT_SCREEN in opponent_conditions and move.category is MoveCategory.SPECIAL:
                    damage *= 0.5

                # Compute the accuracy of the move and save it
                accuracy = compute_move_accuracy(move, bot_pokemon, opponent_pokemon, weather, terrain, self.verbose)
                bot_moves.update({move: {"damage": damage, "accuracy": accuracy}})

            # Keep those moves with the max damage
            max_damage = max([damage_accuracy["damage"] for damage_accuracy in bot_moves.values()])
            max_damage_moves = {move: bot_move["accuracy"] for move, bot_move in bot_moves.items()
                                if bot_move["damage"] == max_damage}

            # Choose the move with the best accuracy
            best_move = max(max_damage_moves, key=lambda move_accuracy: max_damage_moves[move_accuracy])

            # Use the dynamax if convenient
            dynamax = False
            if battle.can_dynamax:
                dynamax = self.__should_dynamax(bot_pokemon, bot_team, bot_matchup, team_matchups)

            return self.create_order(best_move, dynamax=dynamax)
        elif battle.available_switches:
            # Update the matchup for each remaining pokèmon in the team
            for pokemon in bot_team:
                team_matchups.update({pokemon: self.__matchup_on_types(pokemon, opponent_pokemon)})

            # Choose the new active pokèmon
            switch = max(team_matchups, key=lambda pokemon: team_matchups[pokemon])
            self.previous_pokemon = bot_pokemon
            return self.create_order(switch)

        return self.choose_random_move(battle)
