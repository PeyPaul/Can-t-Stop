import random
from collections import Counter
from itertools import product

from cant_stop.game_engine import COL_LENGTHS, COLUMNS, MAX_TEMP_MARKERS

# Fréquences 2d6 (non normalisées) pour pondérer la "stabilité" des colonnes
PAIR_FREQ = {2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:5, 9:4, 10:3, 11:2, 12:1}
PAIR_FREQ_MAX = 6  # pour normaliser dans [0,1]

class HeuristicAI:
    def __init__(
        self,
        name,
        k_risk=1.0,          # Paramètre K pour stop/continue
        alpha_future=0.5,    # Poids du p_continue_next dans le score d'action
        eps_explore=0.05     # Petite exploration pour éviter l'ultra-déterminisme
    ):
        self.name = name
        self.progress = {}
        self.completed = set()
        self.k_risk = k_risk
        self.alpha_future = alpha_future
        self.eps_explore = eps_explore

        # Pré-calculer tous les tirages possibles de 4 dés (1296)
        self._all_rolls = list(product(range(1,7), repeat=4))

    # ---------- Interface requise par ton moteur ----------
    def choose_action(self, possible_actions, dice, pairs, temp_markers=None, game_state=None):
        """
        Sélectionne la meilleure action parmi possible_actions en scorant
        avec :
          - proximité de complétion
          - fréquence 2d6 (stabilité future)
          - probabilité de pouvoir continuer au prochain lancer après cette action
          - bonus double
        """
        if not possible_actions:
            return None

        # Exploration epsilon
        if random.random() < self.eps_explore and len(possible_actions) > 1:
            random.shuffle(possible_actions)
            return possible_actions[0]

        best_action = None
        best_score = float('-inf')

        for action in possible_actions:
            score = self._score_action(action, temp_markers, game_state)
            #print(f"Score pour l'action {action}: {score}")
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def should_continue(self, temp_markers=None, game_state=None):
        """
        Décide de continuer ou s'arrêter à partir de l'état courant.
        Règle : s'arrêter si p_bust >= bankable_steps / (bankable_steps + K)
        """
        # Défense si l'appel ne fournit pas de contexte
        if temp_markers is None or game_state is None:
            # Fallback prudent si on n'a pas d'infos (ne devrait pas arriver via main.py)
            return random.random() < 0.5

        p_continue = self._prob_can_continue(temp_markers, game_state)
        p_bust = 1.0 - p_continue
        bankable_steps = sum(
            max(0, temp_markers.get(col, 0) - self.progress.get(col, 0))
            for col in temp_markers.keys()
        )

        # Si aucun gain provisoire, on peut être plus agressif
        if bankable_steps <= 0:
            return True

        threshold = self.k_risk / (bankable_steps + self.k_risk)
        #print(f"p_bust: {p_bust}, threshold: {threshold}, décision: {p_bust < threshold}")
        return p_bust < threshold

    # ---------- Heuristiques internes ----------
    def _score_action(self, action, temp_markers, game_state):
        """
        Score d'une action candidate.
        """
        # Simuler l'effet immédiat sur les marqueurs temporaires
        tm = dict(temp_markers) if temp_markers is not None else {}
        immediate_score = 0.0
        stability_bonus = 0.0

        # Compter si c'est un double (a == b) pour intensifier la proximité
        is_double = (len(action) == 2 and action[0] == action[1])

        # Appliquer les pas
        for v in action:
            # niveau actuel (temp si présent sinon permanent)
            base = tm.get(v, self.progress.get(v, 0))
            nxt = base + 1
            tm[v] = nxt

            remaining_after = max(1, COL_LENGTHS[v] - nxt)  # éviter division par 0, mais proche de complétion -> gros score
            proximity = 1.0 / remaining_after

            # bonus stabilité (fréquences 2d6 normalisées)
            stability = PAIR_FREQ[v] / PAIR_FREQ_MAX

            immediate_score += proximity
            stability_bonus += 0.3 * stability  # poids modéré

        if is_double:
            immediate_score *= 1.8

        # Bonus pour pousser des colonnes déjà ouvertes ce tour
        already_open = sum(1 for v in action if v in temp_markers)
        immediate_score += 0.2 * already_open

        # Légère pénalité si l'action ouvre plusieurs nouvelles colonnes alors qu'on en a déjà
        if temp_markers is not None:
            opens = sum(1 for v in action if v not in temp_markers)
            if len(temp_markers) >= 2 and opens >= 2:
                immediate_score -= 0.3

        # Regarder la probabilité de pouvoir continuer après l'action
        p_continue_next = self._prob_can_continue(tm, game_state)

        return immediate_score + stability_bonus + self.alpha_future * p_continue_next

    def _prob_can_continue(self, temp_markers, game_state):
        """
        Probabilité exacte (sur 1296 tirages) d'avoir au moins une action légale
        au prochain lancer, étant donné:
          - colonnes verrouillées (via game_state)
          - état des marqueurs temporaires temp_markers
          - limite MAX_TEMP_MARKERS
        """
        success = 0
        for d1, d2, d3, d4 in self._all_rolls:
            dice = (d1, d2, d3, d4)
            pairs = game_state.get_pairs(dice)
            possible = self._enumerate_possible_actions(pairs, temp_markers, game_state)
            if possible:
                success += 1
        return success / 1296.0

    def _enumerate_possible_actions(self, pairs, temp_markers, game_state):
        """
        Reproduit la logique de 'possible' de main.py pour rester cohérent.
        Retourne une liste d'actions légales (tuples de 1 ou 2 colonnes).
        """
        tm = dict(temp_markers) if temp_markers is not None else {}   
        possible = []
        for i, (a,b) in enumerate(pairs):
            if not game_state.is_column_locked(a) and not game_state.is_column_locked(b):
                if a == b:
                    if a in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a]-1:
                            possible.append((a, b))
                    else:
                        if len(temp_markers) < MAX_TEMP_MARKERS and self.progress[a] < COL_LENGTHS[a]-1:
                            possible.append((a, b))
                else:
                    if a in temp_markers and b in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a] and temp_markers[b] < COL_LENGTHS[b]:
                            possible.append((a, b))
                    elif a not in temp_markers and b not in temp_markers:
                        if len(temp_markers) + 1 <MAX_TEMP_MARKERS:
                            possible.append((a, b))
                    elif a in temp_markers and b not in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS:
                            possible.append((a, b))
                    else:
                        if temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS:
                            possible.append((a, b))

            if (a,b) not in possible:
                for val in (a, b):
                    if not game_state.is_column_locked(val):
                        if val in temp_markers:
                            if temp_markers[val] < COL_LENGTHS[val]:
                                if val == a:
                                    possible.append((val,))
                                else:
                                    possible.append((val,))
                        else:
                            if len(temp_markers) < MAX_TEMP_MARKERS:
                                if val == a:
                                    possible.append((val,))
                                else:
                                    possible.append((val,))

        return possible
