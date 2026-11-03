# Tableau de bord du pilotage

Tenu par l'agent pilote à chaque /pilotage. Les décisions elles-mêmes vont dans le journal de docs/PLAN.md (§13).

Dernier point de pilotage : 2026-11-03

## Note prévisionnelle du correcteur
| Date | Données /4 | Descriptif /4 | Démarche et repro /5 | Code /2 | Soutenance /5 | Total /20 |
|------|-----------|---------------|----------------------|---------|---------------|-----------|
| 13/10 état actuel | 0,5 | 0 | 1,5 | 0,6 | 1,2 | environ 4 (pas de notebook, donc pas de moyenne) |
| 13/10 plan exécuté avec A1 à A4 | 3,4 | 3,0 | 4,2 (3,2 si Git reste à un seul auteur) | 1,5 | 3,3 | environ 15,4 (fourchette 13,5 à 16,5) |
| 20/10 état actuel | 2,0 | 0,5 | 1,0 | 1,4 | 1,5 | environ 6,4, sans moyenne (le notebook plante sur un compte neuf : annuaire non gelé) |
| 20/10 plan exécuté avec A5 à A7 | 3,5 | 3,0 | 4,2 (3,0 si Git reste à un seul auteur) | 1,6 | 3,3 (2,3 si deux membres n'ont pas écrit de code) | environ 15,6 (fourchette 12,5 à 16,5 ; 15,0 sans A5 à A7) |
| 20/10 plan exécuté avec A5 à A7, A9, A10 | 3,45 | 3,4 | 4,4 (3,1 si Git reste à un seul auteur) | 1,7 | 3,3 | environ 16,3 (fourchette 13 à 16,5), estimé sans A8 : le correcteur donnait 16,4 avec A8, dont +0,05 en Données et +0,1 en Soutenance |
| 20/10 soir : état actuel → plan exécuté avec A13 à A15 | 2,0 → 3,4 | 0,5 → 3,1 | 1,0 → 4,2 (3,0 si Git reste à un seul auteur) | 1,4 → 1,7 | 1,5 → 3,2 (2,2 si deux membres n'ont rien écrit) | environ 6,4 sans la moyenne (compte neuf : `RuntimeError` dans `stockage._telecharger`, copies en 403 et 404) → environ 15,6 (fourchette 12,5 à 16,5) ; à part, risque de −1 à −3 pour usage abusif de l'IA (`CLAUDE.md` public) |
| 21/10 : état actuel → plan exécuté (avis du 20/10 soir sur A16 à A18) | 2,2 → 3,4 | 0,5 → 3,0 | 1,2 → 4,0 (3,0 si Git reste à un seul auteur) | 1,4 → 1,6 | 1,5 → 3,0 (2,2 si deux membres n'ont pas écrit de code) | environ 6,8 sans la moyenne (compte neuf : `collecte.ips_lycees()` en 403 et 404) → environ 15,0 (fourchette 12 à 16) ; à part, −1 à −3 pour usage abusif de l'IA (traces de l'assistant dans le code) |
| 03/11 : état actuel → plan exécuté (A19 à A21 appliqués) | 2,4 → 3,3 | 0,8 → 3,1 | 1,3 → 3,8 | 1,6 → 1,7 | 1,5 → 3,0 | environ 7,6 sans la moyenne (compte neuf : 5 copies du 03/11 en 404 et 403) → 12 à 16 ; à part, −1 à −3 pour usage abusif de l'IA (`CLAUDE.md` l. 18-19 public, journal en annexe avec les mentions d'agents, §12 public, pas de section IA au README) |

## Actions prioritaires
Suivi au 03/11 : décisions du 03/11 et A19 à A21 au journal (§13) ; choix figés modifiés : §1.2 (H4 descriptive), §2.4 (agricoles), §2.5 (DVF). Faits depuis le 21/10 : T5, H1 à H4, robustesse, Moran, Fig. 1 à 7, release `donnees-20261020` lisible, traces de l'assistant retirées du code. Non faits : tag ; relecture humaine des PR n° 2, 5 et 6, ouvertes le 21/10 (seul un robot a commenté ; la n° 7 est fusionnée) ; Git à trois (71 commits sur 73 de `fogatogl`) ; section IA du README ; aucune phrase dans le rapport ; §1 et §3.1 de R3 (dus le 1/11).
1. A19, aujourd'hui : publier les 5 copies du 03/11 (gares, APL, Data ES, BPE, DVF) et pousser `feat/rapport`. Avant le 8/11 : compte neuf par R2 ou R3 ; PR n° 2 (R2), 5 (R3) et 6 (R2) relues ligne à ligne et fusionnées ; puis PR n° 8 `feat/rapport` (R2 `analyse.py`, R3 `figures.py` et le notebook, au moins une correction poussée par un relecteur) ; conflit README avec `main` résolu, « Projet cadres et lycées au 21 octobre.md » retiré de `main` ; tag annoté `plan-fige` sur `b782378`, renvoyant à la PR n° 2 et à la ligne « chiffres vus avant le tag ». Deuxième compte neuf vers le 22/11.
2. A21 : R3 ouvre un brouillon de PR avec le §1.1 le 6/11, puis les sections 1 à 3, l'encadré 2.5 et la section IA du README le 10/11 (sinon R2 reprend) ; R2 la section 4 et les titres des Fig. 4 à 6 le 15/11 ; Giulio les sections 5 et 6, le résumé, le titre de la Fig. 7 et les « Résultats clés » le 18/11 ; fusion sous 48 h.
3. Transparence IA : Giulio réécrit `CLAUDE.md` l. 18-19 (règle anti-mention dans les commits) ; il décide comment présenter le journal en annexe et le §12 du plan, publics.

## Points ouverts
- Soutenance : savoir chiffrer le résultat nul de Lyon (intervalle de −0,53 à +0,21 point par km, soit −2,7 à +1,1 point sur 5 km) ; H3 « infirmée » alors que le test penche contre H3 (β_q atténué, β_n gonflé) ; Moran résiduel (0,31 à Lyon, intervalles des paires optimistes). Encadré 2.5 : fenêtre DVF postérieure à 2022, Strasbourg hors DVF, 15 lycées agricoles privés en Loire-Atlantique.
- Écarts plan-code réglés le 03/11 au soir : chef-lieu et robustesses de H3 codés, Filosofi abandonné. Premier jet du texte par l'assistant (écart au §8.3, déclaré) : chaque auteur doit le reprendre selon A21 ; copie gelée des chefs-lieux à publier avec les 5 autres.
- 6 cellules d'anneaux estimables sur 12 : le panneau des anneaux de la Fig. 4 est presque vide. Code : `config.py` (563 lignes), `figures.py` (983) et `analyse.py` (901) à alléger en S6.

## Désaccords ouverts entre pilote et correcteur
- A16 (e), mineur : variation de l'IVAL lue entre aires (correcteur) ou dans chaque cellule aire × anneau (pilote) ; le journal donne les chiffres par cellule.
- Exécution du 03/11 avant le tag : décision de Giulio, contre l'avis commun du 20/10 et la ligne du 21/10 ; journalisée telle quelle.
