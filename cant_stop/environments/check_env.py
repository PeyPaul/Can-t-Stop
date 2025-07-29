from stable_baselines3.common.env_checker import check_env
from sb3_contrib.common.env_checker import check_env
from environments.gym_env_v2 import CantStopGymEnv

print("Vérification de l'environnement CantStopGymEnv...")

env = CantStopGymEnv()
print("Environnement créé avec succès.")
# It will check your custom environment and output additional warnings if needed
check_env(env)