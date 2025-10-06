import pickle
import base64

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from gameplay.engine.game import UnoGame
from gameplay.engine.constants import COLOR_SYMBOLS

SESSION_KEY = "uno_game_pickle"
TURN_REVEAL_KEY = "turn_revealed_for"
WILD_COLOR_PENDING = "wild_color_pending"
MESSAGES_KEY = "uno_messages"

def _save_game_to_session(request, game_obj):
    """Save game state to session using pickle and base64."""
    pick = pickle.dumps(game_obj)
    request.session[SESSION_KEY] = base64.b64encode(pick).decode()
    request.session.modified = True


def _load_game_from_session(request):
    """Load game state from session."""
    val = request.session.get(SESSION_KEY)
    if not val:
        return None
    try:
        pick = base64.b64decode(val)
        game = pickle.loads(pick)
        return game
    except Exception as e:
        print(f"Error loading game: {e}")
        return None


def _clear_game(request):
    """Clear all game-related session data."""
    request.session.pop(SESSION_KEY, None)
    request.session.pop(TURN_REVEAL_KEY, None)
    request.session.pop(WILD_COLOR_PENDING, None)
    request.session.pop(MESSAGES_KEY, None)
    request.session.modified = True


def _add_message(request, msg):
    """Add a message to the session messages list."""
    messages = request.session.get(MESSAGES_KEY, [])
    messages.append(msg)
    request.session[MESSAGES_KEY] = messages[-20:]  
    request.session.modified = True


def _get_messages(request, clear=True):
    """Get messages from session and optionally clear them."""
    messages = request.session.get(MESSAGES_KEY, [])
    if clear:
        request.session[MESSAGES_KEY] = []
        request.session.modified = True
    return messages


def _format_card_for_template(card):
    """Return dict representing card for template rendering."""
    if not card:
        return None
    
    is_wild = getattr(card, "wild", False) or getattr(card, "color", "") == ""
    color = getattr(card, "color", None) or ""
    card_id = getattr(card, "id", "")
    
    if is_wild and not color:
        display = card_id
        color_name = "Choose Color"
        symbol = "★"
    elif is_wild:
        display = card_id
        color_name = card.get_color_name() 
        symbol = "★"
    else:
        display = f"{color} {card_id}" if color else card_id
        color_name = card.get_color_name()
        symbol = COLOR_SYMBOLS.get(color, "?")
    
    if is_wild and not color:
        card_str = card_id.lower()
    elif is_wild and color:
        card_str = f"{card_id.lower()} {color.lower()}"
    elif color:
        card_str = f"{color.lower()} {card_id.lower()}"
    else:
        card_str = card_id.lower()
    
    return {
        "id": card_id,
        "wild": is_wild,
        "color": color,
        "display": display,
        "color_name": color_name,
        "symbol": symbol,
        "card_str": card_str
    }


def _process_ai_turns(game: UnoGame, request):
    """Process AI turns until it's a human player's turn or game ends."""
    messages_added = []
    
    while game.queue and game.get_curr_player().is_ai:
        cp = game.get_curr_player()
        
        play_cmd, wild_color = cp.select_card_to_play(game)
        
        if play_cmd.startswith("play"):
            payload = play_cmd[5:] if len(play_cmd) > 5 else ""
            
            try:
                if wild_color:
                    res = game.play(payload, wild_color)
                    messages_added.append(f"{cp.username} played {payload} and chose {wild_color}")
                else:
                    res = game.play(payload)
                    messages_added.append(f"{cp.username} played {payload}")
                
                if len(cp.hand) == 1 and not cp.called:
                    uno_result = game.uno(cp.id)
                    messages_added.append(f"{cp.username}: {uno_result}")
                    
                if cp.finished:
                    messages_added.append(f"🎉 {cp.username} finished in rank {len(game.finished)}!")
                    
            except Exception as e:
                messages_added.append(f"AI play error: {e}")
                try:
                    res = game.draw()
                    messages_added.append(f"{cp.username} drew a card")
                except:
                    pass
        else:
            try:
                res = game.draw()
                messages_added.append(f"{cp.username} drew a card")
            except Exception as e:
                messages_added.append(f"AI draw error: {e}")
        
        if not game.queue:
            break
    
    for msg in messages_added:
        _add_message(request, msg)
    
    return game


@require_http_methods(["GET", "POST"])
def start_game_view(request):
    """Create a new game from form input."""
    if request.method == "POST":
        try:
            human_count = int(request.POST.get("human_count", "1"))
            human_count = max(1, min(4, human_count))  
        except ValueError:
            human_count = 1
        
        names = []
        for i in range(1, human_count + 1):
            name = request.POST.get(f"human_name_{i}", "").strip()
            if name:
                names.append(name)
            else:
                names.append(f"Player{i}")
        
        try:
            ai_count = int(request.POST.get("ai_count", "0"))
            ai_count = max(0, min(5, ai_count))  
        except ValueError:
            ai_count = 0
        
        if len(names) + ai_count < 2:
            return render(request, "gameplay/start.html", {
                "error": "Need at least 2 players to start a game!"
            })
        
        game = UnoGame()
        
        for name in names:
            game.add_player(name, is_ai=False)
        
        for i in range(ai_count):
            game.add_player(f"AI-{i+1}", is_ai=True)
        
        try:
            game.start()
            _save_game_to_session(request, game)
            request.session[TURN_REVEAL_KEY] = None
            request.session[WILD_COLOR_PENDING] = False
            _add_message(request, f"🎮 Game started! {game.get_curr_player().username} goes first.")
            
            if game.get_curr_player().is_ai:
                game = _process_ai_turns(game, request)
                _save_game_to_session(request, game)
            
            return redirect("uno_game")
        except Exception as e:
            return render(request, "gameplay/start.html", {
                "error": f"Failed to start game: {e}"
            })
    
    return render(request, "gameplay/start.html", {})


@require_http_methods(["GET", "POST"])
def game_view(request):
    """Main game view - handles all game actions."""
    game: UnoGame = _load_game_from_session(request)
    if not game:
        return redirect("uno_start")
    
    if not game.queue:
        context = {
            "game_over": True,
            "scoreboard": game.scoreboard(),
            "finished": game.finished
        }
        _clear_game(request)
        return render(request, "gameplay/game.html", context)
    
    current_player = game.get_curr_player()
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "start_turn":
            request.session[TURN_REVEAL_KEY] = current_player.id
            request.session.modified = True
            _add_message(request, f"📋 {current_player.username}'s turn revealed")
            return redirect("uno_game")
        
        elif action == "end_turn":
            request.session[TURN_REVEAL_KEY] = None
            request.session.modified = True
            _add_message(request, f"✅ Turn hidden. Pass device to next player.")
            return redirect("uno_game")
        
        elif action == "play":
            card_input = request.POST.get("card_input", "").strip()
            
            is_wild_card = any(wild in card_input.upper() for wild in ["WILD+4", "WILD"])
            
            if is_wild_card and not request.session.get(WILD_COLOR_PENDING):
                request.session[WILD_COLOR_PENDING] = card_input
                request.session.modified = True
                return redirect("uno_game")
            
            wild_color = request.POST.get("wild_color", "").strip().lower() if is_wild_card else None
            
            try:
                if wild_color:
                    result = game.play(card_input)
                    _add_message(request, f"✅ {current_player.username} played {card_input} and chose {wild_color}")
                else:
                    result = game.play(card_input)
                    _add_message(request, f"✅ {current_player.username} played {card_input}")
                
                request.session[WILD_COLOR_PENDING] = None
                
                if "cannot play this card" in result.lower() or "not found in hand" in result.lower():
                    _add_message(request, f"❌ {result}")
                    return redirect("uno_game")

                if current_player.finished:
                    _add_message(request, f"🎉 {current_player.username} finished in rank {len(game.finished)}!")
                
                if result and not any(x in result.lower() for x in ["cannot play", "not found"]):
                    _add_message(request, result)
                
                _save_game_to_session(request, game)
                game = _process_ai_turns(game, request)
                _save_game_to_session(request, game)
                
                request.session[TURN_REVEAL_KEY] = None
                
            except Exception as e:
                _add_message(request, f"❌ Could not play {card_input}: {e}")
                request.session[WILD_COLOR_PENDING] = None
            
            return redirect("uno_game")
        
        elif action == "select_wild_color":
            wild_color = request.POST.get("wild_color", "").strip().lower()
            pending_card = request.session.get(WILD_COLOR_PENDING)
            
            if pending_card and wild_color:
                try:
                    result = game.play(pending_card + " " + wild_color[0], wild_color)
                    _add_message(request, f"✅ Played {pending_card} with color {wild_color}")
                    
                    if len(current_player.hand) == 1 and not current_player.called:
                        uno_result = game.uno(current_player.id)
                        _add_message(request, uno_result)
                    
                    request.session[WILD_COLOR_PENDING] = None
                    _save_game_to_session(request, game)
                    
                    game = _process_ai_turns(game, request)
                    _save_game_to_session(request, game)
                    
                    request.session[TURN_REVEAL_KEY] = None
                    
                except Exception as e:
                    _add_message(request, f"❌ Error: {e}")
                    request.session[WILD_COLOR_PENDING] = None
            
            return redirect("uno_game")
         
        elif action == "draw":
            try:
                result = game.draw()
                _add_message(request, f"📥 {current_player.username} drew a card")
                
                _save_game_to_session(request, game)
                game = _process_ai_turns(game, request)
                _save_game_to_session(request, game)
                
                request.session[TURN_REVEAL_KEY] = None
                
            except Exception as e:
                _add_message(request, f"❌ Draw error: {e}")
            
            return redirect("uno_game")
        
        elif action == "uno":
            try:
                result = game.uno(current_player.id)
                _add_message(request, f"🎯 {current_player.username}: {result}")
                _save_game_to_session(request, game)
            except Exception as e:
                _add_message(request, f"❌ UNO error: {e}")
            
            return redirect("uno_game")
        
        elif action == "callout":
            try:
                result = game.callout(current_player.id)
                _add_message(request, f"📢 {current_player.username} called out: {result}")
                _save_game_to_session(request, game)
            except Exception as e:
                _add_message(request, f"❌ Callout error: {e}")
            
            return redirect("uno_game")
        
        elif action == "table":
            try:
                table_info = game.table()
                _add_message(request, f"📊 Table Status:\n{table_info}")
            except Exception as e:
                _add_message(request, f"❌ Table error: {e}")
            
            return redirect("uno_game")
        
        elif action == "quit":
            _clear_game(request)
            return redirect("uno_start")
    
    game = _load_game_from_session(request)
    if not game or not game.queue:
        return redirect("uno_start")
    
    current_player = game.get_curr_player()
    
    turn_revealed_for = request.session.get(TURN_REVEAL_KEY)
    reveal_hand = (turn_revealed_for == current_player.id)
    
    wild_pending = request.session.get(WILD_COLOR_PENDING)
    
    players_info = []
    for p in game.queue:
        players_info.append({
            "id": p.id,
            "username": p.username,
            "is_ai": p.is_ai,
            "card_count": len(p.hand),
            "called_uno": p.called,
            "is_current": (p.id == current_player.id)
        })
    
    for i, p in enumerate(game.finished, 1):
        players_info.append({
            "id": p.id,
            "username": f"{p.username} (Rank {i})",
            "is_ai": p.is_ai,
            "card_count": 0,
            "called_uno": False,
            "is_current": False,
            "finished": True
        })
    
    hand_cards = []
    if not current_player.is_ai and reveal_hand:
        for card in current_player.hand:
            hand_cards.append(_format_card_for_template(card))
    
    try:
        discard_top = _format_card_for_template(game.get_curr_card())
    except:
        discard_top = None
    
    discard_history = []
    if hasattr(game, "discard") and game.discard:
        for card in game.discard[-5:]:
            discard_history.append(_format_card_for_template(card))
        discard_history.reverse()
    
    messages = _get_messages(request, clear=True)
    
    context = {
        "game": game,
        "players": players_info,
        "current_player": {
            "id": current_player.id,
            "username": current_player.username,
            "is_ai": current_player.is_ai,
            "card_count": len(current_player.hand),
            "called_uno": current_player.called
        },
        "hand_revealed": reveal_hand,
        "hand_cards": hand_cards,
        "discard_top": discard_top,
        "discard_history": discard_history,
        "messages": messages,
        "wild_color_pending": wild_pending,
        "game_over": not game.queue,
        "direction": "normal",
        "deck_count": len(game.deck) if hasattr(game, "deck") else 0
    }
    
    return render(request, "gameplay/game.html", context) 