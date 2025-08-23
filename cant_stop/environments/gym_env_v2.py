import gymnasium as gym
from gymnasium import spaces
import numpy as np
np.bool = np.bool_ # Cette ligne est très importante
from game_engine import GameState, COL_LENGTHS, COLUMNS, MAX_TEMP_MARKERS
import sys

## Monkey patch
if "numpy._core" not in sys.modules:
    import numpy
    sys.modules["numpy._core"] = numpy

class CantStopGymEnv(gym.Env):
    """
    Environnement Gym pour Can't Stop (1 agent RL vs IA simple)
    """
    metadata = {"render.modes": ["human"]}

    def __init__(self):
        super(CantStopGymEnv, self).__init__()
        self.action_space = spaces.Discrete(12)
        # IL RESTE À FAIRE : définir l'espace d'observation
        obs_dim = 11 + 11 + 11 + 1 + 1 + 11 + 24
        self.observation_space = spaces.Box(low=-1, high=13, shape=(obs_dim,), dtype=np.int32)
        
        self.players = None
        self.game_state = None
        self.possible = None
        self.done = False
        self.temp_markers = {}
        self.reward = 0
        self.turn = 0
        self.observations = None
        self.info = None
        self.possible = {}
        
    def reset(self, seed=None, options=None, **kwargs):
        seed = kwargs.get('seed', None)
        options = kwargs.get('options', None)
        from players.random_ai import RandomAI
        from players.rl_agent_training import RLAgent
        self.done = False
        self.reward = 0
        self.players = [
        RLAgent("RL"),
        RandomAI("random")
        ]
        for p in self.players:
            p.progress = {col: 0 for col in COLUMNS}
        self.turn = 0
        self.game_state = GameState(self.players)
        self.game_state.locked_columns = set()
        
        self.temp_markers = {}
        player = self.game_state.get_current_player()
        dice = self.game_state.roll_dice() #on tire les dés pour le premier tour de RL
        pairs = self.game_state.get_pairs(dice)
        self.possible = self.get_possible_actions(pairs, player,self.temp_markers)

        self.observations = self.get_observation(self.possible, self.done, self.temp_markers)
        self.info = self.get_information(self.possible)
        return self.observations, self.info

    def step(self, action): # A FAIRE : IMPLEMENTER LE MASQUE DES ACTIONS
        player = self.game_state.get_current_player()
        
        #chasse aux bugs
        print(f"actions possibles: {self.possible}")

        if self.should_continue_RL(self, action):
            # on applique les choix de l'agent RL
            self.temp_markers = self.play_turn_RL(self.game_state, player, action)
            
        else:
            self.temp_markers = self.play_turn_RL(self.game_state, player, action)
            self.temp_markers = {}

            winner = self.game_state.check_winner()
            if winner: 
                self.done = True
                self.reward += 100 - self.turn
                
            self.game_state.next_player()
            player = self.game_state.get_current_player()
            self.play_turn(self.game_state, player, action) # on joue le tour de l'IA random
            self.temp_markers = {}
            
            winner = self.game_state.check_winner()
            if winner: 
                self.done = True
                self.reward += -10
                
            self.turn += 1
            self.reward += -5
            self.game_state.next_player()
            player = self.game_state.get_current_player()
            # print(f"\n--- Tour {self.turn} : {player.name} ---")

        # on tire à nouveau les dés
        dice = self.game_state.roll_dice()
        pairs = self.game_state.get_pairs(dice)
        if self.temp_markers == None: #ça fix un problème mais je ne sais pas à quoi c'est dû
            self.temp_markers = {}
        self.possible = self.get_possible_actions(pairs, player,self.temp_markers)

        #garde de sécurité pour la boucl infinie
        max_loop = 50
        loop = 0
        
        #chasse au bug
        print(f"player.progress: {player.progress}")
        print(f"temp_markers: {self.temp_markers}")
        print(f"COL_LENGTHS: {COL_LENGTHS}")
        #print(f"actions possibles: {self.possible}")
        assert all(player.progress[c] <= COL_LENGTHS[c] for c in COLUMNS), "BUG: overflow in player progress"
        assert all(v <= COL_LENGTHS[c] for c, v in self.temp_markers.items()), "BUG: overflow in temp_markers"

        while not self.possible: # on gere le bust de RL (il ne peut buster que ici)
            # print(f"{player.name} a busté !")
            
            loop += 1
            if loop > max_loop:
                print("Boucle infinie détectée, arrêt du jeu.")
                print(f"Progression temporaire : {self.temp_markers}")
                print(f"Actions possibles : {self.possible}")
                print(f"Tour : {self.turn}")
                print(f"Joueur courant : {player.name}")
                print(f"Reward : {self.reward}")
                self.render()
                sys.exit()
            self.reward += 0
            self.game_state.next_player()
            player = self.game_state.get_current_player()
            self.play_turn(self.game_state, player, action) # on joue le tour de l'IA random
            winner = self.game_state.check_winner()
            if winner: 
                self.done = True
                self.reward += -10
            self.turn += 1
            self.reward += -5
            self.game_state.next_player()
            player = self.game_state.get_current_player()
            # print(f"\n--- Tour {self.turn} : {player.name} ---")
            dice = self.game_state.roll_dice()
            pairs = self.game_state.get_pairs(dice)
            self.possible = self.get_possible_actions(pairs, player,self.temp_markers) 

        self.observations = self.get_observation(self.possible, self.done)
        
        self.info = self.get_information(self.possible)
        return self.observations, self.reward, self.done, False, self.info


    def render(self, mode="human"):
        from main import display_board
        display_board(self.players, self.game_state.board, self.game_state.locked_columns)


    def get_observation(self, possible, done=False, temp_markers={}): 
        player_progress = np.array([COL_LENGTHS[col] - self.players[0].progress[col] for col in COLUMNS], dtype=np.int32)  # 11 valeurs
        opponent_progress = np.array([COL_LENGTHS[col] - self.players[1].progress[col] for col in COLUMNS], dtype=np.int32)  # 11 valeurs
        temp_markers_progress = np.zeros(len(COLUMNS), dtype=np.int32)  # 11 valeurs A CHANGER PROBABLEMENT
        player_completed = np.array([len(self.players[0].completed)], dtype=np.int32) # 1 valeur
        opponent_completed = np.array([len(self.players[1].completed)], dtype=np.int32) # 1 valeur
        locked_columns = np.array([1 if col in self.game_state.locked_columns else 0 for col in COLUMNS], dtype=np.int32)  # 11 valeurs
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
            if idx+2 in self.temp_markers.keys():
                temp_markers_progress[idx] = self.temp_markers[idx+2]

        # choses qui pourraient être ajoutées :
        # - nombre de marqueurs temporaires disponibles
        # - les dés lancés (4 valeurs)
        # - la taille des colonnes (11 valeurs)
        # - le masque des actions
        
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
    
    def get_information(self, possible):
        action_mask = np.zeros(12, dtype=np.bool_)
        for i in range(6):
            if i in possible.keys():
                possible[i+6] = possible[i]
        for i in range(12):
            if possible.get(i) is not None:
                action_mask[i] = True
            else:
                action_mask[i] = False
        return {
            "action_mask": action_mask,
            "possible": possible,
            "turn": self.turn,
            "temp_markers": self.temp_markers,
            "player": self.game_state.get_current_player().name,
            "reward": self.reward
        }
    
    def get_possible_actions(self, pairs, player,temp_markers):
        # possible = {}
        # for i, (a, b) in enumerate(pairs):
        #     if not self.game_state.is_column_locked(a) and not self.game_state.is_column_locked(b):
        #         # Cas où on peut prendre deux fois la même colonne
        #         if a == b and ((a in self.temp_markers and self.temp_markers[a] < COL_LENGTHS[a]-1) or (a not in self.temp_markers and len(self.temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1)):
        #             possible[2*i] = (a, b) 
        #         # Si les deux colonnes sont déjà en cours de progression
        #         elif a != b and (a in self.temp_markers and self.temp_markers[a] < COL_LENGTHS[a]) and (b in self.temp_markers and self.temp_markers[b] < COL_LENGTHS[b]):
        #             possible[2*i] = (a, b)
        #         # Si on a suffisamment de marqueurs temporaires
        #         elif a != b and len(self.temp_markers) + 1 < MAX_TEMP_MARKERS:
        #             possible[2*i] = (a, b)
        #         # Vérification de la limite de marqueurs temporaires un à un
        #         elif a != b and ((a in self.temp_markers and self.temp_markers[a] < COL_LENGTHS[a] and len(self.temp_markers) < MAX_TEMP_MARKERS) or (b in self.temp_markers and self.temp_markers[b] < COL_LENGTHS[b] and len(self.temp_markers) < MAX_TEMP_MARKERS)):
        #             possible[2*i] = (a, b)
        #             print("ça passe par ici, j'en suis quasiment sûr !!!!!!!! il faudrait inverser les deux dernières conditions pour que tous soit juste, non en vrai il faudrait faire bien plus que cela. On a des problèmes")
        #     # Si on ne peut pas prendre les deux, on regarde si on peut prendre un seul
        #     if (a,b) not in possible.values():
        #         for val in (a, b):
        #             if not self.game_state.is_column_locked(val) and ((val in self.temp_markers and self.temp_markers[val] < COL_LENGTHS[val]) or (val not in self.temp_markers and len(self.temp_markers) < MAX_TEMP_MARKERS)):
        #                 if val == a:
        #                     possible[2*i] = (val,)
        #                 else:
        #                     possible[2*i + 1] = (val,)
                            
                            
        possible = {}
        for i, (a,b) in enumerate(pairs):
            if not self.game_state.is_column_locked(a) and not self.game_state.is_column_locked(b):
                if a == b:
                    if a in self.temp_markers:
                        if self.temp_markers[a] < COL_LENGTHS[a]-1:
                            possible[2*i] =(a,b)
                    else:
                        if len(self.temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1:
                            possible[2*i] =(a,b)
                else:
                    if a in self.temp_markers and b in self.temp_markers:
                        if self.temp_markers[a] < COL_LENGTHS[a] and self.temp_markers[b] < COL_LENGTHS[b]:
                            possible[2*i] =(a,b)
                    elif a not in self.temp_markers and b not in self.temp_markers:
                        if len(self.temp_markers) + 1 <MAX_TEMP_MARKERS:
                            possible[2*i] =(a,b)
                    elif a in self.temp_markers and b not in self.temp_markers:
                        if self.temp_markers[a] < COL_LENGTHS[a] and len(self.temp_markers) < MAX_TEMP_MARKERS:
                            possible[2*i] =(a,b)
                    else:
                        if self.temp_markers[b] < COL_LENGTHS[b] and len(self.temp_markers) < MAX_TEMP_MARKERS:
                            possible[2*i] =(a,b)
                            
            if (a,b) not in possible.values():
                for val in (a, b):
                    if not self.game_state.is_column_locked(val):
                        if val in self.temp_markers:
                            if self.temp_markers[val] < COL_LENGTHS[val]:
                                if val == a:
                                    possible[2*i] = (val,)
                                else:
                                    possible[2*i + 1] = (val,)
                        else:
                            if len(self.temp_markers) < MAX_TEMP_MARKERS:
                                if val == a:
                                    possible[2*i] = (val,)
                                else:
                                    possible[2*i + 1] = (val,)

        return possible

    def play_turn_RL(self, game_state, player, action):
        choice = self.choose_action_RL(player, self.possible, action)
        for val in choice:
            if val not in self.temp_markers:
                self.temp_markers[val] = player.progress.get(val, 0)
            self.temp_markers[val] += 1

        if not self.should_continue_RL(player, action):
            # print(f"{player.name} s'arrête et sécurise ses progrès.")
            for col, val in self.temp_markers.items():
                self.reward += (val - player.progress[col]) * 1
                player.progress[col] = val
                if player.progress[col] >= COL_LENGTHS[col]:
                    game_state.lock_column(col, player)
                    if player.name == "RL":
                        self.reward += 5
        return self.temp_markers
    
    def play_turn(self, game_state, player, action): #on peut améliorer cette fonction car l'agent RL ne joue pas ici
        self.temp_markers = {}
        busted = False
        #print(f"\n--- Tour {self.turn} : {player.name} ---")
        while True:
            dice = game_state.roll_dice()
            pairs = game_state.get_pairs(dice)
            possible = self.get_possible_actions(pairs, player,self.temp_markers)

            if possible:
                choice = self.choose_action_random(player, possible, dice, pairs)
                # print(f"{player.name} a choisi la paire {choice}")
                for val in choice:
                    if val not in self.temp_markers:
                        self.temp_markers[val] = player.progress.get(val, 0)
                    self.temp_markers[val] += 1
            else:
                busted = True
                # print(f"{player.name} a busté!")
                #sys.exit()
                break
            # print(f"Progression temporaire : {self.temp_markers}")
            # Vérification de la décision de continuer ou non
            if self.should_continue_random(player):
                continue
            else:
                # print(f"{player.name} s'arrête et sécurise ses progrès.")
                break
        if not busted:
            for col, val in self.temp_markers.items():
                player.progress[col] = val
                if player.progress[col] >= COL_LENGTHS[col]:
                    game_state.lock_column(col, player)
                    # self.reward += -2
        return self.reward

    def choose_action_RL(self, player, possible, action):
        # Implémentation de la logique de choix d'action pour l'agent RL
        for i in range(6):
            if i in possible.keys():
                possible[i+6] = possible[i]
        
        action = int(action) # TEST TEST TEST

        choice = possible[action+0]
        return choice
        
    def choose_action_random(self, player, possible, dice, pairs):
        # Implémentation de la logique de choix d'action pour l'IA random
        choice = player.choose_action(list(possible.values()), dice, pairs)
        return choice
    
    def should_continue_RL(self, player, action):
        if action >= 6:
            return False
        return True
    
    def should_continue_random(self, player):
        return player.should_continue()
    
    def get_action_mask(self):
        """
        Méthode requise par ActionMasker wrapper pour l'action masking.
        Retourne le masque d'actions valides.
        """
        if hasattr(self, 'info') and self.info is not None and 'action_mask' in self.info:
            return self.info['action_mask']
        else:
            # Fallback: toutes les actions sont valides si pas d'info disponible
            return np.ones(12, dtype=np.bool_)