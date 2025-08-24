from typing import List, Optional, Dict
from card import Card 

class Player:
    def __init__(self, player_id: int, username: str):
        self.id = player_id
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

