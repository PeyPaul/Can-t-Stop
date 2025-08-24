## Callback de watchdog

from stable_baselines3.common.callbacks import BaseCallback
import time
import numpy as np

class WatchdogCallback(BaseCallback):
    def __init__(self, max_silence_sec=1200, verbose=1):
        super().__init__(verbose)
        self.max_silence_sec = max_silence_sec
        self.last_update = time.time()
        self.last_steps = 0

    def _on_step(self) -> bool:
        # self.num_timesteps = steps totaux vus par SB3
        if self.num_timesteps > self.last_steps:
            self.last_steps = self.num_timesteps
            self.last_update = time.time()
        else:
            if time.time() - self.last_update > self.max_silence_sec:
                print(f"[WATCHDOG] Freeze suspecté à {self.num_timesteps} steps. Abort.")
                return False  # stoppe l'entraînement proprement
        if self.n_calls % 10000 == 0:
            print(f"[HB] {self.num_timesteps} steps...")
        return True
    
class EpisodeTurnMaxCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(EpisodeTurnMaxCallback, self).__init__(verbose)
        self.episode_turns = []

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", [])

        for info, done in zip(infos, dones):
            if "turn" in info:
                self.episode_turns.append(info["turn"])

            # Si un épisode est terminé → calcul et log
            if done and len(self.episode_turns) > 0:
                max_turn = np.max(self.episode_turns)
                self.logger.record("custom/max_turn_per_episode", max_turn)
                if self.verbose > 0:
                    print(f"[EpisodeTurnMaxCallback] Max turn for episode: {max_turn}")
                self.episode_turns = []  # reset pour le prochain épisode

        return True
    

# import gym as gym
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environments.gym_env_v2 import CantStopGymEnv
import sys
import os
import time

model_dir = f"models/PPO-{int(time.time())}"
log_dir = f"logs/PPO-{int(time.time())}"
total_timesteps = 1000000

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
        entry_point="environments.gym_env_v2:CantStopGymEnv"
    )

    #env = gym.make("CantStop-v0")
    env = CantStopGymEnv()
    env.reset()
    env = ActionMasker(env, mask_fn)
    model = MaskablePPO("MlpPolicy", env=env, verbose=1, tensorboard_log=log_dir)
    callback = [WatchdogCallback(max_silence_sec=1200), EpisodeTurnMaxCallback(verbose=1)]
    for i in range(1, 20):
        model.learn(total_timesteps=total_timesteps, reset_num_timesteps=False, tb_log_name="ppo_cant_stop", callback=callback, progress_bar=True)
        model.save(os.path.join(model_dir, f"ppo_cant_stop_{total_timesteps * i}"))
        print("Modèle PPO entraîné et sauvegardé.")
        
    env.close()



    
    # obs, info = env.reset()
    # done = False
    
    # while not done:
    #     action = model.predict(obs, deterministic=True, action_masks=info["action_mask"])[0]
    #     obs, reward, done, truncated, info = env.step(action)
    #     env.render()