import random
import numpy as np
from game_engine import GameState, COL_LENGTHS, COLUMNS, MAX_TEMP_MARKERS

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environments.gym_env_v2 import CantStopGymEnv
import sys
import os

model_dir = "models/PPO-1754059837"
model_path = os.path.join(model_dir, "ppo_cant_stop_3800000.zip")
        
class RLAgent:
    def __init__(self, name): # ça a l'air bon
        self.name = name
        self.progress = {}
        self.completed = set()
        def mask_fn(env):
            return env.get_action_mask() #je sens qu'il va y avoir un problème ici, mais on verra
        env = CantStopGymEnv()
        env.reset()
        env = ActionMasker(env, mask_fn)
        model = MaskablePPO("MlpPolicy", env=env, verbose=1)
        model.load(model_path)  # Charger le modèle pré-entraîné
        print(f"Modèle chargé depuis {model_path}")
        env.reset()
        self.model = model
        self.action = None
        self.observations = None


    def choose_action(self, possible_actions, dice, pairs, temp_markers, game_state): # AJOUTER L'ELEMENT TEMP_MARKERS
        observation = self.get_observation(game_state, done=False, temp_markers=temp_markers, pairs=pairs)
        action_masks = self.get_action_mask(game_state, pairs, temp_markers)

        self.action = self.model.predict(observation, deterministic=True, action_masks=action_masks)[0]

        possible = self.get_possible_actions(game_state, pairs, game_state.get_current_player(), temp_markers)
        choice = possible[int(self.action)]
        return choice

    def should_continue(self):
        return self.action < 6 
    
    def get_observation(self, gamestate, done=False, temp_markers={}, pairs=None): #peut être adapter les variables
        possible = self.get_possible_actions(gamestate, pairs, gamestate.get_current_player(), temp_markers)

        player_progress = np.array([COL_LENGTHS[col] - gamestate.players[0].progress[col] for col in COLUMNS], dtype=np.int32)  # 11 valeurs
        opponent_progress = np.array([COL_LENGTHS[col] - gamestate.players[1].progress[col] for col in COLUMNS], dtype=np.int32)  # 11 valeurs
        temp_markers_progress = np.zeros(len(COLUMNS), dtype=np.int32)  # 11 valeurs A CHANGER PROBABLEMENT
        player_completed = np.array([len(gamestate.players[0].completed)], dtype=np.int32) # 1 valeur
        opponent_completed = np.array([len(gamestate.players[1].completed)], dtype=np.int32) # 1 valeur
        locked_columns = np.array([1 if col in gamestate.locked_columns else 0 for col in COLUMNS], dtype=np.int32)  # 11 valeurs
        actions = np.full((12, 2), fill_value=-1, dtype=np.int32).flatten() # 12 paires possibles, 2 valeurs par paire

        for i in range(6):
            if i in possible.keys():
                possible[i+6] = possible[i]
        
        for i in range(12): #on remplis les actions à l'aide de possibles
            val = possible.get(i)
            if val is None:
                actions[2*i] = -1
                actions[2*i+1] = -1
            elif len(val) == 2:
                actions[2*i] = val[0]
                actions[2*i+1] = val[1]
            elif len(val) == 1:
                actions[2*i] = val[0]
                actions[2*i+1] = -1
        
        if done:
            actions[:] = -1
                
        for idx in range(len(COLUMNS)): #on update les marqueurs temporaires
            if idx+2 in temp_markers.keys():
                temp_markers_progress[idx] = temp_markers[idx+2]
        
        self.observations = np.concatenate([
            player_progress,
            opponent_progress,
            temp_markers_progress,
            player_completed,
            opponent_completed,
            locked_columns,
            actions
        ])
        return self.observations

    def get_action_mask(self, gamestate, pairs, temp_markers):
        possible = self.get_possible_actions(gamestate, pairs, gamestate.get_current_player(), temp_markers)
        action_mask = np.zeros(12, dtype=np.bool_)
        for i in range(6):
            if i in possible.keys():
                possible[i+6] = possible[i]
        for i in range(12):
            if possible.get(i) is not None:
                action_mask[i] = True
            else:
                action_mask[i] = False
        return action_mask

    def get_possible_actions(self, game_state, pairs, player, temp_markers): # à adapter
        possible = {}
        for i, (a, b) in enumerate(pairs):
            if not game_state.is_column_locked(a) and not game_state.is_column_locked(b):
                # Cas où on peut prendre deux fois la même colonne
                if a == b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a]-1) or (a not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1)):
                    possible[2*i] = (a, b) 
                # Si les deux colonnes sont déjà en cours de progression
                elif a != b and (a in temp_markers and temp_markers[a] < COL_LENGTHS[a]) and (b in temp_markers and temp_markers[b] < COL_LENGTHS[b]):
                    possible[2*i] = (a, b)
                # Si on a suffisamment de marqueurs temporaires
                elif a != b and len(temp_markers) + 1 < MAX_TEMP_MARKERS:
                    possible[2*i] = (a, b)
                # Vérification de la limite de marqueurs temporaires un à un
                elif a != b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS) or (b in temp_markers and temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS)):
                    possible[2*i] = (a, b)
            # Si on ne peut pas prendre les deux, on regarde si on peut prendre un seul
            if (a,b) not in possible.values():
                for val in (a, b):
                    if not game_state.is_column_locked(val) and ((val in temp_markers and temp_markers[val] < COL_LENGTHS[val]) or (val not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS)):
                        if val == a:
                            possible[2*i] = (val,)
                        else:
                            possible[2*i + 1] = (val,)
        for i in range(6):
            if i in possible.keys():
                possible[i+6] = possible[i]
        return possible