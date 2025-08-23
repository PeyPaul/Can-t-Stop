# Can-t-Stop


On a bien avancé. Maintenant on a quelquechose qui fonctionne : on peut entrainer l'agent et jouer contre lui.
Mais problème, il est nul donc on va essayer de modifier les reward pour voir si on arrive à quelquechose de mieux

Les pauses dans l'entrainement sont un phénomène étrange. Ils viennent tous de la boucle dans step, il doit y avoir un problème avec les variables.
Aussi le plateau de jeux est complétement remplis lors de ses blocage, ce qui est rès étrange, je ne sais pas comment cela peut arriver

Col  2 [Lm,Lm,m,] (Verrouillée)
Col  3 [Lm,Lm,m,m,m,] (Verrouillée)
Col  4 [Lm,Lm,Lm,Lm,Lm,Lm,m,] (Verrouillée)
Col  5 [Lm,Lm,Lm,Lm,Lm,Lm,m,m,m,] (Verrouillée)
Col  6 [Lm,Lm,Lm,Lm,Lm,Lm,Lm,Lm,Lm,Lm,L,] (Verrouillée)
Col  7 [Lm,Lm,Lm,Lm,Lm,Lm,Lm,Lm,Lm,Lm,m,m,m,] (Verrouillée)
Col  8 [Lm,Lm,Lm,Lm,Lm,Lm,Lm,m,m,m,m,] (Verrouillée)
Col  9 [Lm,Lm,Lm,Lm,m,m,m,m,m,] (Verrouillée)
Col 10 [m,m,m,m,m,m,m,] (Verrouillée)
Col 11 [Lm,Lm,m,m,m,] (Verrouillée)
Col 12 [m,m,m,] (Verrouillée)

Cette configuration est en théorie impossible



Je trouve que l'agent RL n'est toujours pas bon, peut être qu'il va falloir penser à modifier les informations à donner à l'IA pour les rendre plus simples