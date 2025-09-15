from typing import List, Optional
from card import Card 
from game import UnoGame
class Player:
    def __init__(self, player_id: int, username: str, is_ai: bool = False):
        self.id = player_id
        self.is_ai = is_ai
        self.username = username
        self.hand: List[Card] = []
        self.called = False
        self.finished = False

    def cards_changed(self):
        self.sort_hand()

    def sort_hand(self):
        self.hand.sort()

    def parse_color(self, color: str) -> str:
        color_map = {
            "red": "R", "r": "R", "R": "R",
            "green": "G", "g": "G", "G": "G",
            "blue": "B", "b": "B", "B": "B",
            "yellow": "Y", "y": "Y", "Y": "Y",
        }
        return color_map.get(color, "")

    def get_card(self, words: List[str]) -> Optional[int]:
        color = ""
        card_id = ""
        
        if len(words) == 1:
            str_input = words[0]
            parsed_color = self.parse_color(str_input)
            if parsed_color != "":
                return None
            else:
                card_id = str_input
        elif len(words) >= 2:
            potential_color = self.parse_color(words[0])
            if potential_color != "":
                color = potential_color
                card_id = words[1]
            else:
                potential_color = self.parse_color(words[1])
                if potential_color != "":
                    return None
                else:
                    card_id = words[0]
                    color = ""

        if card_id == "":
            return None

        aliases = ["W","W+4","REV","R","S"]
        wild_aliases = {
            "W": "WILD",
            "W+4": "WILD+4", 
            "REV": "REVERSE",
            "R": "REVERSE",
            "S": "SKIP",
        }
        
        if card_id.upper() in aliases:
            card_id = wild_aliases.get(card_id.upper(), card_id)

        if card_id.upper() in ["WILD", "WILD+4"]:
            for card in self.hand:
                if card.id.upper() == card_id.upper():
                    return card.get_value()
        else:
            if color == "":
                return None
            for card in self.hand:
                if card.id.upper() == card_id.upper() and card.color.upper() == color.upper():
                    return card.get_value()

        return None

    def get_hand(self) -> str:
        self.sort_hand()
        hand_str = " | ".join([f"**{str(card)}**" for card in self.hand])
        return f"Here is your hand:\n\n{hand_str}\n\nYou currently have {len(self.hand)} card(s)."

    def select_card_to_play(self, game: UnoGame) -> tuple:

        current_card = game.get_curr_card()
        hand = self.hand[:]
        hold_numbers = set()

        numbers_seen = {}
        for card in hand:
            if not card.wild:
                numbers_seen.setdefault(card.id, set()).add(card.color)
        for num, colors in numbers_seen.items():
            if len(colors) > 1:
                hold_numbers.add(num)

        for card in hand:
            if (card.id in ["+2", "SKIP", "REVERSE", "WILD+4"] or card.wild) and (
                card.wild or card.color == current_card.color or card.id == current_card.id
            ):
                if card.wild:
                    color_counts = {}
                    for c in hand:
                        if c.color and not c.wild:
                            color_counts[c.color] = color_counts.get(c.color, 0) + 1
                    best_color = max(color_counts, key=color_counts.get) if color_counts else "R"
                    return (f"play {card.id.lower()} {best_color.lower()}", best_color)
                return (f"play {card.color.lower()} {card.id.lower()}", None)

        for card in hand:
            if not card.wild and card.id not in hold_numbers and (
                card.color == current_card.color or card.id == current_card.id
            ):
                return (f"play {card.color.lower()} {card.id.lower()}", None)

        for card in hand:
            if not card.wild and card.id in hold_numbers and (
                card.color == current_card.color or card.id == current_card.id
            ):
                return (f"play {card.color.lower()} {card.id.lower()}", None)

        if len(self.hand) == 2 and not self.called:
            game.uno(self.id)

        for card in hand:
            if card.wild or card.color == current_card.color or card.id == current_card.id:
                if card.wild:
                    color_counts = {}
                    for c in hand:
                        if c.color and not c.wild:
                            color_counts[c.color] = color_counts.get(c.color, 0) + 1
                    best_color = max(color_counts, key=color_counts.get) if color_counts else "R"
                    return (f"play {card.id.lower()} {best_color.lower()}", best_color)
                return (f"play {card.color.lower()} {card.id.lower()}", None)

        return ("draw", None)

