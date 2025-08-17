rules: dict[str, dict[str, str | int]] = {
    "DECKS": {
        "desc": "The number of decks to use.",
        "value": 1,
        "name": "Decks",
        "type": "integer",
        "max": 8,
        "min": 1
    },
    "INITIAL_CARDS": {
        "desc": "How many cards to pick up at the beginning.",
        "value": 7,
        "name": "Initial Cards",
        "type": "integer",
        "min": 1,
        "max": 5000
    },
    "DRAW_SKIP": {
        "desc": "Whether pickup cards (+2, +4) should also skip the next person's turn.",
        "value": True,
        "name": "Draws Skip",
        "type": "boolean"
    },
    "REVERSE_SKIP": {
        "desc": "Whether reverse cards skip turns when there's only two players left.",
        "value": True,
        "name": "Reverses Skip",
        "type": "boolean"
    },
    "MUST_PLAY": {
        "desc": "Whether someone must play a card if they are able to.",
        "value": False,
        "name": "Must Play",
        "type": "boolean"
    },
    "CALLOUTS": {
        "desc": "Gives the ability to call someone out for not saying uno!",
        "value": True,
        "name": "Callouts",
        "type": "boolean"
    },
    "CALLOUT_PENALTY": {
        "desc": "The number of cards to give someone when called out.",
        "value": 2,
        "name": "Callout Penalty",
        "type": "integer",
        "max": 1000
    },
    "FALSE_CALLOUT_PENALTY": {
        "desc": "The number of cards to give someone for falsely calling someone out.",
        "value": 2,
        "name": "False Callout Penalty",
        "type": "integer",
        "max": 1000
    },
    "DRAW_AUTOPLAY": {
        "desc": "Automatically plays a card after drawing, if possible. If a wild card is drawn, will give a prompt for color.",
        "value": False,
        "name": "Automatically Play After Draw",
        "type": "boolean"
    },
}

rule_keys = list(rules.keys())

    
if __name__ == "__main__":
    pass