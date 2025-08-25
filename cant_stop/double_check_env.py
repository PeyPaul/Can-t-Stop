import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environments.gym_env_v3 import CantStopGymEnv
import sys
import os
import time

total_timesteps = 1

def mask_fn(env):
    return env.get_action_mask()

if __name__ == "__main__":
    # Enregistrement de l'environnement custom
    gym.envs.registration.register(
        id="CantStop-v0",
        entry_point="environments.gym_env_v3:CantStopGymEnv"
    )

    #env = gym.make("CantStop-v0")
    env = CantStopGymEnv()
    env.reset()
    env = ActionMasker(env, mask_fn)
    model = MaskablePPO("MlpPolicy", env=env, verbose=1)
    #model.learn(total_timesteps=total_timesteps)

    print("Modèle PPO entraîné.")

    
    obs, info = env.reset()
    done = False
    
    while not done:
        print(f"--Tour {info['turn']} : {info['player']} ---")
        env.render()
        
        action = model.predict(obs, deterministic=True, action_masks=info["action_mask"])[0]
        
        print(f"Action prise: {action}")
        print(f"Action possible: {info['possible']}")
        print(f"action masquée: {info['action_mask']}")
        print(f"Marqueurs temporaires: {info['temp_markers']}")
        obs, reward, done, truncated, info = env.step(action)
        print(f"Reward: {info['reward']}")
        
        env.render()
        
        
        
        
        


        