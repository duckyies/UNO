import random
import time
from typing import Dict, List, Optional
from  gameplay.engine.card import Card
from  gameplay.engine.player import Player
from  gameplay.engine.rules import Rule
from  gameplay.engine.constants import COLORS, COLOR_ALIASES, COLOR_SYMBOLS, COLOR_VALUES

class UnoGame:
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.queue: List[Player] = []
        self.deck: List[Card] = []
        self.called_out: bool = False
        self.discard: List[Card] = []
        self.finished: List[Player] = []
        self.drawn: int = 0
        self.card_num: int = 1
        self.time_started: float = 0
        self.rules: List[Rule] = self.generate_rules()


    @staticmethod
    def generate_rules() -> List[Rule]:
        return [
            Rule(0, "The number of decks to use.", 1, "Decks", "integer", 8, 1),
            Rule(1, "How many cards to pick up at the beginning.", 7, "Initial Cards", "integer", 5000, 1),
            Rule(2, "Whether pickup cards (+2, +4) should also skip the next person's turn.", 1, "Draws Skip", "boolean", 0, 0),
            Rule(3, "Whether reverse cards skip turns when there's only two players left.", 1, "Reverses Skip", "boolean", 0, 0),
            Rule(4, "Whether someone must play a card if they are able to.", 0, "Must Play", "boolean", 0, 0),
            Rule(5, "Gives the ability to call someone out for not saying uno!.", 1, "Callouts", "boolean", 0, 0),
            Rule(6, "The number of cards to give someone when called out.", 2, "Callout Penalty", "integer", 1000, 0),
            Rule(7, "The number of cards to give someone for falsely calling someone out.", 2, "False Callout Penalty", "integer", 1000, 0),
        ]

    def generate_deck(self):
        decks_rule = self.get_rule("decks")
        if not decks_rule:
            raise Exception("Rule 'decks' not found")
        
        decks = decks_rule.value
        for _ in range(decks):
            for color in COLORS:
                for card_num in range(10):
                    self.deck.append(Card(str(card_num), color, self.card_num))
                    self.card_num += 1
                    if card_num != 0: 
                        self.deck.append(Card(str(card_num), color, self.card_num))
                        self.card_num += 1
                
                for _ in range(2):
                    self.deck.append(Card("+2", color, self.card_num))
                    self.card_num += 1
                    self.deck.append(Card("SKIP", color, self.card_num))
                    self.card_num += 1
                    self.deck.append(Card("REVERSE", color, self.card_num))
                    self.card_num += 1
            
            for _ in range(4):
                self.deck.append(Card("WILD", "", self.card_num))
                self.card_num += 1
                self.deck.append(Card("WILD+4", "", self.card_num))
                self.card_num += 1
        
        self.shuffle_deck()

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def add_player(self, name: str, is_ai: bool = False) -> Player:
        player = Player(len(self.players), name, is_ai)
        self.players[player.id] = player
        return player

    def start(self):
        if len(self.players) < 2:
            raise Exception("Need at least two players to start!")
        
        self.generate_deck()
        self.queue = [player for player in self.players.values()]
        self.time_started = time.time()
        self.discard.append(self.deck.pop())
        
        start_card_rule = self.get_rule("Initial Cards")
        if not start_card_rule:
            raise Exception("Rule 'Initial Cards' not found")
        
        start_card_no = start_card_rule.value
        if start_card_no * len(self.players) > len(self.deck):
            raise Exception("Did not find enough cards to start playing")
        
        for player_id in self.players.keys():
            self.deal(player_id, start_card_no)

    def deal(self, player_id: int, number: int) -> str:
        if len(self.deck) < number:
            if len(self.discard) == 0:
                raise Exception("Not enough cards found to play")
            
            top_card = self.discard[0]
            self.deck.extend(self.discard[1:])
            self.discard = [top_card]
            self.shuffle_deck()
        
        player = self.players.get(player_id)
        if not player:
            raise Exception(f"Player with id {player_id} not found")
        
        card_num = f"{self.deck[0].get_color_name()} {self.deck[0].id}" if self.deck else -1
        
        for _ in range(number):
            if self.deck:
                player.hand.append(self.deck.pop(0))
                self.drawn += 1
        
        player.sort_hand()
        player.called = False
        return card_num

    def scoreboard(self) -> str:
        lines = []
        rank = 1
        for person in self.finished:
            lines.append(f"{rank}. *{person.username}*")
            rank += 1
        
        mins = int((time.time() - self.time_started) / 60)
        lines.append(f"\nThis game lasted {mins} minutes and {self.drawn} cards were drawn")
        return "\n".join(lines)

    def get_rule(self, name: str) -> Optional[Rule]:
        return next((rule for rule in self.rules if rule.name.lower() == name.lower()), None)

    def get_curr_player(self) -> Player:
        if not self.queue:
            raise Exception("No players in queue")
        return self.queue[0]

    def get_curr_card(self) -> Card:
        if not self.discard:
            raise Exception("No cards in discard pile")
        return self.discard[-1]

    def next(self) -> Player:
        if not self.queue:
            raise Exception("Game has ended!")
        
        player = self.queue.pop(0)
        self.queue.append(player)
        self.queue = [p for p in self.queue if not p.finished]
        
        if not self.queue:
            raise Exception("All players finished!")
        
        return self.queue[0]

    def play(self, card_str: str, wild_color: str = None) -> str:       
        if not self.queue:
            return "Game has ended!"
        print(card_str)

        rev_skip = self.get_rule("Reverses Skip").value
        draw_skip = self.get_rule("Draws Skip").value
        player = self.queue[0]

        words = card_str.split()
        found_card_num = player.get_card(words)
        if found_card_num is not None:
            temp = next((cd for cd in player.hand if cd.get_value() == found_card_num), None)
            card_obj = Card(temp.id, temp.color, temp.num)
            if card_obj is None:
                return f"Card {found_card_num} not found in hand, it's currently {player.username}'s turn"

            curr_card = self.discard[-1]
            if card_obj.wild or card_obj.color == "" or curr_card.id == card_obj.id or curr_card.color == card_obj.color or curr_card.color == "":
                self.called_out = False
                self.discard.append(card_obj)

                if card_obj.wild and wild_color:
                    parsed_color = self.queue[0].parse_color(wild_color)
                    if parsed_color:
                        card_obj.color = parsed_color
                    else:
                        return "Invalid color for wild card."

                player.hand = [c for c in player.hand if c.get_value() != found_card_num ]
                player.sort_hand()
                prefix = ""
                extra = ""

                if len(player.hand) == 0:
                    player.finished = True
                    self.finished.append(player)
                    prefix += f"{player.username} has no more cards. They finished in rank *{len(self.finished)}*!\n\n"

                    if len(self.queue) == 2:
                        prefix += self.scoreboard()
                        self.finished.append(self.queue[1])
                        self.queue = []
                        return prefix

                if card_obj.id.upper() == "REVERSE":
                    if len(self.queue) > 2:
                        self.queue = self.queue[::-1]
                        ins = self.queue.pop()
                        self.queue.insert(0, ins)
                        extra += "Turns are now in reverse order!"

                    elif rev_skip == 1:
                        self.queue = self.queue[::-1]
                        extra += f"{self.queue[0].username}, skip a turn!"

                elif card_obj.id.upper() == "SKIP":
                    ins = self.queue.pop(0)
                    self.queue.append(ins)
                    extra += f"{self.queue[0].username}, skip a turn!"

                elif card_obj.id == "+2":
                    amount = 2
                    self.deal(self.queue[1].id, amount)
                    extra += f"{self.queue[1].username} picks up {amount}!"
                    if draw_skip == 1:
                        extra += " Also, skip a turn!"
                        ins = self.queue.pop(0)
                        self.queue.append(ins)

                elif card_obj.id.upper() == "WILD":
                    extra += f"The color is now {card_obj.color and card_obj.get_color_name() or 'wild'}"

                elif card_obj.id.upper() == "WILD+4":
                    self.deal(self.queue[1].id, 4)
                    extra += f"{self.queue[1].username} picks up! The current color is now {card_obj.color and card_obj.get_color_name() or 'wild'}"
                    if draw_skip == 1:
                        extra += " Also, skip a turn!"
                        ins = self.queue.pop(0)
                        self.queue.append(ins)

                self.next()
                return prefix + "\n" + extra
            else:
                return f"You cannot play this card here. Last played card was {curr_card.color} {curr_card.id}"

        return f"Card {card_str} not found in hand, it's currently {player.username}'s turn"

    def draw(self) -> str:
        must_play = self.get_rule("Must Play").value
        player = self.queue[0]

        if must_play == 1:
            curr_card = self.discard[-1]
            for card in player.hand:
                if card.wild or card.color == "" or curr_card.id == card.id or curr_card.color == card.color:
                    return "You must play a card if able."

        card_num = self.deal(player.id, 1)
        self.next()
        return f"{card_num}"

    def callout(self, call_player_id: int) -> str:
        callouts = self.get_rule("Callouts").value
        if callouts == 0:
            return "Callouts are not permitted in this game"
        if self.called_out:
            return "A callout was already performed in this turn!"

        callout_penalty = self.get_rule("Callout Penalty").value
        false_callout = self.get_rule("False Callout Penalty").value
        called_out = False
        res = ""
        calls = []
        for player in self.queue:
            if len(player.hand) == 1 and not player.called:
                calls.append(player.id)
                called_out = True
                res += f"{player.username} you did not say UNO! Pick up {callout_penalty}\n"
        for pid in calls:
            self.deal(pid, callout_penalty)
        if not called_out:
            self.deal(call_player_id, false_callout)
            self.called_out = True
            return f"There was no one to call out! Pick up {callout_penalty}"
        else:
            self.called_out = True
            return res

    def uno(self, call_player_id: int) -> str:
        player = next((ply for ply in self.queue if ply.id == call_player_id), None)
        if not player:
            return "Player not found!"
        if len(player.hand) <= 2:
            if player.called:
                return "You already said UNO!"
            else:
                player.called = True
                return "UNO!"
        return "You have more than 1 card!"

    def table(self) -> str:
        last_card = self.discard[-1]
        ext = f"A {last_card.get_color_name()} {last_card.id} has been played!\nIt is currently {self.queue[0].username}'s turn!\n\n"
        for idx, player in enumerate(self.queue, start=1):
            ext += f"{idx}. {player.username} - {len(player.hand)} cards\n"

        mins = int((time.time() - self.time_started) / 60)
        ext += f"This game has lasted {mins} minutes and {self.drawn} cards have been drawn"
        return ext
