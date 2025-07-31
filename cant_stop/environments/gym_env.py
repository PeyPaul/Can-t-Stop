# gym_env.py
# Interface RL (optionnel, squelette)


# import gym
# from gym import spaces
import gymnasium as gym
from gymnasium import spaces
import numpy as np
np.bool = np.bool_ # Cette ligne est très importante
from game_engine import GameState, COL_LENGTHS, COLUMNS

class CantStopGymEnv(gym.Env):
    """
    Environnement Gym pour Can't Stop (1 agent RL vs IA simple)
    """
    metadata = {"render.modes": ["human"]}

    def __init__(self):
        super().__init__()
        # Observation: progression du joueur RL + colonnes verrouillées
        self.observation_space = spaces.Box(low=0, high=13, shape=(len(COLUMNS) * 2,), dtype=np.int32)
        # Action: index de la paire ou colonne à choisir (max 6 possibilités)
        self.action_space = spaces.Discrete(6)
        self.players = None
        self.game_state = None
        self.current_pairs = None
        self.done = False

    def reset(self, seed=None, options=None, **kwargs):# ,*, seed=None, options=None
        from players.random_ai import RandomAI
        from cant_stop.players.rl_agent_training import RLAgent
        self.players = [RLAgent("RL"), RandomAI("Random")]
        for p in self.players:
            p.progress = {col: 0 for col in COLUMNS}
        self.game_state = GameState(self.players)
        self.done = False
        obs = self._get_obs()
        #info = {}
        return obs#, info

    def step(self, action):
        player = self.players[self.game_state.current_player_index]
        if player.name != "RL":
            raise Exception("Seul l'agent RL doit jouer via step() !")
        # Lancer les dés et générer les paires
        dice = self.game_state.roll_dice()
        pairs = self.game_state.get_pairs(dice)
        self.current_pairs = pairs
        possible = self._get_possible_actions(pairs, player)
        # Appliquer l'action choisi
        if action >= len(possible):
            # Action invalide : pénalité
            reward = -1
            done = True
            info = {}
            return self._get_obs(), reward, done, info
        choice = possible[action]
        for val in choice:
            if val not in player.progress:
                player.progress[val] = 0
            player.progress[val] += 1
            if player.progress[val] >= COL_LENGTHS[val]:
                self.game_state.lock_column(val, player)
        # Récompense : +1 par colonne complétée, +10 si victoire
        reward = sum([1 for col in choice if player.progress[col] >= COL_LENGTHS[col]])
        winner = self.game_state.check_winner()
        done = False
        if winner == player:
            reward += 10
            done = True
        # Tour suivant
        self.game_state.next_player()
        # L'IA random joue automatiquement
        if not done:
            self._play_random_turn()
        obs = self._get_obs()
        info = {}
        return obs, reward, done, info

    def render(self, mode="human"):
        from main import display_board
        display_board(self.players, self.game_state.board, self.game_state.locked_columns)

    def _get_obs(self):
        # Progression RL + colonnes verrouillées
        rl = self.players[0]
        progress = [rl.progress.get(col, 0) for col in COLUMNS]
        locked = [1 if col in self.game_state.locked_columns else 0 for col in COLUMNS]
        return np.array(progress + locked, dtype=np.int32)

    def _get_possible_actions(self, pairs, player):
        # Génère les actions possibles comme dans main.py
        temp_markers = {col: player.progress.get(col, 0) for col in COLUMNS}
        possible = []
        MAX_TEMP_MARKERS = 3
        for a, b in pairs:
            if not self.game_state.is_column_locked(a) and not self.game_state.is_column_locked(b):
                if a == b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a]-1) or (a not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1)):
                    possible.append((a,b))
                elif a != b and (a in temp_markers and temp_markers[a] < COL_LENGTHS[a]) and (b in temp_markers and temp_markers[b] < COL_LENGTHS[b]):
                    possible.append((a,b))
                elif a != b and len(temp_markers) + 1 < MAX_TEMP_MARKERS:
                    possible.append((a,b))
                elif a != b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS) or (b in temp_markers and temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS)):
                    possible.append((a,b))
            if (a,b) not in possible:
                for val in (a, b):
                    if not self.game_state.is_column_locked(val) and ((val in temp_markers and temp_markers[val] < COL_LENGTHS[val]) or (val not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS)):
                        possible.append((val,))
        return possible

    def _play_random_turn(self):
        # L'IA random joue automatiquement jusqu'à la fin de son tour
        player = self.players[self.game_state.current_player_index]
        while True:
            dice = self.game_state.roll_dice()
            pairs = self.game_state.get_pairs(dice)
            possible = self._get_possible_actions(pairs, player)
            if not possible:
                break
            choice = possible[0]
            for val in choice:
                if val not in player.progress:
                    player.progress[val] = 0
                player.progress[val] += 1
                if player.progress[val] >= COL_LENGTHS[val]:
                    self.game_state.lock_column(val, player)
            # Fin de tour random (75% de continuer)
            import random
            if random.random() > 0.75:
                break
        self.game_state.next_player()
