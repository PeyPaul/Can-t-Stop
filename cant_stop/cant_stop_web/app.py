# app.py
import time
import uuid
from threading import Lock
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# import sys
# import os

# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# print("sys.path (PYTHONPATH):")
# for p in sys.path:
#     print("  ", p)

# print("\nContenu du dossier courant :", os.getcwd())
# for f in os.listdir(os.getcwd()):
#     print("  ", f)

# # Pour voir le contenu du dossier cant_stop (si accessible)
# cant_stop_path = os.path.join(os.getcwd(), "cant_stop")
# if os.path.isdir(cant_stop_path):
#     print("\nContenu du dossier cant_stop :")
#     for f in os.listdir(cant_stop_path):
#         print("  ", f)

# Adjust import path if your package name/folder is different.
# I used `cant_stop` because your posted files used that in main.py.
from cant_stop.game_engine import GameState, COLUMNS, COL_LENGTHS, MAX_TEMP_MARKERS
from cant_stop.players.random_ai import RandomAI
from cant_stop.players.heuristic_ai import HeuristicAI
# don't import your console HumanPlayer (it blocks for input). We'll use a tiny web-friendly human wrapper.

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# In-memory games store for development
games = {}
games_lock = Lock()

class WebHuman:
    """Lightweight human player object for the web UI.
    It mirrors attributes your AIs expect (progress, completed, name) but does not prompt.
    """
    def __init__(self, name='You'):
        self.name = name
        self.progress = {col: 0 for col in COLUMNS}
        self.completed = set()
        self.is_human = True

    # No choose_action() — human actions come via HTTP calls
    def should_continue(self, *args, **kwargs):
        # not used server-side for human, frontend decides and calls /stop
        return False

def init_player_for_web(kind, name):
    """Factory: kind in {'human','heuristic','random','rl' (not provided here)}"""
    if kind == 'human':
        return WebHuman(name)
    if kind == 'random':
        p = RandomAI(name)
    else:
        # default heuristic
        p = HeuristicAI(name)
    # Ensure AI/player objects have required attributes (progress/completed)
    if not hasattr(p, 'progress'):
        p.progress = {col: 0 for col in COLUMNS}
    if not hasattr(p, 'completed'):
        p.completed = set()
    # mark non-human
    if not hasattr(p, 'is_human'):
        p.is_human = False
    return p

class GameInstance:
    """Wrap a GameState with a lock + per-turn context"""
    def __init__(self, engine: GameState):
        self.engine = engine
        self.lock = Lock()
        self.last_active = time.time()
        # turn context used during the current player's turn (temp markers, dice, etc.)
        # Reset at the start of each player's turn.
        self.turn_context = {
            'temp_markers': {},
            'dice': None,
            'rolls_count': 0,
            'busted': False,
            'in_turn': False,   # true while human/AI turn underway
        }

    def start_new_turn_context(self):
        self.turn_context = {
            'temp_markers': {},
            'dice': None,
            'rolls_count': 0,
            'busted': False,
            'in_turn': True,
        }

    def clear_turn_context(self):
        self.turn_context = {
            'temp_markers': {},
            'dice': None,
            'rolls_count': 0,
            'busted': False,
            'in_turn': False,
        }

    def serialize(self):
        """Return a JSON-serializable view combining GameState.to_dict and turn_context"""
        gs_dict = self.engine.to_dict(temp_markers=self.turn_context['temp_markers'],
                                      dice=self.turn_context['dice'])
        gs_dict['turn_context'] = {
            'temp_markers': dict(self.turn_context['temp_markers']),
            'dice': list(self.turn_context['dice']) if self.turn_context['dice'] else None,
            'rolls_count': self.turn_context['rolls_count'],
            'busted': self.turn_context['busted'],
            'in_turn': self.turn_context['in_turn'],
        }
        return gs_dict

def create_game(opponent='heuristic'):
    # First player = human; second = chosen AI (or another human if you want)
    p1 = init_player_for_web('human', 'You')
    p2 = init_player_for_web(opponent, 'AI' if opponent != 'human' else 'Player 2')

    engine = GameState([p1, p2])
    gi = GameInstance(engine)
    # initial turn context: ready for first player's turn
    gi.start_new_turn_context()
    return gi

# --- HTTP endpoints ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_game', methods=['POST'])
def api_new_game():
    data = request.get_json() or {}
    opponent = data.get('opponent', 'heuristic')
    with games_lock:
        gi = create_game(opponent)
        game_id = str(uuid.uuid4())
        games[game_id] = gi
    return jsonify({'game_id': game_id, 'state': gi.serialize()})

@app.route('/api/game/<game_id>/state', methods=['GET'])
def api_state(game_id):
    gi = games.get(game_id)
    if not gi:
        return jsonify({'error': 'game not found'}), 404
    with gi.lock:
        gi.last_active = time.time()
        return jsonify(gi.serialize())

@app.route('/api/game/<game_id>/roll', methods=['POST'])
def api_roll(game_id):
    """Roll dice for the current player. Returns resulting state.
    For human: used by frontend when player clicks 'Roll'.
    For AI: server runs AI turns centrally (see run_ai_turns) so frontend generally doesn't call this for AI.
    """
    gi = games.get(game_id)
    if not gi:
        return jsonify({'error': 'game not found'}), 404

    with gi.lock:
        engine = gi.engine
        player = engine.get_current_player()

        # If new turn (or previous turn_context not active), start a fresh context
        if not gi.turn_context['in_turn'] or gi.turn_context['dice'] is None:
            gi.start_new_turn_context()

        # Only allow explicit roll for humans. For AIs we'll call run_ai_turns().
        if getattr(player, 'is_human', False) is not True:
            return jsonify({'error': 'Not human turn; call /run_ai or poll state instead.'}), 400

        dice = engine.roll_dice()
        gi.turn_context['dice'] = dice
        gi.turn_context['rolls_count'] += 1

        pairs = engine.get_pairs(dice)
        possible = engine.available_actions(pairs, gi.turn_context['temp_markers'], player)

        if not possible:
            # busted
            gi.turn_context['busted'] = True
            gi.turn_context['in_turn'] = False
            # human busts -> discard temp_markers and move to next player
            gi.clear_turn_context()
            engine.next_player()
            # After the bust, if next player is AI, run AI turns synchronously
            run_ai_turns(gi)
            gi.last_active = time.time()
            return jsonify({'state': gi.serialize(), 'message': 'bust'})

        # else return available actions for frontend to show
        gi.last_active = time.time()
        return jsonify({'state': gi.serialize(), 'available_actions': possible})

@app.route('/api/game/<game_id>/action', methods=['POST'])
def api_action(game_id):
    """Apply a chosen action for the current (human) player.
    Body: {"choice": [col] or [col1,col2]}
    After applying, the server DOES NOT automatically roll again; frontend should call /roll to roll or /stop to bank.
    """
    gi = games.get(game_id)
    if not gi:
        return jsonify({'error': 'game not found'}), 404
    body = request.get_json() or {}
    choice = body.get('choice')
    if choice is None:
        return jsonify({'error': 'no choice provided'}), 400

    with gi.lock:
        engine = gi.engine
        player = engine.get_current_player()
        if getattr(player, 'is_human', False) is not True:
            return jsonify({'error': 'Not human turn'}), 400

        # Apply the action to temp_markers
        try:
            gi.turn_context['temp_markers'] = engine.apply_action(tuple(choice), gi.turn_context['temp_markers'], player)
        except Exception as e:
            return jsonify({'error': f'apply_action error: {e}'}), 400

        gi.last_active = time.time()
        # After applying action, compute available moves for the current dice (player can choose another action or decide to stop)
        dice = gi.turn_context['dice']
        pairs = engine.get_pairs(dice) if dice is not None else []
        possible = engine.available_actions(pairs, gi.turn_context['temp_markers'], player)
        return jsonify({'state': gi.serialize(), 'available_actions': possible})

@app.route('/api/game/<game_id>/stop', methods=['POST'])
def api_stop(game_id):
    """Human decides to stop and bank temp_markers to permanent progress.
    After banking, server will run AI turns until it's human's turn again."""
    gi = games.get(game_id)
    if not gi:
        return jsonify({'error': 'game not found'}), 404

    with gi.lock:
        engine = gi.engine
        player = engine.get_current_player()
        if getattr(player, 'is_human', False) is not True:
            return jsonify({'error': 'Not human turn'}), 400

        # Bank the temp_markers into player's permanent progress & lock columns if completed
        for col, val in gi.turn_context['temp_markers'].items():
            player.progress[col] = val
            if player.progress[col] >= COL_LENGTHS[col]:
                engine.lock_column(col, player)

        # Clear turn context, check winner, advance player
        gi.clear_turn_context()
        winner = engine.check_winner()
        if winner:
            gi.last_active = time.time()
            return jsonify({'state': gi.serialize(), 'message': f'{winner.name} wins!'})

        engine.next_player()

        # If next player(s) are AI, run their turns synchronously and return resulting state
        run_ai_turns(gi)
        gi.last_active = time.time()
        return jsonify({'state': gi.serialize()})

def run_ai_turns(gi):
    """Run AI turns (possibly multiple sequential AI players) until it's a human's turn or game over.
    This function follows the logic in main.py: roll, enumerate possible, choose action, apply, decide continue/stop/bust.
    """
    engine = gi.engine

    while True:
        player = engine.get_current_player()
        if getattr(player, 'is_human', False):
            # stop AI loop and let human act
            gi.start_new_turn_context()
            break

        # Start AI turn context
        gi.start_new_turn_context()
        player_temp = gi.turn_context['temp_markers']
        busted = False

        while True:
            dice = engine.roll_dice()
            gi.turn_context['dice'] = dice
            gi.turn_context['rolls_count'] += 1
            pairs = engine.get_pairs(dice)
            possible = engine.available_actions(pairs, player_temp, player)

            if not possible:
                busted = True
                break

            # Ask AI to pick an action (HeuristicAI.choose_action expects: possible_actions, dice, pairs, temp_markers, game_state)
            if hasattr(player, 'choose_action'):
                action = player.choose_action(possible, dice, pairs, player_temp, engine)
            elif hasattr(player, 'act'):
                action = player.act(possible, dice, pairs, player_temp, engine)
            else:
                # No AI decision method
                busted = True
                break

            if action is None:
                busted = True
                break

            # Apply AI action
            player_temp = engine.apply_action(tuple(action), player_temp, player)
            gi.turn_context['temp_markers'] = player_temp

            # Decide whether AI continues
            try:
                cont = player.should_continue(temp_markers=player_temp, game_state=engine)
            except Exception:
                cont = False

            if not cont:
                # Bank progress
                for col, val in player_temp.items():
                    player.progress[col] = val
                    if player.progress[col] >= COL_LENGTHS[col]:
                        engine.lock_column(col, player)
                break
            # else continue rolling for this AI

        # AI finished (either busted or stopped). Clear temp if busted, or already banked if stopped.
        if busted:
            gi.clear_turn_context()
        else:
            gi.clear_turn_context()

        # Check for winner
        winner = engine.check_winner()
        if winner:
            return

        # Next player
        engine.next_player()
        # Continue loop: either next is AI (loop) or human (break out next iteration)
    # end run_ai_turns

if __name__ == '__main__':
    app.run(debug=True)
