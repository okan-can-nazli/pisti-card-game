import pygame
import threading
import time
import os
import random
import csv
import pyfiglet
from collections import Counter
import shutil
import sys


stop_music = False

columns = shutil.get_terminal_size(fallback=(190, 24)).columns
DECK_SIZE=52
JOKER_CARD="J"
THE_5="5"
PER_PISTI_POINT = 10
CHAOS_MODE_FIVES=13
EXTRA_PILE_POINTS = 3
CARDS_PER_HAND = 4
INITIAL_TABLE_CARDS = 4


#Deck loader
def load_deck(deck_list, difficulty_choice, filepath="deck.csv"):
    try:
        print("Deck is Loading...")
        time.sleep(1)
        
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:  # ← moved inside the 'try' block
                # Convert types
                row["point"] = int(row["point"])
                row["face_down"] = True
                deck_list.append(row)

            # Chaos mode: randomize 13 cards to rank '5'
            if difficulty_choice == 2:
                cards_to_change = random.sample(deck_list, CHAOS_MODE_FIVES)
                for card in cards_to_change:
                    card["rank"] = THE_5
                    card["point"] = 0

    except FileNotFoundError:
        print(f"Error: {filepath} not found!")
        sys.exit(1)

    return deck_list

# Music loop
def play_music_loop(folder="musics"):
    
    global stop_music

    pygame.mixer.init()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    music_folder = os.path.join(script_dir, folder)
    tracks = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.endswith(".mp3")]

    if not tracks:
        print("No mp3 files found in Project Musics!")
        return

    random.shuffle(tracks)
    track_index = 0
    while not stop_music:
        pygame.mixer.music.load(tracks[track_index])
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and not stop_music:
            time.sleep(2)
        track_index = (track_index + 1) % len(tracks)



def play_end_sound(result, folder="sound_effects"):
    """Play specific music for win/lose"""
    global stop_music
    stop_music = True  # Stop the background music loop
    
    pygame.mixer.music.stop()
    time.sleep(0.3)  # Give time for background music to stop
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    music_folder = os.path.join(script_dir, folder)
    
    if result == "lose":
        music_file = os.path.join(music_folder, "lose.mp3")
    elif result == "win":
        music_file = os.path.join(music_folder, "win.mp3")
    else:
        music_file = os.path.join(music_folder, "draw.mp3")
    
    if os.path.exists(music_file):
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play()
        


# Main menu
def main_menu():
    print("\n" * 5 )
    title = pyfiglet.figlet_format("PİŞTİ")
    for line in title.splitlines():
        print(line.center(columns))
    print("\n" + "Press Enter to start".center(columns))
    input()

    diff_levels = {1: "Normal", 2: "Chaos Mode"}

    # Get player name
    while True:
        name_input = input("Enter Your Name: ")
        if all(char.isalpha() or char.isspace() for char in name_input):
            player_name = name_input
            break
        print("Your name can only contain letters")

    # Select difficulty
    while True:
        print("\nSelect Level:")
        for key, name in diff_levels.items():
            print(f"{key}. {name}")
        try:
            difficulty_choice = int(input("Enter your choice (1-2): "))
            if difficulty_choice in diff_levels:
                break
            print("Invalid choice. Choose 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number.")



    win_point = 999 # Default high score for Chaos Mode (instant win)

    if difficulty_choice == 1:
        # Select win point ONLY for Normal mode
        while True:
            try:
                win_point = int(input("Enter Win Point (101, 151, or 201): "))
                if win_point in [101, 151, 201]:
                    break
                print("Please enter a valid point")
            except ValueError:
                print("Invalid input. Please enter a number.")

    return player_name, win_point, difficulty_choice


# Game logic
class GameActions:
    def __init__(self, deck):
        self.table = []
        self.player_hand = []
        self.enemy_hand = []
        self.collected = {"player": [], "enemy": []}
        self.deck = deck
        self.showed_cards = []
        self.player_pisti_count = 0
        self.enemy_pisti_count = 0
        self.round_number = 0
        self.enemy_point = 0
        self.player_point = 0
        self.current_turn = "player"  #  first turn in first round
        self.last_collector = None
        self.is_pisti = False
        self.enemy_card = None
        self.paired_rank = None
        self.instant_win = None 


    @property
    def enemy_visible_cards(self):
        # Cards the AI can see
        return self.showed_cards + self.enemy_hand


    @property
    def pair(self):
        """Returns True if the last two cards have the same rank."""
        if len(self.table) < 2:
            return False
        
        elif self.table[-1]["rank"] == self.table[-2]["rank"]:
            self.paired_rank = self.table[-1]["rank"]
            return True
    
    @property
    def joker_condition(self):
        """True if the last card is a JOKER_CARD and table has at least 2 cards."""
        return (
            len(self.table) >= 2 and self.table[-1]["rank"] == JOKER_CARD and self.table[-2]["rank"] != JOKER_CARD
            )
    
    # shuffle and deal cards   
    def draw_cards(self):
        
        # Place initial cards on table
        if len(self.deck) == DECK_SIZE:
            first_card = random.choice(self.deck)
            first_card["face_down"] = False  
            self.table.append(first_card)
            self.deck.remove(first_card)
            
            for _ in range(INITIAL_TABLE_CARDS - 1):
                card = random.choice(self.deck)
                self.table.append(card)
                card["face_down"] = False #to display cards as face up
                self.deck.remove(card)
                
                
        # Draw 4 cards for player and enemy
        for _ in range(CARDS_PER_HAND):
            if self.deck:
                card = random.choice(self.deck)
                card["face_down"]=False  #set card as not FACE_DOWN
                self.player_hand.append(card)
                self.deck.remove(card)
                
        for _ in range(CARDS_PER_HAND):
            if self.deck:
                card = random.choice(self.deck)
                card["face_down"] = True #set card as FACE_DOWN
                self.enemy_hand.append(card)
                self.deck.remove(card)



    def play_a_turn(self):
        
        self.enemy_card = None
        
        # Player turn
        if self.current_turn == "player":
            
            #Player selects a card 
            while True:
                try:
                    print("\n"*2)
                    choose_index = int(input(f"Select Your Card to Play (1-{len(self.player_hand)}): "))
                    if not (1 <= choose_index <= len(self.player_hand)):
                        raise ValueError
                except ValueError:
                    continue  
                break      
            
            #Player plays the card
            self.player_card = self.player_hand[choose_index - 1]
            self.showed_cards.append(self.player_card)
            self.table.append(self.player_card)
            self.player_hand.remove(self.player_card)
            
            self.collect_cards() # After player played a card,check pair or JOKER_CARD condition
            
            self.current_turn = "enemy" # Hand over turn to enemy
                
            
        #Enemy turn
        elif self.current_turn == "enemy":
        
            # Enemy selects a card
        
            # Try to match table card
            if self.table:
                for card in self.enemy_hand:
                
                    if card["rank"] == self.table[-1]["rank"]:
                        self.enemy_card = card
                        break

            # If no match, pick strategically
            if not self.enemy_card:
                counts = Counter(c["rank"] for c in self.enemy_visible_cards)
                max_count = max(counts.get(c["rank"], 0) for c in self.enemy_hand)
                best_cards = [c for c in self.enemy_hand if counts.get(c["rank"], 0) == max_count]
                
                # AVOID playing Jack when table is empty
                if not self.table:
                    non_jack_cards = [c for c in best_cards if c["rank"] != "J"]
                    if non_jack_cards:
                        best_cards = non_jack_cards
                    else:
                        # If all best cards are Jacks, pick ANY non-Jack from hand
                        non_jack_cards = [c for c in self.enemy_hand if c["rank"] != "J"]
                        if non_jack_cards:
                            best_cards = non_jack_cards
                        # If hand is ALL J
                        
                #declare enemy_card
                self.enemy_card = random.choice(best_cards)

            #Enemy plays the card
            self.showed_cards.append(self.enemy_card)
            self.table.append(self.enemy_card)
            self.enemy_card["face_down"] = False
            self.enemy_hand.remove(self.enemy_card)
            
            self.collect_cards()  # After enemy played a card,check pair or JOKER_CARD condition
            
            self.current_turn = "player" # Hand over turn to player

    def collect_for_current_player(self):
        """Collect cards for whoever's turn it is"""
        self.last_collector = self.current_turn
        self.collected[self.current_turn].append(self.table.copy())

    def collect_cards(self):
        
        #All Pisti Conditions
        if self.pair and len(self.table) == 2: 
            
            #THE_5 Pisti condition
            if self.paired_rank == THE_5:
                
                self.is_pisti = True
                
                # for player
                if self.current_turn == "player":
                    self.instant_win = "player"
                    self.collected["player"].append(self.table.copy())
                                
                # for enemy
                elif self.current_turn == "enemy":
                    self.instant_win = "enemy"
                    self.collected["enemy"].append(self.table.copy())
                
                self.table.clear()  # Clear the table
                return  # exit from function instantly
            
            # JOKER_CARD condition
            elif self.paired_rank == JOKER_CARD:
                
                # for player
                if self.current_turn == "player":
                    
                    self.collect_for_current_player()
                    self.player_pisti_count += 2

                # for enemy
                elif self.current_turn == "enemy":

                    self.collect_for_current_player()
                    self.enemy_pisti_count += 2
                    
            # normal pişti condition
            else:
                
                # for player
                if self.current_turn == "player":
                    self.collect_for_current_player()
                    self.player_pisti_count += 1

                # for enemy
                elif self.current_turn == "enemy":
                    self.collect_for_current_player()
                    self.enemy_pisti_count += 1


            self.is_pisti = True 
            
            self.table.clear() #take whole cards on the table

            
        #Normal Pair Condition
        elif (self.pair or self.joker_condition) and len(self.table) >= 2:
            
            if self.current_turn == "player":
                self.collect_for_current_player()

                
            elif self.current_turn == "enemy":
                self.collect_for_current_player()


            
            self.table.clear() #take whole cards on the table



    # Give claimed points to everyone and reset temporary point holders
    def add_points(self):
        
        if not self.deck and not self.player_hand and not self.enemy_hand: 
            
            if self.table and self.last_collector:
                # Add leftover table cards to last collector
                self.collected[self.last_collector].append(self.table.copy())
        
        # Calculate round points
        player_round_points = sum(card["point"] for pile in self.collected["player"] for card in pile)
        enemy_round_points = sum(card["point"] for pile in self.collected["enemy"] for card in pile)
        
        
        # Extra (3) points for collecting more piles
        if len(self.collected["player"]) < len(self.collected["enemy"]):
            self.enemy_point += EXTRA_PILE_POINTS
        elif len(self.collected["player"]) > len(self.collected["enemy"]):
            self.player_point += EXTRA_PILE_POINTS

        #add round points to total points
        self.player_point += self.player_pisti_count * PER_PISTI_POINT + player_round_points
        self.enemy_point += self.enemy_pisti_count * PER_PISTI_POINT + enemy_round_points
            
        #clear temporary point holders
        
        self.table.clear()
        
        self.player_pisti_count = 0
        self.enemy_pisti_count = 0
        
        self.collected = {"player": [], "enemy": []}
        
        self.showed_cards.clear() 
    
    
        

class Printer:
    
    def __init__(self, game_obj):
        self.game = game_obj


    def title_printer(self,title):
        title=pyfiglet.figlet_format(title)
        for line in title.splitlines():
            print(line.center(columns))
        
    # Show Round/Point Border and Player-Enemy Border
    def border_printer(self,name,width=60):
        text = name
        border = "┌" + "─" * (width - 2) + "┐"
        bottom = "└" + "─" * (width - 2) + "┘"
        padded_text = text.center(width - 2)
        print(border.center(columns))
        print(f"│{padded_text}│".center(columns))
        print(bottom.center(columns))
    
    
    
    # Show ANY card or card list based on FACE_DOWN
    def card_printer(self,hand,hidden_card_count=0):
        card_lines = []
        for card in hand:
            
            #FACE UP cards for player hand, table, enemy's last played card
            if not card.get("face_down"):
                    
                rank = str(card["rank"])
                suit = card["suit"]
                lines = [
                    "┌───────┐" + "┐" * hidden_card_count,
                f"│ {rank:<2}    │" + "|" * hidden_card_count,
                f"|       |" + "|" * hidden_card_count,
                f"│   {suit}   │" + "|" * hidden_card_count,
                f"|       |" + "|" * hidden_card_count,
                f"│    {rank:>2} │" + "|" * hidden_card_count,
                "└───────┘" + "┘" * hidden_card_count
                ]
                card_lines.append(lines)

            #FACE DOWN cards for enemy hand and deck
            else:                
                lines = [
                    "┌───────┐" + "┐" * hidden_card_count,
                    "│▓▓▓▓▓▓▓│" + "│" * hidden_card_count,
                    "│▓▓▓▓▓▓▓│" + "│" * hidden_card_count,
                    "│▓ ▓ ▓ ▓│" + "│" * hidden_card_count,
                    "│▓▓▓▓▓▓▓│" + "│" * hidden_card_count,
                    "│▓▓▓▓▓▓▓│" + "│" * hidden_card_count,
                    "└───────┘" + "┘" * hidden_card_count,
                ]
                
                card_lines.append(lines)
        
        #print card(s)
        if card_lines:
            for i in range(len(card_lines[0])):
                line = " ".join(card[i] for card in card_lines)
                print(line.center(columns))
        else:
            print(9 * "\n")



    # End game display
    def end_game_printer(self, player_name, player_points, enemy_points, win_point,instant_win):
        if player_points >= win_point or enemy_points >= win_point or instant_win:
            if (player_points > enemy_points) or instant_win == "player":
                title = f"{player_name} Won"
                result = "win"

            elif (enemy_points > player_points) or instant_win == "enemy":
                title = f"YOU LOSE"
                result = "lose"

            else:
                title = "DRAW"
                result = "draw"
            

            print("\n" * 10)

            self.title_printer(title)
            print("\n" * 3)
            print(f"{player_name}:{player_points} || Enemy:{enemy_points}".center(columns))
            
            play_end_sound(result) # Play end game music

            print("\n" * 5)
            input("Press Enter to exit...".center(columns))  # This keeps program alive until you press Enter

        
def main():
    
    # Start background music
    music_thread = threading.Thread(target=play_music_loop, daemon=True)
    music_thread.start()    
    # Get player name info,win point and difficulty level
    player_name, win_point, diff_choice = main_menu()
    
    deck = []
    game = GameActions(deck)
    printer = Printer(game)
    game.printer = printer


    # Main game loop
    while win_point > game.player_point and win_point > game.enemy_point and not game.instant_win: 

        if not game.deck and not game.player_hand and not game.enemy_hand:
            game.add_points() # compute & add claimed round points to everyone and reset round point holders 
            
             # Check if game is over
            if game.player_point >= win_point or game.enemy_point >= win_point:
                break
            load_deck(game.deck, diff_choice, "deck.csv") # renew deck
            game.round_number += 1
            
            if game.round_number > 1:# each round change first player
                game.current_turn = "enemy" if game.current_turn == "player" else "player"

        # Draw cards if hands are empty
        if not game.player_hand and not game.enemy_hand and game.deck:
            game.draw_cards()
        
            
        
    
        # Display game state
        printer.border_printer(f" {player_name}: {game.player_point} | ROUND: {game.round_number} | Enemy: {game.enemy_point} ",columns) # main border
        
        printer.card_printer([game.deck[-1]] if game.deck else [],  len(game.deck)-1 if game.deck else 1) # deck
        print(f"{len(game.deck)} cards left".center(columns)) # deck
        print("\n"*1)
        
        if game.enemy_card is not None:# enemy's last played card
            printer.card_printer([game.enemy_card])
            print("Enemy's Last Played Card".center(columns))
            print("\n"*1)
            
        printer.card_printer(game.enemy_hand)# enemy hand
        printer.border_printer("Enemy") # enemy border
        
        printer.card_printer([game.table[-1]] if game.table else [], len(game.table)-1 if game.table else 0)#table
        
        printer.border_printer(player_name)# player border
        printer.card_printer(game.player_hand)#player hand
        
        
        game.play_a_turn() #play a turn then check pair or JOKER_CARD condition
    

        
        if game.is_pisti:
            printer.title_printer("   PİŞTİ!!!")
            time.sleep(1)
            game.is_pisti = False



    # End game display
    printer.end_game_printer(player_name, game.player_point, game.enemy_point, win_point,game.instant_win)


if __name__ == "__main__":
    main()
