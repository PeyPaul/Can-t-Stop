# from environments.gym_env_v2 import CantStopGymEnv 

# # On peut utiliser cant_stop.environments.gym_env comme chemin avec la commande : python -m cant_stop.environments.double_check_env

# print("Vérification de l'environnement CantStopGymEnv...")

# env = CantStopGymEnv()
# episodes = 50

# for episode in range(episodes):
#     state = env.reset()
#     done = False
#     while not done:
#         random_action = env.action_space.sample()
#         print(f"Episode {episode + 1}, Action choisie: {random_action}")
#         obs, reward, done, info = env.step(random_action)
#         print(f'reward: {reward}')


from environments.gym_env_v2 import CantStopGymEnv

env = CantStopGymEnv()
obs, info = env.reset()

# Test avec une action valide
valid_actions = [i for i, valid in enumerate(info["action_mask"]) if valid]
if valid_actions:
    action = valid_actions[0]
    obs, reward, done, truncated, info = env.step(action)
    print("Test réussi !")