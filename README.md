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




Peut être serait iltemps de créer un gym_env _v3 avec une obsvervation adaptée (moins de bruits) et peut être aussi laisser l'agent RL s'entrainer tout seul

nouvelle idée de reward : tant que RL décide de continuer : reward = nombre d'avancée dans les marqueurs temporaires. Mais si il buste, son reward est égale à l'opposé du carré de cette somme.
ça encourage RL a continuer et prendre des risques mais à faire attention à ne pas bust
J'ai implémenter cette dernière idée. Peut être qqche de trop pénalisant : en cas de bust la pénalité est le carré du reward que RL aurait dû avoir, donc pas le dernier reward mais le reward hypothetique. Je ne sais pas si c'est réellement un problème










[k=0.5] → 964/1000 victoires (96.40%)
[k=0.7] → 971/1000 victoires (97.10%)
[k=0.8] → 973/1000 victoires (97.30%)
[k=0.85] → 977/1000 victoires (97.70%)
[k=0.9] → 974/1000 victoires (97.40%)
[k=0.95] → 982/1000 victoires (98.20%)
[k=1] → 978/1000 victoires (97.80%)
[k=1.1] → 979/1000 victoires (97.90%)
[k=1.2] → 978/1000 victoires (97.80%)
[k=1.5] → 974/1000 victoires (97.40%)