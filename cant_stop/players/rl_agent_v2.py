import random
import numpy as np
from game_engine import GameState, COL_LENGTHS, COLUMNS, MAX_TEMP_MARKERS

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environments.gym_env_v3 import CantStopGymEnv
import sys
import os

model_dir = "models/PPO-1756132938"
model_path = os.path.join(model_dir, "ppo_cant_stop_5000000.zip")
        
class RLAgent_v2:
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


    def choose_action(self, possible_actions, dice, pairs, temp_markers, game_state):
        observation = self.get_observation(game_state, done=False, temp_markers=temp_markers, pairs=pairs)
        action_masks = self.get_action_mask(game_state, pairs, temp_markers)

        self.action = self.model.predict(observation, deterministic=True, action_masks=action_masks)[0]

        possible = self.get_possible_actions(game_state, pairs, game_state.get_current_player(), temp_markers)
        choice = possible[int(self.action)]
        return choice

    def should_continue(self, temp_markers=None, game_state=None):
        return self.action < 6

    def get_observation(self, gamestate, done=False, temp_markers={}, pairs=None): #peut être adapter les variables
        possible = self.get_possible_actions(gamestate, pairs, gamestate.get_current_player(), temp_markers)

        player_progress = np.array([COL_LENGTHS[col] - gamestate.players[0].progress[col] for col in COLUMNS], dtype=np.int32)  # 11 valeurs
        temp_markers_progress = np.zeros(len(COLUMNS), dtype=np.int32)  # 11 valeurs A CHANGER PROBABLEMENT
        num_temp_markers = np.array([3 - len(temp_markers)], dtype=np.int32)  # 1 valeur
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
                temp_markers_progress[idx] = COL_LENGTHS[idx+2] - temp_markers[idx+2]
            else :
                temp_markers_progress[idx] = COL_LENGTHS[idx+2] - gamestate.players[0].progress[idx+2]

        self.observations = np.concatenate([
            player_progress,
            temp_markers_progress,
            num_temp_markers,
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
        for i, (a,b) in enumerate(pairs):
            if not game_state.is_column_locked(a) and not game_state.is_column_locked(b):
                if a == b:
                    if a in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a]-1:
                            possible[2*i] =(a,b)
                    else:
                        if len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1:
                            possible[2*i] =(a,b)
                else:
                    if a in temp_markers and b in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a] and temp_markers[b] < COL_LENGTHS[b]:
                            possible[2*i] =(a,b)
                    elif a not in temp_markers and b not in temp_markers:
                        if len(temp_markers) + 1 <MAX_TEMP_MARKERS:
                            possible[2*i] =(a,b)
                    elif a in temp_markers and b not in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS:
                            possible[2*i] =(a,b)
                    else:
                        if temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS:
                            possible[2*i] =(a,b)
                            
            if (a,b) not in possible.values():
                for val in (a, b):
                    if not game_state.is_column_locked(val):
                        if val in temp_markers:
                            if temp_markers[val] < COL_LENGTHS[val]:
                                if val == a:
                                    possible[2*i] = (val,)
                                else:
                                    possible[2*i + 1] = (val,)
                        else:
                            if len(temp_markers) < MAX_TEMP_MARKERS:
                                if val == a:
                                    possible[2*i] = (val,)
                                else:
                                    possible[2*i + 1] = (val,)
                                    
        for i in range(6):
            if i in possible.keys():
                possible[i+6] = possible[i]
        return possible