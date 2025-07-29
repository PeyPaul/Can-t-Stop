# train_rl_agent.py
# Script d'entraînement PPO pour l'agent RL sur Can't Stop

# import gym as gym
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environments.gym_env_v2 import CantStopGymEnv

def mask_fn(env):
    return env.get_action_mask()

if __name__ == "__main__":
    # Enregistrement de l'environnement custom
    gym.envs.registration.register(
        id="CantStop-v0",
        entry_point="environments.gym_env_v2:CantStopGymEnv",
    )

    # env = gym.make("CantStop-v0")
    env = CantStopGymEnv()
    env = ActionMasker(env, mask_fn)
    model = MaskablePPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=1)
    # Sauvegarde du modèle
    model.save("ppo_cantstop")
    print("Modèle PPO entraîné et sauvegardé.")

    # Test rapide
    obs, info = env.reset()
    for _ in range(10):
        action, _states = model.predict(obs)
        obs, reward, done, truncated, info = env.step(action)
        env.render()
        if done:
            obs, info = env.reset()
