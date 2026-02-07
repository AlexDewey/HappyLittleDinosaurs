import random
from typing import List, Optional
import json
import pygame

class Player:
    def __init__(self, name: str):
        self.name = name
        self.score = 0
        self.cards = []
        self.disasters = []
        self.played_card = None
        self.eliminated = False
        self.won_round = False

    def __repr__(self):
        return f"{self.name} (Score: {self.score}, Disasters: {len(self.disasters)})"

class PlayerCard:
    def __init__(self, card_type: str, points: int, effect: str, title: str):
        self.type = card_type  # "point" or "instant"
        self.points = points
        self.title = title
        self.effect = effect

    def __repr__(self):
        return f"{self.type} ({self.points}pts)"

class DisasterCard:
    def __init__(self, disaster_type: str):
        self.type = disaster_type
        self.title = f"{disaster_type} Disaster"

    def __repr__(self):
        return self.title

class Deck:
    def __init__(self):
        self.draw_deck = []
        self.discard_pile = []
        self.draw_disaster = []
        self.discard_disaster_pile = []

    def draw_card(self) -> PlayerCard:
        if not self.draw_deck:
            self.draw_deck = self.discard_pile[:]
            self.discard_pile = []
            random.shuffle(self.draw_deck)
            print("Shuffling discard pile back into deck...")

            with open('player_cards.json', 'r') as file:
                card_json = json.load(file)  # Converts JSON to Python dict/list

            # For each card in the draw deck, ensure it's point value is the same as in JSON
            for card in self.draw_deck:
                for card_description in card_json:
                    if card.title == card_description["title"]:
                        card.points = card_description["points"]
                        break
                    
        return self.draw_deck.pop()

    def draw_disaster_card(self) -> DisasterCard:
        if not self.draw_disaster:
            self.draw_disaster = self.discard_disaster_pile[:]
            self.discard_disaster_pile = []
            random.shuffle(self.draw_disaster)
            print("Shuffling disaster discard pile back into deck...")
        return self.draw_disaster.pop()

def create_decks() -> Deck:
    deck = Deck()

    with open('player_cards.json', 'r') as file:
        card_json = json.load(file)  # Converts JSON to Python dict/list

    # Adding cards
    for card_description in card_json:
        for _ in range(0, card_description["amount"]):
            deck.draw_deck.append(PlayerCard(title=card_description["title"],
                                  card_type="point",
                                  points=card_description["points"],
                                  effect=card_description["effect"]))
    
    with open('player_instants.json', 'r') as file:
        instant_json = json.load(file)  # Converts JSON to Python dict/list
    
    for card_description in instant_json:
        for _ in range(0, card_description["amount"]):
            deck.draw_deck.append(PlayerCard(title=card_description["title"],
                                  card_type="instant",
                                  points=None,
                                  effect=card_description["effect"]))

    random.shuffle(deck.draw_deck)
    
    # Create disaster cards
    disaster_types = ["Meteor", "Natural", "Predator", "Emotional"]
    for _ in range(20):
        deck.draw_disaster.append(DisasterCard(random.choice(disaster_types)))
    
    random.shuffle(deck.draw_disaster)
    
    return deck

def refill_player_hands(player_list: List[Player], deck: Deck):
    for player in player_list:
        if player.eliminated:
            continue
            
        while len(player.cards) < 5:
            card = deck.draw_card()
            if card:
                player.cards.append(card)
            else:
                break
        
        # Check if hand is all instants
        while all(card.type == "instant" for card in player.cards) and len(player.cards) > 0:
            print(f"{player.name} has only instant cards! Discarding and redrawing...")
            deck.discard_pile.extend(player.cards)
            player.cards = []
            for _ in range(5):
                card = deck.draw_card()
                if card:
                    player.cards.append(card)

def select_number_of_players() -> int:
    while True:
        try:
            num = int(input("How many players? (2-4): "))
            if 2 <= num <= 4:
                return num
            print("Please enter a number between 2 and 4.")
        except ValueError:
            print("Please enter a valid number.")

def enter_player_names(num_players: int) -> List[Player]:
    players = []
    for i in range(num_players):
        name = input(f"Enter name for Player {i+1}: ").strip()
        if not name:
            name = f"Player {i+1}"
        players.append(Player(name))
    return players

def play_disaster(deck: Deck) -> Optional[DisasterCard]:
    disaster = deck.draw_disaster_card()
    if disaster:
        print(f"\n🦖 DISASTER: {disaster.title}!")
    return disaster

def show_hand(player: Player):
    print(f"\n{player.name}'s hand:")
    for i, card in enumerate(player.cards):
        if card.type == "instant":
            print(f"    {i+1}. {card.title} (Instant): {card.effect}")
        elif card.effect == "None":
            print(f"    {i+1}. {card.title}, ({card.points})")
        else:
            print(f"    {i+1}. {card.title}, ({card.points}): {card.effect}")

def play_point_cards(player_list: List[Player]):
    print("\n--- PLAYING POINT CARDS ---")
    for player in player_list:
        if player.eliminated:
            continue
            
        show_hand(player)
        point_cards = [i for i, c in enumerate(player.cards) if c.type == "point"]
        
        if not point_cards:
            print(f"{player.name} has no point cards to play!")
            continue
        
        while True:
            try:
                choice = int(input(f"Choose a point card to play (1-{len(player.cards)}): ")) - 1
                if 0 <= choice < len(player.cards) and player.cards[choice].type == "point":
                    player.played_card = player.cards.pop(choice)
                    print(f"{player.name} played {player.played_card}")
                    break
                else:
                    print("Please choose a valid point card.")
            except ValueError:
                print("Please enter a valid number.")

def reveal_cards(player_list: List[Player]):
    print("\n--- REVEALED CARDS ---")
    for player in player_list:
        if not player.eliminated and player.played_card:
            if player.played_card.effect == "None":
                print(f"{player.name}: {player.played_card.title}, ({player.played_card.points})")
            else:
                print(f"{player.name}: {player.played_card.title}, ({player.played_card.points}): {player.played_card.effect}")

def disaster_sudden_death_handling(player_list: List[Player]) -> Optional[Player]:
    active_players = [p for p in player_list if not p.eliminated and p.played_card]
    if not active_players:
        return None
    
    min_points = min(p.played_card.points for p in active_players)
    losers = [p for p in active_players if p.played_card.points == min_points]
    
    if len(losers) == 1:
        print(f"\n{losers[0].name} has the lowest card and gets the disaster!")
        return losers[0]
    
    print(f"\nTie for lowest! Tiebreaker between: {', '.join(p.name for p in losers)}")
    print("Sudden death tiebreaker...")
    
    while len(losers) > 1:
        # Check if all tied players have no point cards
        players_with_points = [p for p in losers if any(c.type == "point" for c in p.cards)]
        
        if not players_with_points:
            print("No players have point cards left! No one gets the disaster.")
            return None
        
        # Remove players who have no point cards from tiebreaker
        for loser in losers[:]:
            if not any(c.type == "point" for c in loser.cards):
                print(f"{loser.name} has no point cards and is eliminated from tiebreaker!")
                losers.remove(loser)
        
        if len(losers) == 1:
            break
        
        # Each remaining player plays a point card
        for loser in losers:
            show_hand(loser)
            
            while True:
                try:
                    choice = int(input(f"{loser.name}, choose a point card to play (1-{len(loser.cards)}): ")) - 1
                    if 0 <= choice < len(loser.cards) and loser.cards[choice].type == "point":
                        loser.played_card = loser.cards.pop(choice)
                        print(f"{loser.name} played {loser.played_card}")
                        break
                    else:
                        print("Please choose a valid point card.")
                except ValueError:
                    print("Please enter a valid number.")
        
        # Find new lowest
        min_points = min(p.played_card.points for p in losers)
        losers = [p for p in losers if p.played_card.points == min_points]
    
    if losers:
        print(f"\n{losers[0].name} loses the tiebreaker and gets the disaster!")
        return losers[0]
    return None

def reward_disaster(player: Optional[Player], disaster: DisasterCard, deck: Deck):
    if player is None:
        print("No player received the disaster card.")
        return
    if player and disaster:

        # Check to see if player has any disaster immunity card
        for i, card in enumerate(player.cards):
            if card.title == "Disaster Insurance":
                print(f"{player.name} has a Disaster Insurance card! Using it to avoid disaster.")
                used_card = player.cards.pop(i)
                deck.discard_pile.append(used_card)
                deck.discard_disaster_pile.append(disaster)
                return

        player.disasters.append(disaster)
        print(f"{player.name} received a disaster card.")
    elif disaster:
        deck.discard_disaster_pile.append(disaster)

def reward_points(player_list: List[Player]):
    print("\n--- REWARDING POINTS ---")
    # Reward players who have won_round flag True
    # Player with the highest score gets .win_round=True

    # Find the player with the highest scoring card
    max_points = max(p.played_card.points for p in player_list if not p.eliminated and p.played_card)
    winners = [p for p in player_list if not p.eliminated and p.played_card and p.played_card.points == max_points]

    if winners:
        # Award the win_round flag to the winner(s)
        for winner in winners:
            winner.won_round = True
            print(f"{winner.name} wins the round!")
    else:
        print("No winners this round.")

    for player in player_list:
        if player.won_round:
            # Increment score by card points
            player.score += player.played_card.points
            print(f"{player.name} gains {player.played_card.points} points for winning the round! (Total: {player.score})")
            player.won_round = False

def move_up_disaster_card_players(player_list: List[Player]):
    for player in player_list:
        if not player.eliminated and len(player.disasters) > 0:
            player.score += len(player.disasters)
            print(f"{player.name} moves up {len(player.disasters)} for disaster cards!")

def check_eliminations(player_list: List[Player]):
    for player in player_list:
        if len(player.disasters) >= 3 and not player.eliminated:
            player.eliminated = True
            print(f"\n💀 {player.name} has been ELIMINATED! (3 disasters)")

def check_winners(player_list: List[Player]) -> Optional[Player]:
    active_players = [p for p in player_list if not p.eliminated]
    
    if len(active_players) == 1:
        print(f"\n🎉 {active_players[0].name} WINS by elimination!")
        return active_players[0]
    
    for player in active_players:
        if player.score >= 50:
            print(f"\n🎉 {player.name} WINS with {player.score} points!")
            player.won_round = True
            return player
    
    return None

def loser_discard_option(loser: Optional[Player], deck: Deck):
    if not loser or loser.eliminated or len(loser.cards) == 0:
        return
    
    print(f"\n{loser.name}, you can discard a card for a new one.")
    show_hand(loser)
    
    choice = input("Discard a card? (y/n): ").lower()
    if choice == 'y':
        while True:
            try:
                idx = int(input(f"Which card? (1-{len(loser.cards)}): ")) - 1
                if 0 <= idx < len(loser.cards):
                    discarded = loser.cards.pop(idx)
                    deck.discard_pile.append(discarded)
                    new_card = deck.draw_card()
                    if new_card:
                        loser.cards.append(new_card)
                        print(f"Drew: {new_card}")
                    break
            except ValueError:
                pass

def use_effect_question():
    while True:
        try:
            confirm_effect = str(input("Do you want to use your effect? (y/n)"))
            if confirm_effect == "y" or confirm_effect == "n":
                return confirm_effect
            else:
                print("Please enter y or n.")
        except ValueError:
            print("Please enter a valid number.")

def effect_handler(player_list: List[Player], deck: Deck):
    # Sort players from least points to most
    # Don't include eliminated players        
    sorted_players = sorted(player_list, key=lambda x: x.score)

    for player in sorted_players:
        if player.played_card.title == "Flaming Chainsaw":
            print("Flaming Chainsaw Stops All Effects!!!")
            return
        
    for player in sorted_players:
        if player.eliminated:
            continue
        if player.played_card.effect == "None":
            continue

        print("\n")

        if player.played_card.title == "Pet Rock":
            show_hand(player)

            # 1: Ask if they want to use
            response = use_effect_question()

            # 2: If use, select point card
            if response == "y":
                while True:
                    try:
                        choice = int(input(f"Choose a point card to play (1-{len(player.cards)}): ")) - 1
                        if 0 <= choice < len(player.cards) and player.cards[choice].type == "point":
                            selected_card = player.cards.pop(choice)
                            deck.discard_pile.append(selected_card)
                            print(f"{player.name} played {player.played_card}")
                            break
                        else:
                            print("Please choose a valid point card.")
                    except ValueError:
                        print("Please enter a valid number.")
            
                # 3: Add score of played_card by selected_card value
                player.played_card.points += selected_card.points
                print(f"New point card total is {player.played_card.points}")

        if player.played_card.title == "Dino Grabber":
            valid_targets = [player for player in player_list if not getattr(player, 'eliminated', False)]
            valid_targets.remove(player)

            for i, valid_target in enumerate(valid_targets):
                print(f"{i+1}. {valid_target.name}")
            print("\n")

            while True:
                try:
                    choice = int(input(f"{player.name}, choose a player to steal from (1-{len(valid_targets)}): "))
                    if 1 <= choice <= len(valid_targets):
                        target = valid_targets[choice - 1]
                        print(f"{player.name} chose {valid_target.name}")
                        break
                    else:
                        print("Please choose a valid target.")
                except ValueError:
                    print("Please enter a valid number.")
            
            show_hand(target)

            while True:
                try:
                    choice = int(input(f"{player.name}, choose a card to steal (1-{len(player.cards)}): "))
                    if 1 <= choice <= len(player.cards):
                        card = target.cards.pop(choice - 1)
                        player.cards.append(card)
                        print(f"{player.name} stole a card from {valid_target.name}!")
                        break
                    else:
                        print("Please choose a valid card.")
                except ValueError:
                    print("Please enter a valid number.")
            
        if player.played_card.title == "Grappling Snake":
            # Only non-eliminated players who have an effect card
            valid_targets = []
            for target in player_list:
                if target.eliminated == False and target.played_card.effect != "None":
                    valid_targets.append(target)
            valid_targets.remove(player)

            # Test if there are any effect cards
            if len(valid_targets) == 0:
                continue

            reveal_cards(player_list)
            # 1: Ask if they want to use
            response = use_effect_question()

            if response == "n":
                break

            # From valid targets, find their scores and ask which to swap with.
            for i, valid_target in enumerate(valid_targets):
                print(f"{i+1}. {valid_target.name}:  {valid_target.played_card.title} ({valid_target.played_card.points})")
            print("\n")

            while True:
                try:
                    choice = int(input(f"{player.name}, choose a player to swap effect cards with (1-{len(valid_targets)}): "))
                    if 1 <= choice <= len(valid_targets):
                        target = valid_targets[choice - 1]
                        print(f"{player.name} chose {valid_target.name}")
                        break
                    else:
                        print("Please choose a valid target.")
                except ValueError:
                    print("Please enter a valid number.")

            temp = player.played_card.points
            player.played_card.points = target.played_card.points
            target.played_card.points = temp

            print(f"Swap occured! Now {player.name}'s {player.played_card.title} is worth {player.played_card.points} and {target.name}'s {player.played_card.title} is worth {player.played_card.points}")
            
        if player.played_card.title == "Delicious Smoothie":
            # 1. Can they use?
            valid_targets = []
            for target in player.cards:
                if target.effect != "None":
                    valid_targets.append(target)
            
            if len(valid_targets) == 0:
                break
            
            print(f"\n{player.name}'s valid effect cards:")
            for i, card in enumerate(valid_targets):
                if card.effect == "None":
                    print(f"    {i+1}. {card.title}, ({card.points})")
                else:
                    print(f"    {i+1}. {card.title}, ({card.points}): {card.effect}")

            # 2: Ask if they want to use
            response = use_effect_question()

            while True:
                try:
                    choice = int(input(f"{player.name}, choose a card to add points (1-{len(valid_targets)}): "))
                    # Must select non-instant card
                    if 1 <= choice <= len(valid_targets) and valid_targets[choice - 1].type == "point":
                        card_selected = valid_targets[choice - 1]
                        player.cards.remove(valid_targets[choice - 1])
                        deck.discard_pile.append(card_selected)
                        break
                    else:
                        print("Please choose a valid point card.")
                except ValueError:
                    print("Please enter a valid number.")
            
            player.played_card.points += card_selected.points
            print(f"{player.name}'s card is now worth {player.played_card.points} points!")
    
        if player.played_card.title == "Fire Spray":

            for i in range(0, 3):
                show_hand(player)

                print(f"{3-i} discard's left.")

                # 1: Ask if they want to use
                response = use_effect_question()

                if response == "y":
                    while True:
                        try:
                            choice = int(input(f"Choose a point card to discard (1-{len(player.cards)}): ")) - 1
                            if 0 <= choice < len(player.cards) and player.cards[choice].type == "point":
                                selected_card = player.cards.pop(choice)
                                deck.discard_pile.append(selected_card)
                                break
                            else:
                                print("Please choose a valid point card.")
                        except ValueError:
                            print("Please enter a valid number.")
                else:
                    break

        if player.played_card.title == "Mouth Trap":
            highest_card_score = 0
            lowest_card_score = 999
            for player in player_list:
                score = player.played_card.points
                if score > highest_card_score:
                    highest_card_score = score
                if score < lowest_card_score:
                    lowest_card_score = score

            for i, selected_player in enumerate(player_list):
                if selected_player.played_card.points == highest_card_score:
                    player_list[i].played_card.points = lowest_card_score
                elif selected_player.played_card.points == lowest_card_score:
                    player_list[i].played_card.points = highest_card_score

        if player.played_card.title == "Treenoculars":
            # Look at the top two cards in the deck and choose one to add to your hand
            top_two_cards = [deck.draw_card(), deck.draw_card()]
            print(f"\n{player.name}, you can choose one of these cards to add to your hand:")
            for i, card in enumerate(top_two_cards):
                print(f"    {i+1}. {card.title}, ({card.points})")
            while True:
                try:
                    choice = int(input(f"Choose a card to add to your hand (1-2): ")) - 1
                    if 0 <= choice < 2:
                        player.cards.append(top_two_cards.pop(choice))
                        # discard the other card
                        deck.discard_pile.append(top_two_cards[0])
                        break
                    else:
                        print("Please choose a valid card.")
                except ValueError:
                    print("Please enter a valid number.")
        
        if player.played_card.title == "Hungry Plant":
            # Choose two players to swap their card points
            valid_targets = [player for player in player_list if not getattr(player, 'eliminated', False)]

            if len(valid_targets) < 2:
                break

            for i, valid_target in enumerate(valid_targets):
                print(f"{i+1}. {valid_target.name}: {valid_target.played_card.title} ({valid_target.played_card.points})")
            print("\n")

            while True:
                try:
                    choice = int(input(f"{player.name}, choose the first player to swap (1-{len(valid_targets)}): "))
                    if 1 <= choice <= len(valid_targets):
                        target = valid_targets[choice - 1]
                        break
                    else:
                        print("Please choose a valid target.")
                except ValueError:
                    print("Please enter a valid number.")
            valid_targets.remove(target)

            for i, valid_target in enumerate(valid_targets):
                print(f"{i+1}. {valid_target.name}: {valid_target.played_card.title} ({valid_target.played_card.points})")
            print("\n")

            while True:
                try:
                    choice = int(input(f"{player.name}, choose the second player to swap (1-{len(valid_targets)}): "))
                    if 1 <= choice <= len(valid_targets):
                        target2 = valid_targets[choice - 1]
                        break
                    else:
                        print("Please choose a valid target.")
                except ValueError:
                    print("Please enter a valid number.")
            
            temp = target.played_card.points
            target.played_card.points = target2.played_card.points
            target2.played_card.points = temp
            print(f"Swap occured! Now {target.name}'s {target.played_card.title} is worth {target.played_card.points} and {target2.name}'s {target2.played_card.title} is worth {target2.played_card.points}")

def instants_handler(player_list: List[Player], deck: Deck):
    # Go around to each non-eliminated person asking for instant cards, starting with lowest point person.
    # If someone during the loop plays an instant card, loop again through all people at the end of the first loop until all players from least points to most are cycled through.
    
    instant_was_played = True
    
    while instant_was_played:
        instant_was_played = False
        sorted_players = sorted(player_list, key=lambda x: x.score)
        
        for player in sorted_players:
            if player.eliminated:
                continue
            
            while True:
                instant_cards = [i for i, c in enumerate(player.cards) if c.type == "instant"]
                if not instant_cards:
                    break
                
                show_hand(player)
                choice = input(f"{player.name}, do you want to play an instant card? (y/n): ").lower()
                if choice == 'y':
                    while True:
                        try:
                            card_choice = int(input(f"Choose an instant card to play (1-{len(player.cards)}): ")) - 1
                            if 0 <= card_choice < len(player.cards) and player.cards[card_choice].type == "instant":
                                instant_card = player.cards.pop(card_choice)
                                deck.discard_pile.append(instant_card)
                                instant_handler(instant_card, player, player_list, deck)
                                instant_was_played = True
                                break
                            else:
                                print("Please choose a valid instant card.")
                        except:
                            print("Please enter a valid number.")
                else:
                    break

def instant_handler(instant_card: PlayerCard, player: Player, player_list: List[Player], deck: Deck):
    if instant_card.title == "Score Swapper":
        # Swap the highest and lowest player played_card points
        non_eliminated_players = [p for p in player_list if not p.eliminated]
        highest_player = max(non_eliminated_players, key=lambda p: p.played_card.points)
        lowest_player = min(non_eliminated_players, key=lambda p: p.played_card.points)
        highest_points = highest_player.played_card.points
        lowest_points = lowest_player.played_card.points
        highest_player.played_card.points = lowest_points
        lowest_player.played_card.points = highest_points
        print(f"{player.name} swapped {highest_player.name}'s and {lowest_player.name}'s card points!")
        reveal_cards(player_list)
    elif instant_card.title == "Score Sapper":
        valid_targets = [p for p in player_list if not p.eliminated and p != player]
        if not valid_targets:
            print("No valid targets to sap score from.")
            return
        # Show all point cards of valid targets, sap 2 points from chosen target card
        for i, target in enumerate(valid_targets):
            print(f"{i+1}. {target.name} (Score: {target.score})")
        while True:
            try:
                choice = int(input(f"{player.name}, choose a player to sap card points from (1-{len(valid_targets)}): ")) - 1
                if 0 <= choice < len(valid_targets):
                    target = valid_targets[choice]
                    target.played_card.points -= 2
                    if target.score < 0:
                        target.score = 0
                    print(f"{player.name} sapped 2 points from {target.name}! New score: {target.played_card.points}")
                    reveal_cards(player_list)
                    break
                else:
                    print("Please choose a valid target.")
            except ValueError:
                print("Please enter a valid number.")
    elif instant_card.title == "Score Adder":
        # Add 2 points to a target player's played_card
        valid_targets = [p for p in player_list if not p.eliminated and p != player]
        if not valid_targets:
            print("No valid targets to add score to.")
            return
        for i, target in enumerate(valid_targets):
            print(f"{i+1}. {target.name} (Points: {target.played_card.points})")
        while True:
            try:
                choice = int(input(f"{player.name}, choose a player to add card points to (1-{len(valid_targets)}): ")) - 1
                if 0 <= choice < len(valid_targets):
                    target = valid_targets[choice]
                    target.played_card.points += 2
                    print(f"{player.name} added 2 points to {target.name}! New points: {target.played_card.points}")
                    reveal_cards(player_list)
                    break
                else:
                    print("Please choose a valid target.")
            except ValueError:
                print("Please enter a valid number.")

def game_start():
    print("🦖 Welcome to Happy Little Dinosaurs! 🦖\n")
    
    num_players = select_number_of_players()
    player_list = enter_player_names(num_players)
    deck = create_decks()

    round_num = 1
    
    while True:
        print(f"\n{'='*50}")
        print(f"ROUND {round_num}")
        print('='*50)

        refill_player_hands(player_list, deck)
        
        disaster = play_disaster(deck)
        
        play_point_cards(player_list)

        reveal_cards(player_list)

        effect_handler(player_list, deck)
        
        reveal_cards(player_list)

        instants_handler(player_list, deck)
        
        loser = disaster_sudden_death_handling(player_list)
        
        reward_disaster(loser, disaster, deck)
        
        reward_points(player_list)
        
        move_up_disaster_card_players(player_list)
        
        check_eliminations(player_list)
        
        winner = check_winners(player_list)
        if winner:
            print("\n" + "="*50)
            print("GAME OVER!")
            print("="*50)
            print("\nFinal Standings:")
            for player in sorted(player_list, key=lambda p: p.score, reverse=True):
                status = "ELIMINATED" if player.eliminated else f"{player.score} points"
                print(f"  {player.name}: {status}")
            break
        
        loser_discard_option(loser, deck)
        
        print("\nCurrent Standings:")
        for player in player_list:
            if not player.eliminated:
                print(f"  {player}")
        
        round_num += 1
        input("\nPress Enter to continue to next round...")

if __name__ == "__main__":
    game_start()