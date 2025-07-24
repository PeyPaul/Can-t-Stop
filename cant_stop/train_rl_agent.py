# train_rl_agent.py
# Script d'entraînement PPO pour l'agent RL sur Can't Stop

import gym as gym
from stable_baselines3 import PPO
from environments.gym_env import CantStopGymEnv

if __name__ == "__main__":
    # Enregistrement de l'environnement custom
    gym.envs.registration.register(
        id="CantStop-v0",
        entry_point="environments.gym_env:CantStopGymEnv",
    )

    env = gym.make("CantStop-v0")
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=100_000)
    # Sauvegarde du modèle
    model.save("ppo_cantstop")
    print("Modèle PPO entraîné et sauvegardé.")

    # Test rapide
    obs = env.reset()
    for _ in range(10):
        action, _states = model.predict(obs)
        obs, reward, done, info = env.step(action)
        env.render()
        if done:
            obs = env.reset()
