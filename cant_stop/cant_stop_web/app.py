# app.py
import time
import uuid
from threading import Lock
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Import your game engine and players here. Adjust names if different.
import game_engine
from players.human_player import HumanPlayer
from players.random_ai import RandomAI
from players.heuristic_ai import HeuristicAI

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# In-memory store of running games (good for development). Use Redis or DB in production.
games = {}
games_lock = Lock()

class GameInstance:
    """Wraps a game engine instance with a lock and a last-active timestamp."""
    def __init__(self, engine):
        self.engine = engine
        self.lock = Lock()
        self.last_active = time.time()
        
    def serialize(self):
        """Return a JSON-serializable representation of the engine's state.
        Tries several common method names and falls back to a minimal manual structure.
        """
        e = self.engine
        # Preferred: use an explicit serializer on your game engine
        if hasattr(e, 'to_dict'):
            return e.to_dict()
        if hasattr(e, 'get_state'):
            return e.get_state()

        # Try to build minimal useful state for the UI — adapt to your engine's fields
        state = {
        'players': [],
        'current_player_index': getattr(e, 'current_player_index', None),
        'game_over': getattr(e, 'game_over', False),
        }

        players = getattr(e, 'players', None)
        if players:
            for p in players:
                st = {
                'name': getattr(p, 'name', str(p)),
                'score': getattr(p, 'score', None),
                'is_human': getattr(p, 'is_human', False)
                }
                state['players'].append(st)

        # Board representation: try common names
        state['board'] = getattr(e, 'board', getattr(e, 'columns', None))
        state['dice'] = getattr(e, 'dice', None)
        # available actions: try engine-provided method
        if hasattr(e, 'available_actions'):
            try:
                state['available_actions'] = e.available_actions()
            except Exception:
                state['available_actions'] = []
        else:
            state['available_actions'] = []
        return state
    
    
def create_game(opponent='heuristic'):
    """Create a new game instance using your engine and player classes. Adapt as needed."""
    # Create players: first player = human
    human = HumanPlayer(name='You')
    if opponent == 'random':
        ai = RandomAI(name='Random AI')
    elif opponent == 'rl':
        # if you have RL agent class
        from players.rl_agent import RLAgent
        ai = RLAgent(name='RL Agent')
    else:
        ai = HeuristicAI(name='Heuristic AI')

    # Construct your game object. Replace `Game` with whatever your engine uses.
    engine = game_engine.Game([human, ai])
    return GameInstance(engine)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_game', methods=['POST'])
def api_new_game():
    data = request.get_json() or {}
    opponent = data.get('opponent', 'heuristic')
    gi = create_game(opponent)

    game_id = str(uuid.uuid4())
    with games_lock:
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
    
    
@app.route('/api/game/<game_id>/actions', methods=['GET'])
def api_actions(game_id):
    gi = games.get(game_id)
    if not gi:
        return jsonify({'error': 'game not found'}), 404
    with gi.lock:
        e = gi.engine
        if hasattr(e, 'available_actions'):
            actions = e.available_actions()
        else:
            # try to provide a meaningful fallback
            actions = []
        return jsonify({'actions': actions})
    
def run_ai_turns(gi):
    """Run AI moves synchronously until the current player is human or game over.
    This keeps the server simple: after a human action we call this and return the updated state.
    For long-running AIs, push to background workers (Celery) or use sockets.
    """
    engine = gi.engine
    while True:
        # Detect current player object using common names
        cur = None
        if hasattr(engine, 'current_player'):
            cur = engine.current_player
        elif hasattr(engine, 'current_player_index') and hasattr(engine, 'players'):
            idx = engine.current_player_index
            if 0 <= idx < len(engine.players):
                cur = engine.players[idx]

        if cur is None:
            break

        # Decide if this player is human
        is_human = getattr(cur, 'is_human', False) or getattr(cur, 'player_type', None) == 'human'
        if is_human:
            break

        # Ask AI for action(s). Adapt according to your AI API
        if hasattr(cur, 'act'):
            ai_choice = cur.act(engine)
        elif hasattr(cur, 'choose_action'):
            ai_choice = cur.choose_action(engine)
        elif hasattr(cur, 'make_move'):
            ai_choice = cur.make_move(engine)
        else:
            raise RuntimeError('AI player does not expose an act/choose_action/make_move method')

        if ai_choice is None:
            break
        if not isinstance(ai_choice, list):
            ai_choice = [ai_choice]

        for a in ai_choice:
            if hasattr(engine, 'apply_action'):
                engine.apply_action(a)
            elif hasattr(engine, 'step'):
                engine.step(a)
            else:
                raise RuntimeError('Game engine must expose apply_action or step to accept moves')

        # loop: if the AI still has the turn (or next is another AI), continue
        if getattr(engine, 'game_over', False):
            break
        
        
@app.route('/api/game/<game_id>/action', methods=['POST'])
def api_action(game_id):
    gi = games.get(game_id)
    if not gi:
        return jsonify({'error': 'game not found'}), 404
    body = request.get_json() or {}
    action = body.get('action')

    with gi.lock:
        engine = gi.engine
        # apply the action using common engine API names
        if action is None:
            return jsonify({'error': 'no action provided'}), 400
        try:
            if hasattr(engine, 'apply_action'):
                engine.apply_action(action)
            elif hasattr(engine, 'step'):
                engine.step(action)
            else:
                return jsonify({'error': 'game engine cannot accept actions (no apply_action/step)'}), 500

            # After human action, run AI turns synchronously until it's human's turn again (simple approach)
            run_ai_turns(gi)

        except Exception as e:
            return jsonify({'error': str(e)}), 400

        gi.last_active = time.time()
        return jsonify({'state': gi.serialize()})
    
if __name__ == '__main__':
    app.run(debug=True)