# Dictionnaire des variables

Sorties de `pipeline.construire_base(aires)` (PLAN §4, étape G). Distances à vol d'oiseau en Lambert 93 (EPSG:2154), depuis le centroïde géométrique de la commune.

## `final/base_communale.parquet` : une ligne par commune

Communes des aires demandées, au COG 2025, avec les arrondissements municipaux à la place de Lyon.

| Variable | Définition | Unité | Source, fonction |
|---|---|---|---|
| `code_commune` | Code de la commune, ou de l'arrondissement à Lyon (69381 à 69389) | texte | cartiflette (`INSEE_COG`), `geo.referentiel_communes` |
| `code_parent` | Code de la commune parente (69123 pour les arrondissements de Lyon, sinon le même code) | texte | cartiflette (`INSEE_COM`) |
| `nom_commune` | Nom de la commune ou de l'arrondissement | texte | cartiflette (`NOM`) |
| `geometry` | Contour de la commune, non simplifié | polygone, EPSG:2154 | cartiflette 0.4.0, ADMIN EXPRESS COG 2025 |
| `aire` | Nom de l'aire d'attraction des villes (clé de `aires`, par exemple `config.AIRES_RETENUES`) ; les communes y sont rattachées par leur code `AAV2020` | texte | Insee, AAV 2020 |
| `pole_couronne` | `pole` (commune-centre ou autre commune du pôle) ou `couronne` | texte | Insee, AAV 2020 (`CATEAAV2020`) |
| `centroide` | Centroïde géométrique du contour, point de référence de la commune (§2.4) | point, EPSG:2154 | `geo.referentiel_communes` |
| `dist_centre_km` | Distance entre le centroïde et celui de la commune-centre de l'aire (`CATEAAV2020` = 11, Lyon entière) | km | `geo.referentiel_communes` |
| `n_lyc_prive_<r>km` | Nombre de lycées privés sous contrat à r km ou moins du centroïde (r = 3, 5, 10), bord compris | nombre | annuaire de l'éducation du 13/10/2026, `accessibilite.indicateurs` |
| `dist_lyc_prive_min` | Distance au lycée privé sous contrat le plus proche, parmi tous ceux de France métropolitaine | km | idem |
| `n_lyc_public_<r>km` | Nombre de lycées publics à r km ou moins | nombre | idem |
| `dist_lyc_public_min` | Distance au lycée public le plus proche, parmi tous ceux de France métropolitaine | km | idem |
| `n_lyc_<r>km` | Nombre de lycées, publics et privés sous contrat, à r km ou moins | nombre | idem |
| `ival_moy_<r>km` | Moyenne, pondérée par `poids_ival`, de l'`ival` des lycées publics et privés sous contrat à r km ou moins qui en ont une ; manquante s'il n'y en a aucun | points de pourcentage | DEPP, IVAL (règle A1), `accessibilite.indicateurs` |
| `pop_2022` | Population en 2022 (`P22_POP`) | habitants | Insee, série historique du recensement 2022, `nettoyage.population` |
| `densite` | `pop_2022` divisée par la superficie de l'Insee (`SUPERF`) | habitants par km² | idem |
| `log_densite` | Logarithme népérien de `densite`, forme du contrôle de densité (A7) | — | `nettoyage.population` |
| `expose_lyc_prive_<r>km` | 1 si au moins un lycée privé sous contrat est à r km ou moins, sinon 0 | 0 ou 1 | `pipeline.construire_base` |
| `n_gare_<r>km` | Nombre de gares de voyageurs à r km ou moins du centroïde (r = 3, 5, 10), bord compris (H4) | nombre | SNCF Gares & Connexions, gares de voyageurs, copie du 03/11/2026, `accessibilite.indicateurs` |
| `dist_gare_min` | Distance à la gare de voyageurs la plus proche, parmi toutes celles de France métropolitaine continentale (H4) | km | idem |
| `apl_mg` | Accessibilité potentielle localisée aux médecins généralistes, tous âges, millésime 2024 (H4) | consultations par an et par habitant standardisé | DREES, copie du 03/11/2026, `collecte.apl_medecins` |
| `n_sport_<r>km` | Nombre d'installations sportives en service à r km ou moins du centroïde (r = 3, 5, 10), bord compris (H4) | nombre | Data ES, ministère des Sports, copie du 03/11/2026, `accessibilite.indicateurs` |
| `dist_sport_min` | Distance à l'installation sportive en service la plus proche (H4, descriptif) | km | idem |
| `log_n_sport_5km` | log(1 + `n_sport_5km`), mesure du sport dans H4 | — | `pipeline.construire_base` |
| `n_culture_<r>km` | Nombre d'équipements culturels (BPE, sous-domaine F3) à r km ou moins du centroïde (r = 3, 5, 10), bord compris (H4) | nombre | Insee, BPE 2025, copie du 03/11/2026, `accessibilite.indicateurs` |
| `dist_culture_min` | Distance à l'équipement culturel le plus proche (H4, descriptif) | km | idem |
| `log_n_culture_5km` | log(1 + `n_culture_5km`), mesure de la culture dans H4 | — | `pipeline.construire_base` |
| `part_cadres_2011`, `part_cadres_2022` | Cadres et professions intellectuelles supérieures (groupe 3) parmi les actifs de 25 à 54 ans, occupés ou chômeurs ayant déjà travaillé (somme des 6 groupes), au recensement 2011 ou 2022 | fraction de 0 à 1 | Insee, « Évolution et structure de la population » 2022 (`C11_POP2554_CS3`, `C22_POP2554_STAT_GSEC13_23`), `nettoyage.part_cadres` |
| `prix_m2_med` | Prix médian au m², ventes d'un seul appartement ou d'une seule maison, de juillet 2021 à juin 2026 ; manquant sous 10 ventes et dans toute l'Alsace-Moselle (hors DVF) | euros par m² | Etalab, « Statistiques DVF » (`med_prix_m2_whole_apt_maison`, `nb_ventes_whole_apt_maison`), copie du 03/11/2026, `nettoyage.prix_m2` |
| `log_prix_m2` | Logarithme népérien de `prix_m2_med`, contrôle de la robustesse au prix (§2.5) | — | `nettoyage.prix_m2` |
| `part_cadres_15p_2022` | Cadres et professions intellectuelles supérieures parmi la population de 15 ans ou plus en 2022, inactifs et retraités compris ; robustesse de la variable à expliquer (§2.3, §5.6) | fraction de 0 à 1 | Insee, « Évolution et structure de la population » 2022 (`C22_POP15P_STAT_GSEC13_23` sur `C22_POP15P`), `nettoyage.part_cadres` |
| `evol_cadres_pts` | `part_cadres_2022` moins `part_cadres_2011` | points de pourcentage | `nettoyage.part_cadres` |
| `actifs_2011`, `actifs_2022` | Actifs de 25 à 54 ans en 2011 ou 2022, dénominateurs des parts de cadres ; `actifs_2022` est le poids des moyennes, et le plus petit des deux sert au seuil de 200 actifs de H3 (§3.2, A17) ; effectifs décimaux (exploitation complémentaire) | personnes | idem |

Lycées retenus (§2.4) : lycées d'enseignement général et technologique et lycées polyvalents (`code_nature` 300, 301, 302 et 306), publics ou privés sous contrat (contrat d'association 30 ou 31), hors lycées agricoles.

## Lycées (deuxième sortie de `construire_base`, non écrite sur disque)

| Variable | Définition | Unité | Source, fonction |
|---|---|---|---|
| `uai` | Identifiant de l'établissement | texte | annuaire de l'éducation |
| `nom_lycee` | Nom de l'établissement | texte | idem |
| `code_commune` | Commune de l'établissement (arrondissement à Lyon) | texte | idem |
| `secteur` | `public` ou `prive` (privé sous contrat) | texte | idem (`statut_public_prive`) |
| `aire` | Aire de la commune du lycée ; manquante hors des aires | texte | `nettoyage.lycees_geo` |
| `ips` | Indice de position sociale de la voie générale et technologique, rentrée 2025-2026 ; manquant pour 87 lycées sur 2 413 | indice | DEPP, IPS des lycées |
| `ival` | Moyenne simple de la valeur ajoutée du taux d'accès de la seconde au bac (`va_acces_2nde`), sessions 2012 à 2022, pour les lycées qui en ont au moins 5 | points de pourcentage | DEPP, IVAL, `nettoyage.ival_par_lycee` |
| `poids_ival` | Moyenne des présents au bac (`presents_total`) sur ces mêmes sessions | élèves | idem |
| `geometry` | Position du lycée | point, EPSG:2154 | annuaire de l'éducation |

## `final/paires.parquet` : une ligne par paire de communes contiguës

Paires de communes d'une même aire qui se touchent, par un bord ou par un seul point (contiguïté « Queen », §4 F), chacune une seule fois.

| Variable | Définition |
|---|---|
| `code_commune_i`, `code_commune_j` | Codes des deux communes, avec `code_commune_i` < `code_commune_j` dans l'ordre des codes |
| `aire` | Aire des deux communes |
| `d_<v>` | Valeur de i moins valeur de j pour chaque variable de `config.VARIABLES_PAIRES` : `part_cadres_2022`, `dist_lyc_prive_min`, `n_lyc_prive_5km`, `dist_centre_km`, `log_densite`, `expose_lyc_prive_5km`, `expose_lyc_prive_10km`, `dist_gare_min`, `apl_mg`, `log_n_sport_5km`, `log_n_culture_5km` ; manquant si l'une des deux valeurs manque |

Le sens i − j suit l'ordre des codes : il est arbitraire. Une paire est « de statut différent » à 5 ou 10 km quand `d_expose_lyc_prive_5km` ou `d_expose_lyc_prive_10km` vaut 1 ou −1.
