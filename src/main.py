import time
import os
import sys
from game import UnoGame
import card
import player

def clear_terminal():
    os.system('cls')

def countdown(seconds=5):
    print(f"\nPass the device to the next player!")
    for i in range(seconds, 0, -1):
        print(f"Starting in {i}...", end='\r')
        time.sleep(1)
    print(" " * 20, end='\r') 

def print_ascii_card(card: card.Card):
    color_symbols = {
        "R": "♦", "G": "♣", "B": "♠", "Y": "♥"
    }
    
    if card.wild:
        symbol = "★"
        color_name = "WILD"
    else:
        symbol = color_symbols.get(card.color, "?")
        color_name = card.get_color_name()
    
    card_display = card.id if len(card.id) <= 7 else card.id[:7]
    
    print("┌───────────┐")
    print(f"│{symbol}         {symbol}│")
    print("│           │")
    print(f"│  {card_display:^7}  │")
    print("│           │")
    print(f"│{symbol}         {symbol}│")
    print("└───────────┘")
    print(f"  {color_name}")

def print_hand_ascii(player: player.Player):
    color_symbols = {"R": "♦", "G": "♣", "B": "♠", "Y": "♥"}
    
    print(f"\n{player.username}'s Hand ({len(player.hand)} cards):")
    print("=" * 50)
    
    cards = player.hand
    for i in range(0, len(cards), 5):
        row_cards = cards[i:i+5]
        
        for card in row_cards:
            print("┌─────────┐", end=" ")
        print()
        
        for card in row_cards:
            symbol = "★" if card.wild else color_symbols.get(card.color, "?")
            print(f"│{symbol}       {symbol}│", end=" ")
        print()
        
        for card in row_cards:
            print("│         │", end=" ")
        print()
        
        for card in row_cards:
            card_display = card.id if len(card.id) <= 7 else card.id[:7]
            print(f"│ {card_display:^7} │", end=" ")
        print()
        
        for card in row_cards:
            print("│         │", end=" ")
        print()
        
        for card in row_cards:
            symbol = "★" if card.wild else color_symbols.get(card.color, "?")
            print(f"│{symbol}       {symbol}│", end=" ")
        print()
        
        for card in row_cards:
            print("└─────────┘", end=" ")
        print()
        
        for card in row_cards:
            color_name = "WILD" if card.wild else card.get_color_name()
            print(f" {color_name:^9} ", end=" ")
        print()
        print() 

def play_terminal_game():
    clear_terminal()
    print("Welcome to Terminal UNO!")
    print("=" * 30)
    
    player1_name = input("Enter Player 1's name: ").strip() or "Player 1"
    player2_name = input("Enter Player 2's name: ").strip() or "Player 2"
    
    game = UnoGame()
    game.add_player(player1_name)
    game.add_player(player2_name)
    game.start()
    
    print(f"\nGame started! {game.get_curr_player().username} goes first.")
    input("Press Enter to continue...")
    
    while game.queue: 
        current_player = game.get_curr_player()
        current_card = game.get_curr_card()
        
        print(f"Current Player: {current_player.username}")
        print("=" * 40)
        
        print("Current card on table:")
        print_ascii_card(current_card)
        
        print_hand_ascii(current_player)
        
        print("\nCommands:")
        print("  play <color> <number/type> - Play a card (e.g., 'play r 5', 'play b s')")
        print("  draw - Draw a card")
        print("  table - Show game status")
        print("  uno - Call UNO when you have 1 card")
        print("  callout - Call out someone for not saying UNO")
        print("  hand - Show your hand again")
        print("  quit - Exit game")
        
        while True:
            command = input(f"\n{current_player.username}, enter command: ").strip().lower()
            
            if command.startswith("play "):
                card_input = command[5:]
                result = game.play(card_input)
                print(result)
                
                if "cannot play this card" in result or "not found in hand" in result:
                    continue 
                else:
                    if not game.queue:
                        print("\nGame Over!")
                        print(game.scoreboard())
                        return
                    break  
                    
            elif command == "draw":
                result = game.draw()
                print(f"Drew card number: {result}")
                break
                
            elif command == "table":
                print(game.table())
                
            elif command == "uno":
                result = game.uno(current_player.id)
                print(result)
                
            elif command == "callout":
                result = game.callout(current_player.id)
                print(result)
                
            elif command == "hand":
                print_hand_ascii(current_player)
                
            elif command == "quit":
                print("Thanks for playing!")
                return
                
            else:
                print("Invalid command. Try again.")
        
        if game.discard and game.discard[-1].wild and not game.discard[-1].color:
            while True:
                color_choice = input("Choose a color for the wild card (red/green/blue/yellow): ").strip().lower()
                if color_choice in ['red', 'r']:
                    game.discard[-1].color = 'R'
                    break
                elif color_choice in ['green', 'g']:
                    game.discard[-1].color = 'G'
                    break
                elif color_choice in ['blue', 'b']:
                    game.discard[-1].color = 'B'
                    break
                elif color_choice in ['yellow', 'y']:
                    game.discard[-1].color = 'Y'
                    break
                else:
                    print("Invalid color. Please choose red, green, blue, or yellow.")
            game.play(card_input, color_choice)
        
        input(f"\n{current_player.username}'s turn is over. Press Enter to continue...")
        clear_terminal()
        countdown()

if __name__ == "__main__":
    play_terminal_game()
