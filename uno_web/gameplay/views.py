import pickle
import base64
import time
import json

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse

from gameplay.engine.game import UnoGame
from gameplay.engine import card as card_module
from gameplay.engine import player as player_module
from gameplay.engine.constants import COLOR_ALIASES, COLOR_SYMBOLS

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
    request.session[MESSAGES_KEY] = messages[-20:]  # Keep only last 20 messages
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
    
    # Handle wild cards
    is_wild = getattr(card, "wild", False) or getattr(card, "color", "") == ""
    color = getattr(card, "color", None) or ""
    card_id = getattr(card, "id", "")
    
    # Get display text
    if is_wild and not color:
        display = card_id
        color_name = "Choose Color"
        symbol = "★"
    elif is_wild:
        display = card_id
        color_name = card.get_color_name() if hasattr(card, 'get_color_name') else "Wild"
        symbol = "★"
    else:
        display = f"{color} {card_id}" if color else card_id
        color_name = card.get_color_name() if hasattr(card, 'get_color_name') else ""
        symbol = COLOR_SYMBOLS.get(color, "?")
    
    # Format the card_str for form submission
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
        
        # AI makes decision
        play_cmd, wild_color = cp.select_card_to_play(game)
        
        if play_cmd.startswith("play"):
            # Extract the card to play
            payload = play_cmd[5:] if len(play_cmd) > 5 else ""
            
            try:
                # Try to play the card
                if wild_color:
                    res = game.play(payload, wild_color)
                    messages_added.append(f"{cp.username} played {payload} and chose {wild_color}")
                else:
                    res = game.play(payload)
                    messages_added.append(f"{cp.username} played {payload}")
                
                # Auto-call UNO if needed
                if len(cp.hand) == 1 and not cp.called:
                    uno_result = game.uno(cp.id)
                    messages_added.append(f"{cp.username}: {uno_result}")
                    
                # Check if AI won
                if cp.finished:
                    messages_added.append(f"🎉 {cp.username} finished in rank {len(game.finished)}!")
                    
            except Exception as e:
                messages_added.append(f"AI play error: {e}")
                # Fallback to draw
                try:
                    res = game.draw()
                    messages_added.append(f"{cp.username} drew a card")
                except:
                    pass
        else:
            # AI chose to draw
            try:
                res = game.draw()
                messages_added.append(f"{cp.username} drew a card")
            except Exception as e:
                messages_added.append(f"AI draw error: {e}")
        
        # Check if game ended
        if not game.queue:
            break
    
    # Save all messages
    for msg in messages_added:
        _add_message(request, msg)
    
    return game


@require_http_methods(["GET", "POST"])
def start_game_view(request):
    """Create a new game from form input."""
    if request.method == "POST":
        # Parse human players
        try:
            human_count = int(request.POST.get("human_count", "1"))
            human_count = max(1, min(4, human_count))  # Clamp between 1-4
        except ValueError:
            human_count = 1
        
        names = []
        for i in range(1, human_count + 1):
            name = request.POST.get(f"human_name_{i}", "").strip()
            if name:
                names.append(name)
            else:
                names.append(f"Player{i}")
        
        # Parse AI players
        try:
            ai_count = int(request.POST.get("ai_count", "0"))
            ai_count = max(0, min(5, ai_count))  # Clamp between 0-5
        except ValueError:
            ai_count = 0
        
        # Ensure at least 2 total players
        if len(names) + ai_count < 2:
            return render(request, "gameplay/start.html", {
                "error": "Need at least 2 players to start a game!"
            })
        
        # Create and start game
        game = UnoGame()
        
        # Add human players
        for name in names:
            game.add_player(name, is_ai=False)
        
        # Add AI players
        for i in range(ai_count):
            game.add_player(f"AI-{i+1}", is_ai=True)
        
        # Start the game
        try:
            game.start()
            _save_game_to_session(request, game)
            request.session[TURN_REVEAL_KEY] = None
            request.session[WILD_COLOR_PENDING] = False
            _add_message(request, f"🎮 Game started! {game.get_curr_player().username} goes first.")
            
            # Process AI turns if AI goes first
            if game.get_curr_player().is_ai:
                game = _process_ai_turns(game, request)
                _save_game_to_session(request, game)
            
            return redirect("uno_game")
        except Exception as e:
            return render(request, "gameplay/start.html", {
                "error": f"Failed to start game: {e}"
            })
    
    # GET - show start form
    return render(request, "gameplay/start.html", {})


@require_http_methods(["GET", "POST"])
def game_view(request):
    """Main game view - handles all game actions."""
    game: UnoGame = _load_game_from_session(request)
    if not game:
        return redirect("uno_start")
    
    # Check if game ended
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
        
        # Handle revealing hand for pass-and-play
        if action == "start_turn":
            request.session[TURN_REVEAL_KEY] = current_player.id
            request.session.modified = True
            _add_message(request, f"📋 {current_player.username}'s turn revealed")
            return redirect("uno_game")
        
        # Handle ending turn (hiding hand) for pass-and-play
        elif action == "end_turn":
            request.session[TURN_REVEAL_KEY] = None
            request.session.modified = True
            _add_message(request, f"✅ Turn hidden. Pass device to next player.")
            return redirect("uno_game")
        
        # Handle playing a card
        elif action == "play":
            card_input = request.POST.get("card_input", "").strip()
            
            # Check if this is a wild card needing color selection
            is_wild_card = any(wild in card_input.upper() for wild in ["WILD+4", "WILD"])
            
            if is_wild_card and not request.session.get(WILD_COLOR_PENDING):
                # Mark that we need color selection
                request.session[WILD_COLOR_PENDING] = card_input
                request.session.modified = True
                return redirect("uno_game")
            
            # Get wild color if provided
            wild_color = request.POST.get("wild_color", "").strip().lower() if is_wild_card else None
            
            try:
                # Attempt to play the card
                if wild_color:
                    print("here for something")
                    result = game.play(card_input)
                    _add_message(request, f"✅ {current_player.username} played {card_input} and chose {wild_color}")
                else:
                    result = game.play(card_input)
                    _add_message(request, f"✅ {current_player.username} played {card_input}")
                
                # Clear wild color pending
                request.session[WILD_COLOR_PENDING] = None
                
                # Check for error in result
                if "cannot play this card" in result.lower() or "not found in hand" in result.lower():
                    _add_message(request, f"❌ {result}")
                    return redirect("uno_game")
                
                # Auto-call UNO if down to 1 card
                if len(current_player.hand) == 1 and not current_player.called:
                    uno_result = game.uno(current_player.id)
                    _add_message(request, f"🎯 {current_player.username}: {uno_result}")
                
                # Check if player won
                if current_player.finished:
                    _add_message(request, f"🎉 {current_player.username} finished in rank {len(game.finished)}!")
                
                # Process any additional info from result
                if result and not any(x in result.lower() for x in ["cannot play", "not found"]):
                    _add_message(request, result)
                
                # Save game and process AI turns
                _save_game_to_session(request, game)
                game = _process_ai_turns(game, request)
                _save_game_to_session(request, game)
                
                # Hide hand after playing
                request.session[TURN_REVEAL_KEY] = None
                
            except Exception as e:
                _add_message(request, f"❌ Could not play {card_input}: {e}")
                request.session[WILD_COLOR_PENDING] = None
            
            return redirect("uno_game")
        
        # Handle wild color selection
        elif action == "select_wild_color":
            wild_color = request.POST.get("wild_color", "").strip().lower()
            pending_card = request.session.get(WILD_COLOR_PENDING)
            
            if pending_card and wild_color:
                try:
                    result = game.play(pending_card + " " + wild_color[0], wild_color)
                    _add_message(request, f"✅ Played {pending_card} with color {wild_color}")
                    
                    # Auto-UNO if needed
                    if len(current_player.hand) == 1 and not current_player.called:
                        uno_result = game.uno(current_player.id)
                        _add_message(request, uno_result)
                    
                    # Clear pending and save
                    request.session[WILD_COLOR_PENDING] = None
                    _save_game_to_session(request, game)
                    
                    # Process AI turns
                    game = _process_ai_turns(game, request)
                    _save_game_to_session(request, game)
                    
                    # Hide hand
                    request.session[TURN_REVEAL_KEY] = None
                    
                except Exception as e:
                    _add_message(request, f"❌ Error: {e}")
                    request.session[WILD_COLOR_PENDING] = None
            
            return redirect("uno_game")
        
        # Handle drawing a card
        elif action == "draw":
            try:
                result = game.draw()
                _add_message(request, f"📥 {current_player.username} drew a card")
                
                # Save and process AI turns
                _save_game_to_session(request, game)
                game = _process_ai_turns(game, request)
                _save_game_to_session(request, game)
                
                # Hide hand after draw
                request.session[TURN_REVEAL_KEY] = None
                
            except Exception as e:
                _add_message(request, f"❌ Draw error: {e}")
            
            return redirect("uno_game")
        
        # Handle calling UNO
        elif action == "uno":
            try:
                result = game.uno(current_player.id)
                _add_message(request, f"🎯 {current_player.username}: {result}")
                _save_game_to_session(request, game)
            except Exception as e:
                _add_message(request, f"❌ UNO error: {e}")
            
            return redirect("uno_game")
        
        # Handle callout
        elif action == "callout":
            try:
                result = game.callout(current_player.id)
                _add_message(request, f"📢 {current_player.username} called out: {result}")
                _save_game_to_session(request, game)
            except Exception as e:
                _add_message(request, f"❌ Callout error: {e}")
            
            return redirect("uno_game")
        
        # Handle showing table status
        elif action == "table":
            try:
                table_info = game.table()
                _add_message(request, f"📊 Table Status:\n{table_info}")
            except Exception as e:
                _add_message(request, f"❌ Table error: {e}")
            
            return redirect("uno_game")
        
        # Handle quitting game
        elif action == "quit":
            _clear_game(request)
            return redirect("uno_start")
    
    # GET request - prepare context for rendering
    
    # Reload game in case it changed
    game = _load_game_from_session(request)
    if not game or not game.queue:
        return redirect("uno_start")
    
    current_player = game.get_curr_player()
    
    # Check if hand should be revealed
    turn_revealed_for = request.session.get(TURN_REVEAL_KEY)
    reveal_hand = (turn_revealed_for == current_player.id)
    
    # Check if waiting for wild color selection
    wild_pending = request.session.get(WILD_COLOR_PENDING)
    
    # Prepare players info
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
    
    # Add finished players
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
    
    # Prepare hand cards if revealed
    hand_cards = []
    if not current_player.is_ai and reveal_hand:
        for card in current_player.hand:
            hand_cards.append(_format_card_for_template(card))
    
    # Get top discard card
    try:
        discard_top = _format_card_for_template(game.get_curr_card())
    except:
        discard_top = None
    
    # Get discard history (last 5 cards)
    discard_history = []
    if hasattr(game, "discard") and game.discard:
        for card in game.discard[-5:]:
            discard_history.append(_format_card_for_template(card))
        discard_history.reverse()
    
    # Get messages
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