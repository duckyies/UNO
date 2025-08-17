from typing import List, Optional, Dict
from card import Card 

class PlayerOutput:
    def __init__(self, player_id: int, cards_played: int, name: str):
        self.id = player_id
        self.cards_played = cards_played
        self.name = name

class Player:
    def __init__(self, player_id: int, username: str):
        self.id = player_id
        self.username = username
        self.hand: List[Card] = []
        self.called = False
        self.finished = False
        self.cards_played = 0
        self.messages: List[str] = []

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

    def format_output(self) -> PlayerOutput:
        return PlayerOutput(self.id, self.cards_played, self.username)

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
                    card_id = words
                    color = potential_color
                else:
                    card_id = words[0]
                    color = ""

        if card_id == "":
            return None

        wild = ["WILD", "WILD+4"]
        aliases = ["W","W+4","REV","R","S","NOU","FUCKU"]
        wild_aliases = {
            "W": "WILD",
            "W+4": "WILD+4", 
            "REV": "REVERSE",
            "R": "REVERSE",
            "NOU": "REVERSE",
            "S": "SKIP",
            "FUCKU": "SKIP",
        }
        
        if card_id.upper() in aliases:
            card_id = wild_aliases.get(card_id.upper(), card_id)

        if card_id.upper() in ["WILD", "WILD+4"]:
            for card in self.hand:
                if card.id.upper() == card_id.upper():
                    return card.num
        else:
            if color == "":
                return None
            for card in self.hand:
                if card.id.upper() == card_id.upper() and card.color.upper() == color.upper():
                    return card.num

        return None


    def send_message(self, message: str):
        self.messages.append(message)

    def get_hand(self) -> str:
        self.sort_hand()
        hand_str = " | ".join([f"**{str(card)}**" for card in self.hand])
        return f"Here is your hand:\n\n{hand_str}\n\nYou currently have {len(self.hand)} card(s)."

    def send_hand(self):
        hand = self.get_hand()
        self.send_message(hand)

