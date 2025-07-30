# train_rl_agent.py
# Script d'entraînement PPO pour l'agent RL sur Can't Stop

# import gym as gym
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environments.gym_env_v2 import CantStopGymEnv
import sys

def mask_fn(env):
    return env.get_action_mask()

if __name__ == "__main__":
    for _ in range(1):
        # Enregistrement de l'environnement custom
        gym.envs.registration.register(
            id="CantStop-v0",
            entry_point="environments.gym_env_v2:CantStopGymEnv",
        )

        env = gym.make("CantStop-v0")
        env = CantStopGymEnv()
        env.reset()
        env = ActionMasker(env, mask_fn)
        model = MaskablePPO("MlpPolicy", env=env, verbose=1)
        model.learn(total_timesteps=1)
        
        # Sauvegarde du modèle
        print("Modèle PPO entraîné et sauvegardé.")

        
        
        obs, info = env.reset()
        done = False
        
        while not done:
            print("Action mask :", info["action_mask"])
            print("possibles :", info["possible"])
            print("Actions possibles :", [i for i, valid in enumerate(info["action_mask"]) if valid])
            action = model.predict(obs, deterministic=True, action_masks=info["action_mask"])[0]
            print(f"Action choisie : {action}")
            obs, reward, done, truncated, info = env.step(action)
            env.render()