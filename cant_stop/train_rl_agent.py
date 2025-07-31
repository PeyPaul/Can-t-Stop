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
import os

model_dir = "models"
log_dir = "logs"

if not os.path.exists(model_dir):
    os.makedirs(model_dir)
    
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def mask_fn(env):
    return env.get_action_mask()

if __name__ == "__main__":
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
    model.save(os.path.join(model_dir, "ppo_cant_stop"))
    print("Modèle PPO entraîné et sauvegardé.")



    
    obs, info = env.reset()
    done = False
    
    while not done:
        action = model.predict(obs, deterministic=True, action_masks=info["action_mask"])[0]
        obs, reward, done, truncated, info = env.step(action)
        env.render()