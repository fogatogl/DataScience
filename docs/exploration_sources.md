# Exploration des sources de données (13/10/2026)

Notes issues de l'exploration en lecture seule des 8 sources P1 du plan, faite le 13/10/2026 par des agents d'exploration. **Le code couvre la collecte (annuaire, AAV, contours, IPS), le référentiel des communes et le nettoyage des lycées (jointure avec l'aire et l'IPS pour la Fig. 1) ; rien d'autre n'est nettoyé.** Les URL, les noms de colonnes et les chiffres ci-dessous ont été observés ce jour-là : les jeux de l'Éducation nationale changent (l'annuaire est mis à jour chaque jour), donc revérifier avant de s'appuyer sur un chiffre. Les noms de colonnes sont copiés tels quels depuis les fichiers.

Pour la suite : `CLAUDE.md` demande de lire la section d'une source avant tout ticket qui la touche, et de la corriger si la réalité diffère.

## 1. Où en est le projet

- **Fait** (branches empilées `chore/harness-claude` → `feat/squelette` → `feat/collecte-annuaire` → `feat/collecte-aav` → `feat/geo-referentiel` → `feat/fig1-ips`, rien n'est encore fusionné dans `main`) :
  - le harness Claude Code (`.claude/`, `CLAUDE.md`, `ruff.toml`) et cette exploration ;
  - T0, le squelette du dépôt (`c09b613`), T1, `stockage.py` (`9e9a41d`), et T2, `collecte.annuaire_education` (`ffdeab0`) ;
  - le journal §13 (`45bc8c8`), puis le point de pilotage du 13/10 : amendements A1 à A4 écrits dans le plan et tableau de bord dans `.claude/pilotage.md` ;
  - T3 : `collecte.aav_2020` (`0a4e332`) et `geo.referentiel_communes` avec `collecte.contours_aire` (`df2ca4a`) ;
  - T6 : `collecte.ips_lycees`, `nettoyage.lycees_geo`, `analyse.profil_aires`, `figures.fig1` et `rapport.ipynb` (Fig. 1 seule) ;
  - lycées hors des aires : `collecte.annuaire_education()` lit toute la métropole, sans liste de départements, et `nettoyage.lycees_geo` garde les lycées hors des aires (`aire` manquante) pour l'accessibilité (décision du 20/10, voir §3, à journaliser) ;
  - T4 : `accessibilite.indicateurs` (comptes par rayon et distance au plus proche, sans `marge_km` ni `attribut`, à journaliser) et `tests/test_accessibilite.py`, branche `feat/accessibilite` ;
  - paires contiguës : `geo.paires_contigues` (contiguïté Queen, 5 890 paires sur les 8 candidates dont 100 par un seul point, identiques à libpysal Queen ; `d_<v>` = v_i − v_j pour i < j, manquant si une valeur manque ; échec si une commune n'a pas de voisine) et `tests/test_geo.py`, branche `feat/paires-contigues`. Le sens i − j suit l'ordre des codes (à Lyon, l'arrondissement est toujours j) : seules une pente sans constante ou des paires symétrisées n'en dépendent pas, à fixer avant T5.
  - Fig. 3 : `figures.fig3`, carte folium par aire (classes de distance au lycée privé le plus proche, lycées par secteur, deux fonds sans clé), branche `feat/fig3-carte`. Le fond CARTO de folium exige une clé depuis 2026 (« API KEY REQUIRED » à l'écran, constaté le 20/10) : fonds Esri gris et Plan IGN, sans clé.
  - IVAL (H3) : `collecte.ival_lycees` (copie du 20/10, sha256), `nettoyage.ival_par_lycee` (règle A1), `lycees_geo` avec `ival` et `poids_ival`, `accessibilite.indicateurs(..., attribut, poids)` et 2 tests, branche `feat/ival`. Choix du 20/10 à journaliser : session valide = valeur ajoutée renseignée ; poids sur ces sessions ; rattachement des lycées publiés sous un autre UAI (voir §5).
  - copies gelées (A2, A10) : `stockage.copie_controlee` (sha256 contrôlé à chaque lecture, adresse publique S3 puis release GitHub, avertissement par adresse refusée), annuaire du 13/10, IPS, IVAL et 8 contours datés, `collecte.geler_annuaire` et `geler_contours` pour refaire un gel, README ; branche `feat/copies-gelees`. **Publication en attente** (20/10) : les identifiants S3 du service ont expiré (`PermissionError: Forbidden` sur le bucket, `AWS_ENDPOINT_URL` bien définie), les 11 fichiers sont dans `data/gel_20261020/` ; tant qu'ils ne sont pas publiés et vérifiés par un `curl` anonyme, un compte neuf échoue sur l'annuaire.
  - nettoyage et base v0 (A9, A10), branche `feat/nettoyage-code` : `plotly` et `duckdb` retirés des dépendances directes, `numpy` déclaré ; `nettoyage.lycees_geo` découpée en quatre fonctions ; listes d'UAI valables pour toute partie des 8 candidates (et chaque UAI listé doit exister dans sa source) ; titres-messages obligatoires dans `fig1` et `fig3` ; Fig. 1 refaite (part du privé en lycées et en candidats au bac, IPS de chaque lycée) ; `pipeline.construire_base(aires)` (base 2 179 × 28, paires 5 890 × 9, en 4,5 s) appelée par le rapport ; `docs/dictionnaire_variables.md`.
- **Pas fait** : le tableau de support, T5 (cadres), le test de fiabilité de l'IVAL (Spearman-Brown) et sa robustesse 2012-2025, les copies gelées de l'annuaire et de l'IVAL (amendement A2). L'ordre des tickets est celui du §12.2 du plan, qui fait foi : cette page ne le répète pas.
- **S3** : l'aller-retour `existe`, `ecrire_octets`, `lire_parquet` et `ecrire_parquet` a été testé le 13/10 sur le bucket personnel d'un membre, avec la copie brute de l'annuaire dans `raw/` relue identique. Piège : le listage des buckets (`list_buckets`, donc `s3fs.ls("")`) ne répond jamais avec ces identifiants, alors que les requêtes sur un bucket précis répondent en moins d'une seconde. Ne pas s'en servir pour retrouver le nom du bucket.

### Corrections factuelles au plan (une ligne chacune au journal §13)

Ce ne sont pas des changements de choix fixés avant les résultats. Appliquées au journal §13 le 13/10/2026 (le plan n'est modifiable que par le pilote, avec validation de l'étudiant).

| Constat | Ligne de journal proposée |
|---|---|
| La source 1 n'est pas en COG 2025 : RP2011 est en COG 2013 et RP2022 en COG 2024. | Conversion vers le COG 2025 par la table de passage annuelle 2025 (§8 ci-dessous). Le dénominateur de la source 1 est « actifs occupés + chômeurs ayant déjà travaillé ». |
| `pip install git+https://github.com/inseefrlab/cartiflette` installe un autre paquet (le pipeline de production), sans `carti_download`. | `cartiflette==0.4.0` depuis PyPI, épinglé. Appels avec `year=2025`, `simplification=0`, puis `.to_crs(2154)`. |
| `pynsee` impose `pandas<3.0` et n'est pas nécessaire : les fichiers de l'Insee se lisent directement. | `pynsee` abandonné. |
| Les xlsx de l'Insee ne s'ouvrent pas avec openpyxl, le moteur par défaut de pandas. | `python-calamine` ajouté, avec `engine="calamine"`. Testé le 13/10 : il lit les 4 xlsx (table de passage, AAV, table d'appartenance, séries CSP), seul, sans openpyxl. |
| Les colonnes `voie_*` de l'annuaire sont trop souvent vides ou fausses. | Les lycées sont filtrés par `code_nature` (§3). |

### Décisions en attente

| Décision | Défaut recommandé | Quand |
|---|---|---|
| Filtre des lycées | Décidé et codé à T2 : filtre pandas par `code_nature`, tel que défini au §3 ci-dessous. Les variantes (sections rattachées à un LP, lycées militaires, agricoles par drapeau) vont en robustesse. | fait |
| IPS par aire (Fig. 1) | Moyenne simple des lycées de l'aire, car il n'y a pas d'effectifs. Colonne `ips_voie_gt` pour rester sur le périmètre général et technologique. | fait à T6 avec ce défaut et la rentrée 2025-2026 (`config.py`), à valider par le groupe |
| Choix des 3 aires | Aux étudiants, sur les critères (a) à (f) du §2.2 du plan. Entrées : §7 (communes par aire), §3 (lycées), §4 (IPS) ; la population de l'aire (critère c) vient de `P22_POP` (§10). | avant le 18/10 |
| Lyon : arrondissements | Mesuré le 20/10 (§10) : « Évolution et structure » donne les 9 arrondissements avec la définition de la source 1, en 2011 et 2022. Le coût de Lyon pour la variable à expliquer est nul ; ACT5 n'est plus nécessaire. | fait, choix de la source à trancher en `/pilotage` |
| Dénominateur de la variable à expliquer | Occupés + chômeurs ayant déjà travaillé : somme des 6 groupes socioprofessionnels des 25-54 ans, dans la source 1 ou dans « Évolution et structure » (§10), qui donnent les mêmes valeurs. Source à trancher en `/pilotage` : « Évolution et structure » pour toutes les communes (un seul chemin, COG 2025, arrondissements) ou source 1 et table de passage, avec « Évolution et structure » pour Lyon. | avant T5 |
| Fiabilité de l'IVAL pour H3 | Décidé le 13/10 (amendement A1) : moyenne 2012-2022 avec au moins 5 sessions, H3 « non testable » si la fiabilité est sous 0,5. Voir §5 et le journal §13. | fait |
| Scissions de communes, petites communes, communes à population nulle | À traiter à T5 avec des `assert` explicites. | T5 |
| Superficie de la densité (§2.5) | Décidé le 20/10 par l'étudiant : `SUPERF` de la série historique (même source que `P22_POP`), et non la surface des contours IGN. Codé dans `nettoyage.population`, à journaliser avec l'usage de la série historique à la place de la source 2. | fait |
| Forme et place de `densite` comme contrôle | À trancher en `/pilotage` avant T5 : log ou non, spécification principale ou robustesse (voir §10). | avant T5 |

## 2. Pièges qui traversent plusieurs sources

- **Codes en chaîne de caractères, toujours.** `dtype=str` ou équivalent : `REG` revient en entier (`01` devient `1`), `code_departement` de l'annuaire vaut `035`, `AAV2020` vaut `013`, la Corse est `2A`/`2B`.
- **Quatre géographies différentes selon la source** : source 1 en COG 2013 (RP2011) et 2024 (RP2022) ; recensement, cartiflette 2025 et AAV 2025 en COG 2025 ; annuaire, IPS et IVAL en codes courants, où l'on a trouvé 93059 (Pierrefitte-sur-Seine, fusionnée dans 93066) dans l'IPS ; ACT5 2022 en COG 2025.
- **Lyon, Marseille, Paris** : selon la source, parent, arrondissements, ou les deux.

| Source | Lyon (69123) | Marseille (13055) | Paris (75056) |
|---|---|---|---|
| Source 1 (séries CSP) | parent seul | parent seul | arrondissements 75101-75120, sans parent |
| ACT5 (2011 et 2022) | parent (`COM`) et arrondissements 69381-69389 (`ARM`) | parent et 13201-13216 | parent et 75101-75120 |
| Recensement evol-struct | parent et arrondissements (**à dédoublonner**) | idem | idem |
| AAV 2025, `Composition_communale` | parent seul | parent seul | parent seul |
| Table d'appartenance, feuille `ARM` | 9 arrondissements, `AAV2020` = `002` | 16 | 20 |
| cartiflette `COMMUNE_ARRONDISSEMENT` | `INSEE_COM` = parent, `INSEE_COG` = arrondissement | idem | idem |
| Annuaire, IPS, IVAL | arrondissements 693xx (le parent n'apparaît pas) | 132xx (annuaire : une ligne en 13055, non retenue) | 751xx |

  **Piège Fig. 1** : l'annuaire place les lycées de Lyon en 693xx alors que l'AAV n'a que 69123. `geo.referentiel_communes` est au grain arrondissement (693xx, avec `code_parent` = 69123) : joindre les lycées sur son `code_commune`, sans rattacher les arrondissements à leur parent, sinon le code 69123, absent de l'annuaire, ne correspond à aucun lycée et les 43 lycées de Lyon disparaissent sans erreur. Si le plan passe Lyon au grain commune (proposition A5 du pilote), c'est l'inverse : il faudra rattacher 693xx à 69123.
- **Moyennes** : une part de cadres ne se moyenne pas. Après une fusion de communes, sommer numérateur et dénominateur.
- **Ne jamais joindre sur un libellé** (`nom_commune`, `LIBGEO`, `libelle_commune`) : libellés tronqués, accents remplacés par `?` dans l'IVAL, noms qui diffèrent selon l'année, un même libellé pour deux codes (« Valence » = `049` et `396`).
- **Dépendances** : `uv add python-calamine` ; `pandas` 3.x se résout sans `pynsee` ; installer `cartiflette==0.4.0` depuis PyPI.

## 3. Annuaire de l'éducation (source 3)

- **Jeu** : `fr-en-annuaire-education` sur data.education.gouv.fr (API Opendatasoft v2.1), 68 562 lignes et 71 champs à la date du 13/10/2026, Licence Ouverte v2.0. Instantané mis à jour **chaque jour**, donc figer une copie brute dans `raw/` dès le premier téléchargement.
- **Base** : `https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education`
- **Endpoints**
  - `/records?where=…&limit=100&offset=0&order_by=identifiant_de_l_etablissement` : `limit` ≤ 100 et `offset + limit` ≤ 10 000 (erreur 400 sinon). `limit=-1` ne renvoie que 100 lignes. À éviter.
  - `/exports/parquet?where=…` : **voie recommandée.** Pas de limite de lignes. GeoParquet, colonne `position` en WKB, CRS84, codes en chaîne. Se lit avec `geopandas.read_parquet` ou `duckdb`. Le jeu entier fait 11 Mo ; avec le filtre ci-dessous, 0,5 Mo. `collecte.annuaire_education` télécharge l'export entier, sans `where`, pour garder une vraie copie brute et pouvoir refaire les variantes de robustesse, puis filtre en pandas (mêmes 2 571 lignes).
  - `/exports/csv` : séparateur `;`, BOM UTF-8 (`encoding="utf-8-sig"`) ; lire avec `dtype=str`, sinon `code_departement` devient l'entier 31.
  - `/exports/geojson` : 13 géométries `null` sur les 2 571 retenues.
- **Champs utiles** (noms exacts)

| Besoin | Champ |
|---|---|
| UAI | `identifiant_de_l_etablissement` |
| Nom | `nom_etablissement` |
| Public ou privé | `statut_public_prive` (`Public`, `Privé`, null) |
| Type | `type_etablissement` |
| Nature détaillée | `code_nature` (entier), `libelle_nature` |
| Voies | `voie_generale`, `voie_technologique`, `voie_professionnelle` (texte `"0"` ou `"1"`, null), **inutilisables seules** |
| Contrat du privé | `type_contrat_prive`, `code_type_contrat_prive` |
| Agricole | `lycee_agricole` (`"0"`, `"1"`), `ministere_tutelle` |
| Commune | `code_commune` (5 caractères), `nom_commune` |
| Département | `code_departement` (**3 caractères** : `035`, `02A`, `971`) |
| Coordonnées | `latitude`, `longitude`, `position`, `coordx_origine`, `coordy_origine`, `epsg_origine` |
| Autres | `precision_localisation`, `etat`, `multi_uai`, `etablissement_mere`, `type_rattachement_etablissement_mere`, `date_ouverture`, `date_maj_ligne` |

- **Pas de nombre d'élèves.** Deux jeux d'effectifs existent au catalogue, non inspectés : `fr-en-lycee_gt-effectifs-niveau-sexe-lv` et `fr-en-lycee_pro-effectifs-niveau-sexe-lv`.
- **Filtre du plan (§2.4)**, vérifié : `total_count` = 2 571 lignes (2 542 UAI) en France.
  ```
  type_etablissement="Lycée" and code_nature in (300,301,302,306) and ministere_tutelle!="AGRICULTURE" and not lycee_agricole="1" and (statut_public_prive="Public" or (statut_public_prive="Privé" and code_type_contrat_prive in ("30","31")))
  ```
  Les natures retenues sont, dans les libellés de l'annuaire : 300 LEGT, 301 LET, 302 LEG et 306 lycée polyvalent. `30` est le contrat d'association toutes classes, `31` la partie des classes. Le type `Lycée` isole la partie lycée d'une cité scolaire : la partie collège, typée `Collège`, partage le même UAI.
  - Retenus : 1 674 lignes publiques et 897 privées sous contrat ; en métropole 2 442 lignes (2 413 UAI).
  - Exclus (en lignes) : LP `320` 1 695, sections professionnelles `334` 757, sections générales et technologiques `335` 109, GT ou polyvalent agricole 101, GT ou polyvalent privé hors contrat 275, etc.
- **Dans les 8 départements candidats** (lignes / UAI / public / privé sous contrat)

| Dép. | Lignes | UAI | Public | Privé |
|---|---|---|---|---|
| 035 Rennes | 38 | 37 | 20 | 17 |
| 044 Nantes | 56 | 54 | 27 | 27 |
| 031 Toulouse | 44 | 44 | 32 | 12 |
| 033 Bordeaux | 51 | 51 | 34 | 17 |
| 069 Lyon | 80 | 73 | 39 | 34 |
| 038 Grenoble | 47 | 47 | 35 | 12 |
| 059 Lille | 101 | 99 | 57 | 42 |
| 067 Strasbourg | 42 | 42 | 31 | 11 |
| Total | 459 | 447 | 275 | 172 |

  Un `assert` sur ces comptes protège la jointure avec l'AAV.
- **Doublons d'UAI** : 54 lignes pour 25 UAI parmi les retenus au niveau national, 21 lignes pour 9 UAI dans les 8 départements (établissements multi-sites). `code_commune` et coordonnées sont identiques sur toutes les lignes d'un même UAI : `drop_duplicates("identifiant_de_l_etablissement")` ne perd rien.
- **Coordonnées** : 0 manquante dans les 8 départements ; 13 manquantes sur 2 571 retenus, toutes en Polynésie ou à Wallis. Les annexes situées dans une autre commune sont placées au site principal.
- **Export Parquet, vérifié à T2 (13/10)** : 68 562 lignes, 11,3 Mo, 12 s de téléchargement. La métadonnée `geo` est présente et la géométrie est dans la colonne `position`, mais le CRS **n'est pas écrit** dans les métadonnées : geopandas le lit comme `OGC:CRS84` (donc pas de test `crs == 4326`, `to_crs(2154)` marche). 438 géométries nulles sur l'export complet. Types : `code_nature` entier, tous les autres champs utiles en chaîne.
- **Valeurs manquantes dans le filtre** : `lycee_agricole` est vide sur 57 198 lignes (19 des 2 571 retenues) et `statut_public_prive` sur 1 968. En pandas, `!= "1"` garde la ligne vide, ce que fait aussi le `where` serveur : le filtre pandas de `collecte.annuaire_education` et le `where` ci-dessus donnent exactement les mêmes 2 571 lignes (comparaison ligne à ligne). `code_type_contrat_prive` contient aussi la valeur `"!!"` (12 lignes), sans effet sur le filtre.
- **Piège : lycée sans statut.** Parmi les lignes de nature 300 à 306, deux ont `statut_public_prive` vide : `0171680J` (017, tutelle AGRICULTURE, donc exclu de toute façon) et `0271911F` (027, tutelle de l'Éducation nationale, ouvert le 01/09/2024), un lycée public perdu sans erreur par un filtre `== "Public"`. Depuis le 20/10, l'annuaire est lu sur toute la métropole : `0271911F` est écarté nommément (`config.UAI_SANS_STATUT` ; absent aussi de l'IPS, à 188 km de l'aire candidate la plus proche), et tout nouveau cas fait échouer `collecte.annuaire_education` en nommant l'UAI. L'annuaire est mis à jour chaque jour : de nouveaux cas peuvent apparaître.
- **Variantes du filtre** (8 départements : lignes / UAI) : + sections `335` rattachées à un LP, 472 / 460 ; exclusion de l'agricole par la seule tutelle, 461 / 449 ; garder un UAI si une ligne a une voie G ou T, 446 / 434 (non recommandé : retire de vrais lycées généraux). 11 lycées militaires ou Légion d'honneur au niveau national, 1 dans les 8 départements (`0381513N`).
- **Pour H3** : 35 des 447 UAI ont une `date_ouverture` postérieure à 2011. L'instantané ne contient que des établissements ouverts.
- **Lycées hors des aires, vérifié le 20/10** (annuaire du 13/10, aucune donnée sur les cadres) :
  - 104 lycées sont à moins de 10 km d'une aire candidate sans être dans ses communes (70 publics, 34 privés). Marge seule / dont privés : Rennes 8 / 4, Nantes 10 / 5, Toulouse 12 / 3, Bordeaux 11 / 3, Lyon 14 / 5, Grenoble 5 / 1, Lille 36 / 11, Strasbourg 9 / 3. Les départements de l'AAV (`DEP`) ne suffisent pas à les trouver : ils oublient `0560016N` (Morbihan, marge de Rennes) et `0260008T` (Drôme, marge de Grenoble).
  - **Piège : la marge de 10 km ne suffit pas pour `dist_lyc_*_min`.** Les comptes à 3, 5 et 10 km sont identiques avec la marge ou avec toute la métropole, mais la distance au plus proche lycée privé est fausse pour 161 communes sur 2 179 avec la marge seule (Toulouse 97, jusqu'à 39,5 km d'écart ; Grenoble 16, Strasbourg 15, Lyon 14, Rennes 12, Bordeaux 5, Nantes 2, Lille 0), et au plus proche lycée public pour 29 communes. Environ 400 paires contiguës sur 5 890 auraient un `d_dist_lyc_prive_min` faux (contiguïté Queen, ordre de grandeur).
  - **Décision du 20/10 (étudiant, à journaliser)** : les lycées de toute la métropole servent à l'accessibilité, 2 413 UAI, tous géolocalisés. Le paramètre `marge_km` prévu pour `accessibilite.indicateurs` (§12.2 du plan) devient inutile.
  - Les comptes d'exposition à 10 km du journal A4 ont été faits sans les lycées hors des aires. Avec eux, communes exposées à 10 km (sans eux) : Strasbourg 53 (29), Lyon 242 (193), Lille 173 (143), Bordeaux 93 (78), Nantes 64 (58), Toulouse 81 (77), Rennes 52 (50), Grenoble 65 (65). À 5 km, Rennes (15), Nantes (19) et Toulouse (20) concordent avec A4. Le tableau de support est donc à recalculer, sans reprendre les chiffres de A4.
- **Frontières** : l'annuaire ne contient pas les lycées belges ni allemands, et rien ne permet de corriger leur absence avec cette source.
  - 110 des 201 communes de l'aire de Lille et 55 des 268 de Strasbourg ont leur centroïde à moins de 10 km de la frontière (59 et 24 à moins de 5 km).
  - Le lycée privé français le plus proche est plus loin que la frontière pour 57 communes de Lille et 75 de Strasbourg : leur distance est peut-être surestimée.
  - Communes non exposées dont le disque franchit la frontière : à 10 km, Lille 9 sur 28 et Strasbourg 35 sur 215 ; à 5 km, Lille 33 sur 125 et Strasbourg 21 sur 257. Elles sont surtout dans les anneaux de 0 à 10 km, que la comparaison par anneaux ne protège donc pas.
  - Distance à la frontière : `geo.distance_contour_national_km` mesure la distance au contour de l'union des départements métropolitains (copie gelée du 20/10), qui suit aussi le littoral. Elle ne vaut distance à la frontière que loin des côtes : elle sert donc pour Lille et Strasbourg seulement (A6), où le point le plus proche est toujours sur la frontière terrestre ; à Bordeaux, le contour est maritime (21 et 50 communes à moins de 5 et 10 km).
  - À soumettre au pilote, puisque cela touche le choix des aires (§2.2).
- **Accessibilité, vérifié le 20/10 avec `accessibilite.indicateurs`** (annuaire du 13/10, aucune donnée sur les cadres) :
  - communes exposées (au moins un lycée privé sous contrat dans le rayon), à 5 km / 10 km : Bordeaux 27 / 93, Grenoble 24 / 65, Lille 76 / 173, Lyon 93 / 242, Nantes 19 / 64, Rennes 15 / 52, Strasbourg 11 / 53, Toulouse 20 / 81. `dist_lyc_prive_min` va jusqu'à 43,4 km ;
  - **sensibilité au bord du rayon** : 10 couples centroïde-lycée sont à moins de 1 m d'un rayon ; deux font basculer l'exposition d'une commune au public (38486 à 3 km, lycée à +0,38 m ; 35023 à 5 km, à −0,40 m), aucun au privé. Ces comptes ne sont stables que sur un annuaire gelé (amendement A2, pas encore fait) ;
  - **géolocalisation peu précise** : parmi les 443 lycées à moins de 10 km des aires, deux publics sont localisés à la ville ou au lieu-dit (`0380081G`, aire de Lyon ; `0380032D`, Grenoble) ; tous les privés le sont au moins à la rue ;
  - 17 UAI partagent 7 positions (sites communs), toutes à 16,7 km ou plus d'un centroïde des aires : sans effet aujourd'hui sur les `n_lyc_*`.
- **Pour H4** (§5.7, même fonction sur d'autres points) : `indicateurs` compte chaque ligne. Pour la BPE et Data ES (plusieurs équipements par site), fixer l'unité et dédoublonner avant l'appel, et vérifier l'unicité du code UIC des gares. Filtrer la BPE par type et sur la métropole avant l'appel : sur 1 million de points synthétiques, l'appel prend 69 s, dont 63 s pour la distance au plus proche (`points.sindex.nearest(..., return_distance=True)` ferait le même calcul en 0,4 s). Les gares allemandes (Kehl, pour Strasbourg) manquent aux données SNCF, comme les lycées étrangers.

## 4. IPS des lycées (source 5)

- **Jeu** : `fr-en-ips-lycees-ap2023` (Opendatasoft), moissonné par data.gouv.fr (dataset `664d720768d6ab64e06740f0`). Licence Ouverte v2.0.
- **URL à utiliser** : `https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-ips-lycees-ap2023/exports/csv`. Le lien de data.gouv ajoute `?use_labels=true` et donne des libellés français à la place des noms techniques ; le contenu est identique. Garder les noms techniques.
- **Format** : `;`, UTF-8 avec BOM, point décimal, manquants = chaîne vide. 10 905 lignes, 48 colonnes, une ligne par lycée et par rentrée (clé : `uai` + `rentree_scolaire`). Rentrées 2023-2024 (3 612 lignes), 2024-2025 (3 631), 2025-2026 (3 662). `/records` plafonne à 10 000 lignes : utiliser l'export.
- **Colonnes** : `rentree_scolaire`, `code_region`, `code_region_insee`, `region_academique`, `code_academie`, `academie`, `code_du_departement`, `departement`, `code_insee_de_la_commune`, `nom_de_la_commune`, `uai`, `nom_de_l_etablissement`, `secteur` (`public`, `privé sous contrat`), `type_de_lycee` (`LEGT`, `LPO`, `LP`), `ips_voie_gt`, `ips_voie_pro`, `ips_post_bac`, `ips_etab`, `ecart_type_voie_gt`, `ecart_type_voie_pro`, `ecart_type_etablissement`, plus 27 colonnes de référence `ips_national_*`, `ips_academique_*`, `ips_departemental_*`, **recopiées sur chaque ligne** : ce ne sont pas des variables d'établissement.
- **Manquants** : `ips_voie_gt` 31,5 %, `ips_voie_pro` 42,7 %, `ips_post_bac` 44,5 %, `ips_etab` 5 lignes (toutes privé sous contrat). Les remplissages par type : LEGT `ips_voie_gt` 97,9 % ; LPO 94,2 % ; LP `ips_voie_pro` 99,9 %.
- **Ce qui manque à la source** : pas de coordonnées, pas d'effectifs, pas de privé hors contrat. Le §5.6 du plan (robustesse hors contrat) ne pourra pas utiliser l'IPS.
- **Jointure** : sur `uai`, sans doublon par rentrée. Mais 24 UAI changent de `type_de_lycee` entre rentrées (filtrer par rentrée), 8 changent de commune, 525 changent de nom. Ne garder de cette source que `uai`, `secteur`, `type_de_lycee` et l'IPS ; la géographie vient de l'annuaire.
- **Écart public/privé** (rentrée 2025-2026, métropole, moyennes simples non pondérées de `ips_etab`) : LEGT privé 130,3 contre public 114,9 (+15,4) ; LPO 116,0 contre 102,3 (+13,7) ; LP +17,4. LEGT et LPO regroupés : 126,9 contre 109,1 (+17,8). Écart stable sur les 3 rentrées.
- **Vérifié à T6 (13/10)** :
  - deux téléchargements de l'export à 20 s d'écart sont identiques octet pour octet (3 627 001 octets, sha256 `31b2aafd8fb4597608c55f8f78f7144444a350df795111a651fb5222ee9c8aa7`, dans `config.SHA256_IPS`) ; `collecte.ips_lycees` échoue si la source change ;
  - lycées LEGT et LPO, France : `ips_voie_gt` renseigné à 96-97 % selon la rentrée, `ips_etab` à 100 % ; écart privé − public (moyennes simples) de 17,4, 17,8 et 18,2 points pour `ips_voie_gt` en 2023-2024, 2024-2025 et 2025-2026 (17,8, 18,2 et 18,5 pour `ips_etab`) ;
  - dans les communes des 8 aires candidates (rentrée 2025-2026, `ips_voie_gt`) : 339 lycées dont 9 sans IPS ; l'écart privé − public d'une même aire varie de 5,3 points au plus selon la mesure et la rentrée, un peu plus que le seuil de 3 points de la DEPP ; recalculé depuis le seul fichier IPS (commune de l'IPS), la moyenne d'une aire change de 0,6 point au plus (Nantes, privé : 135,7 contre 135,1), cause non vérifiée ;
- **Mises en garde de la DEPP** : ne pas sur-interpréter des différences de 3 points ou moins ; la remontée de la 2e PCS a augmenté dans le privé sous contrat à la rentrée 2023 (environ +3 points d'IPS).
- **Données 2025-2026** : ajoutent des COM et la Nouvelle-Calédonie ; un filtre « métropole » = longueur du code département ≤ 2. Le code `99130` (Andorre-la-Vieille) est étranger.

## 5. IVAL, lycées généraux et technologiques (source 6)

- **Jeu** : `fr-en-indicateurs-de-resultat-des-lycees-gt_v2` (data.gouv : `6707515c84dfa4012c3ecd45`). Dernier traitement 2026-04-03, session 2025 incluse.
- **URL à utiliser** : `https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-indicateurs-de-resultat-des-lycees-gt_v2/exports/csv` (sans `use_labels`). L'export est généré à la demande : garder une copie brute sur S3.
- **Format** : `;`, UTF-8 avec BOM, CRLF, point décimal. 32 485 lignes, 88 colonnes, une ligne par `uai` et `annee` (session du bac, 2012 à 2025). 2 546 UAI.
- **Colonnes utiles** : `annee`, `uai`, `libelle_uai`, `secteur`, `code_commune`, `libelle_commune`, `code_departement`, `libelle_departement`, `libelle_academie`, `code_region`, `libelle_region`, `presents_total` (poids, jamais manquant), `eff_2nde`, `taux_acces_2nde` et `va_acces_2nde` (indicateur principal du plan), `taux_reu_total` et `va_reu_total`, `taux_men_total` et `va_men_total`, `eff_1ere`, `eff_term`.
  - Toutes en points de pourcentage et en entiers. `va_acces_2nde` va de −77 à 46, moyenne ≈ −1,1.
  - Pas de colonne de taux attendu : attendu = `taux_acces_2nde` − `va_acces_2nde` (référence : France entière, public et privé sous contrat).
  - `taux_men_total` et `va_men_total` sont vides de 2012 à 2016.
- **Libellés abîmés** (`MARMAE`, `?` à la place des accents) : joindre uniquement sur `uai` et `code_commune`.
- **Manquants** : `va_acces_2nde` manquant sur 580 lignes (1,8 %), dont 58 lycées sans aucune valeur. **Rupture en 2024** : le seuil de présents passe de 20 à 40, donc 4,8 % de manquants en 2024 et 6,0 % en 2025, dont 91 des 140 de 2025 dans le privé sous contrat.
- **Comparabilité dans le temps** : `taux_acces_2nde` n'est pas comparable d'une session à l'autre (moyenne 68,2 en 2012, 76,4 en 2017, 87,9 en 2020, 85,1 en 2025), à cause de changements de définition en 2016 et 2017.
- **Stabilité de `va_acces_2nde`** (corrélation d'un lycée entre deux sessions) : 0,56 à 1 an, 0,43 à 3 ans, 0,32 à 5 ans, 0,18 à 10 ans, 0,12 entre 2012 et 2025 (ICC(1) = 0,34). **Risque pour H3**, qui relie l'IVAL récent à l'évolution des cadres 2011-2022 ; moyenner plusieurs sessions atténue le bruit. Le plan (§3.2) prévoyait ce risque.
- **Contrôles du 13/10 pour l'amendement A1, sans aucune donnée sur les cadres** (recalculés sur l'export complet) :
  - corrélation entre les moyennes par lycée de 2012-2017 et de 2018-2022 : 0,49 à 0,50 (n = 2 232 à 2 302 selon qu'on exige une ou plusieurs sessions par période), soit 0,65 à 0,66 pour la moyenne complète après correction de Spearman-Brown. La règle d'inclusion est à figer au ticket ;
  - pas de rupture de `va_acces_2nde` entre 2016 et 2017 (corrélation 0,595), alors que `taux_acces_2nde` change de définition ;
  - 205 des 2 515 lycées de la fenêtre 2012-2022 ont moins de 5 sessions valides ;
  - `va_acces_2nde` manquant : 0,5 % (privé sous contrat) et 0,6 % (public) en 2023, 9,1 % et 2,6 % en 2024, 11,6 % et 3,1 % en 2025.
- **Ancienne version** (data.gouv `5889d042a3a72974c1f0d607`) : valeurs identiques à la v2 sur les 27 808 lignes communes, donc pas de millésime indépendant pour tester la stabilité ; la v2 contient déjà 14 sessions.
- **Jointure avec l'annuaire** : 94,3 % des 2 457 lycées GT de l'annuaire sont dans l'IVAL 2025 ; 6 UAI IVAL 2025 n'existent pas comme lycée dans l'annuaire. **Trois privés de Saint-Sébastien-sur-Loire** (`0440256P`, `0440279P`, `0441653H`, aire de Nantes) sont fusionnés dans l'annuaire sous l'UAI `0443088T` (multi-sites) : une jointure naïve les perd. 16 UAI changent de `code_commune` selon la session.
- **Non lus** : les guides méthodologiques 2016, 2020 et 2023 (seul celui de 2025 l'a été, partiellement).
- **Ticket IVAL, vérifié le 20/10** (aucune donnée sur les cadres) :
  - export CSV identique sur 4 téléchargements (sha256 `6ab77b39…de8658`, 8 231 883 octets, `data_processed` 2026-04-03) ; le Parquet aussi, mais `annee` y est une date ;
  - règle A1 : 2 182 des 2 413 lycées retenus ont une IVAL (302 sur 339 dans les 8 aires) ; presque tous ont les 11 sessions. 599 communes des 8 aires ont un `ival_moy_5km`, contre 658 avec au moins un lycée à 5 km : 59 communes n'ont près d'elles que des lycées sans IVAL, surtout des ouvertures récentes en périurbain (Toulouse, Bordeaux), à prendre en compte pour la population de H3 ;
  - 2016 est atypique : seule session sans seuil de présents (78 lignes sous 20 présents), plus de lignes et plus de valeurs ajoutées manquantes ;
  - **piège : des lycées publient leur IVAL sous un autre UAI que celui de l'annuaire**, et perdent leur IVAL sans erreur dans une jointure par UAI. Dans les 8 aires : les trois privés de Saint-Sébastien-sur-Loire (`0440256P`, `0440279P`, `0441653H`), regroupés en 2026 sous `0443088T` ; Philippe Cousteau (Bordeaux, `0332346W`), dont l'IVAL est publiée sous sa section d'enseignement général `0332835C` ; Chevreul Lestonnac (Lyon 7e, `0690535G`), absorbé en 2019 par `0690574Z`. Rattachés par `config.UAI_IVAL_RATTACHES` ; `lycees_geo` échoue si un autre lycée de l'IVAL des aires manque aux lycées retenus hors de `config.UAI_IVAL_NON_RETENUS` (7 lycées : professionnels, climatique, agricole, hors contrat, Sainte-Claire fermé). Le contrôle ne porte que sur les communes des aires, pas sur la marge ;
  - effet des rattachements : 0443088T −5,98 (poids 287), 0332346W −3,91 (175), 0690574Z −11,49 (217, contre −9,4 sans les sessions de 0690535G).

## 6. cartiflette, contours communaux (source 7)

- **Installation** : `uv add "cartiflette==0.4.0"` depuis PyPI. Testé avec Python 3.13.15. Dépendances : `duckdb>=1.5`, `geopandas>=1.0.1`, `pyarrow>=17`.
  - `pip install git+https://github.com/inseefrlab/cartiflette` installe `cartiflette-pipeline 0.5.0`, qui n'a pas `carti_download`. La forme qui marche : `…#subdirectory=python-package/cartiflette`.
  - **Épingler la version** : le client a été réécrit le 26/09/2026 (0.2.0), la 0.3.0 (06/10) a changé la simplification par défaut, la 0.4.0 date du 12/10. Les 0.1.x ne lisent pas les millésimes 2023 et plus.
  - Au premier appel, duckdb installe les extensions `httpfs` et `spatial` (accès à extensions.duckdb.org nécessaire). Les données sont lues sur `minio.lab.sspcloud.fr/projet-cartiflette`, sans identifiant. Non observé : un SSPCloud réellement neuf.
- **Signature** (copiée de `inspect.signature`) : `carti_download(values, borders='COMMUNE', filter_by='REGION', territory='metropole', vectorfile_format='auto', year=None, crs=4326, simplification=None, bucket='projet-cartiflette', path_within_bucket='production', provider='IGN', dataset_family='ADMINEXPRESS', source='EXPRESS-COG-CARTO-TERRITOIRE', filename='raw', return_as_json=False, engine='geopandas', con=None, force=False, where=None)`.
- **Trois défauts qui contredisent le plan (§2.1)** : `year=None` vaut l'année courante (2026) donc toujours `year=2025` ; `simplification` vaut 80 par défaut donc passer `simplification=0` (sinon les centroïdes bougent, de 52 m au maximum sur le département 35) ; seul EPSG:4326 est publié (`crs=2154` lève une erreur), donc `.to_crs(2154)`.
- **Appel testé** : `carti_download(values="35", borders="COMMUNE", filter_by="DEPARTEMENT", year=2025, simplification=0)` → 332 communes, EPSG:4326, aucune géométrie vide. Millésimes 2022 à 2026 disponibles. `filter_by` accepte aussi `AIRE_ATTRACTION_VILLES` (par exemple `values="013"` pour Rennes, 183 communes).
- **Colonnes** : `ID`, `NOM`, `INSEE_COM`, `STATUT`, `POPULATION`, `AREA`, `CTCD`, `EPCI`, `EPT`, `ARR`, `CANOV`, `ZE2020`, `UU2020`, `AAV2020`, `BV2022`, `INSEE_DEP`, `INSEE_REG`, `LIBELLE_DEPARTEMENT`, `LIBELLE_REGION`, `PAYS`, `SOURCE`, `geometry`. `AREA` désigne un territoire (`metropole`, `martinique`…), pas une surface. Le millésime de `POPULATION` n'est pas documenté.
- **Exactitude** : les 34 875 communes de 2025 correspondent exactement au fichier Insee `v_commune_2025.csv`. `AAV2020` est identique à la table Insee, mais il n'y a **pas** `CATEAAV2020` (pôle ou couronne) : la source 8 reste nécessaire.
- **Arrondissements** : avec `borders="COMMUNE_ARRONDISSEMENT"`, Lyon passe de 397 à 405 unités. `INSEE_COM` garde le code du **parent** (69123) et n'est pas unique ; le code d'arrondissement est dans `INSEE_COG` (unique, égal à `INSEE_COM` pour les autres communes). `STATUT` vaut `Arrondissement municipal`.
- **Vérifié à T3 (13/10)** : `carti_download(values=<code AAV>, borders="COMMUNE_ARRONDISSEMENT", filter_by="AIRE_ATTRACTION_VILLES", year=2025, simplification=0)` marche pour les 8 aires candidates. Les `INSEE_COM` sont exactement les `CODGEO` de la table AAV de l'aire ; seule Lyon a plus d'unités (405 pour 397 communes : 69123 est remplacée par 69381 à 69389). EPSG:4326, aucune géométrie vide, `AAV2020` de cartiflette égal au code demandé. Un code d'aire inexistant lève `ValueError` (« No AIRE_ATTRACTION_VILLES 999 »). `collecte.contours_aire` garde une copie brute GeoParquet par aire dans `raw/`.
- **Centroïdes hors de leur commune** (vérifié le 20/10) : 35168, 31587, 33123, 33035, 01262, 38387, 59237, 59106 et 67043 (33035 et 38387 sont même hors de l'aire, à 397 m et 78 m du contour). Conforme au §2.4 (centroïde géométrique), à signaler dans l'encadré « choix et biais » ; la variante chef-lieu de la robustesse y répond.
- **Autres** : 6 communes ont `POPULATION == 0`. La commune-centre « la plus peuplée du pôle » serait Lyon 3e au niveau arrondissement : la définir au niveau commune ou par `CATEAAV2020 == '11'`.
- **Alternative si besoin** : `https://geo.api.gouv.fr/communes?codeDepartement=35&format=geojson&geometry=contour&fields=code,nom,population` (COG courant, pas épinglé à 2025).

## 7. Zonage en aires d'attraction des villes 2020 (source 8)

- **Fichier** : « Base des aires d'attraction des villes 2020 », page `https://www.insee.fr/fr/information/4803954`. Lien direct, géographie au 01/01/2025 : `https://www.insee.fr/fr/statistiques/fichier/4803954/AAV2020_au_01-01-2025.zip` (1 104 231 octets ; contient `AAV2020_au_01-01-2025.xlsx`). sha256 du zip : `738f81b12832fe294bd24ddbfe3a31830c20d850143fc8b4393f18d4b8ee8181` (calculé et contrôlé le 13/10 par `collecte.aav_2020`, qui l'a dans `config.SHA256_AAV`). Le millésime 2026 existe (`…AAV2020_au_01-01-2026.zip`) mais il est identique commune par commune sur ces colonnes : rester sur 2025.
- **Lecture** : feuille `Composition_communale`, lignes 1 à 4 de métadonnées, noms de variables à la ligne 6 : `pd.read_excel(chemin, sheet_name="Composition_communale", header=5, dtype=str, engine="calamine")` → 34 875 lignes, 7 colonnes (testé). Le CSV est lu en `dtype=str` pour garder `013`.
- **Colonnes** : `CODGEO`, `LIBGEO`, `AAV2020`, `LIBAAV2020`, `CATEAAV2020`, `DEP`, `REG`.
- **`CATEAAV2020`** (libellés dans la feuille `Documentation`, à écrire en dur dans `config.py`) : `11` commune-centre (692), `12` autre commune du pôle principal (1 017), `13` commune d'un pôle secondaire (33), `20` commune de la couronne (24 236), `30` commune hors attraction des villes (8 897, c'est-à-dire `AAV2020` = `000`).
- **Les 8 aires candidates** (COG 2025)

| Aire | `AAV2020` | Communes | Pôle (11+12) | Couronne (20) | Commune-centre | Départements présents |
|---|---|---|---|---|---|---|
| Rennes | `013` | 183 | 5 | 178 | 35238 | 22, 35 |
| Nantes | `008` | 116 | 7 | 109 | 44109 | 44, 85 |
| Toulouse | `005` | 527 | 18 | 509 | 31555 | 09, 11, 31, 32, 81, 82 |
| Bordeaux | `006` | 275 | 18 | 257 | 33063 | 17, 33, 40 |
| Lyon | `002` | 397 | 30 | 367 | **69123** | 01, 38, 42, 69 |
| Grenoble | `014` | 204 | 16 | 188 | 38185 | 38 |
| Lille (partie française) | `004` | 201 | 37 | 164 | 59350 | 59, 62 |
| Strasbourg (partie française) | `010` | 268 | 11 | 257 | 67482 | 57, 67, 88 |

  Chaque aire a une seule commune-centre et aucun pôle secondaire. Rennes déborde sur le 22 et Nantes sur le 85 : à inclure dans la requête de l'annuaire.
- **Lyon et les arrondissements** : cette base ne contient que `69123`. Les arrondissements 69381 à 69389 sont dans la **table d'appartenance géographique** (`https://www.insee.fr/fr/statistiques/fichier/7671844/table-appartenance-geo-communes-2025.zip`, feuille `ARM`, 45 lignes : 20 Paris, 16 Marseille, 9 Lyon), avec `AAV2020` = `002` et `COM` = `69123`. Avec les arrondissements, l'aire de Lyon compte 405 unités et la vérification « même nombre de communes que la table AAV » (§4, étape A) ne tient plus telle quelle.
- **Pièges** : un `CODGEO` n'est jamais en double mais « Valence » correspond à deux codes, donc filtrer sur `AAV2020`. 8 897 communes hors aire. La table d'appartenance ne contient ni `CATEAAV2020` ni `LIBAAV2020`.

## 8. Table de passage des codes communes (source 9)

- **Fichier recommandé** : table de passage annuelle 2025, page `https://www.insee.fr/fr/information/7671867`, lien direct `https://www.insee.fr/fr/statistiques/fichier/7671867/table_passage_annuelle_2025.zip` (960 555 octets ; contient `table_passage_annuelle_2025.xlsx`). Ne pas prendre le millésime 2026 de la même page. sha256 du zip : `803527a0…787d595b`.
- **Lecture** : feuille `COM`, titres aux lignes 1 à 4, libellés à la ligne 5, noms de variables à la ligne 6 : `pd.read_excel(chemin, sheet_name="COM", header=5, dtype=str, engine="calamine")` → 36 760 lignes, 47 colonnes, en 2,7 s (testé).
- **Colonnes** : `NIVGEO` (`COM` ou `ARM`), puis pour chaque année de 2003 à 2025 `CODGEO_<année>` et `LIBGEO_<année>`. Une case vide = la commune n'existait pas cette année-là.
- **Une ligne par chemin de filiation, pas par commune** : 850 communes de 2025 ont plusieurs lignes (maximum 22). **Réduire à des paires uniques `(CODGEO_<année>, CODGEO_2025)` avant de joindre**, sinon les sommes sont comptées plusieurs fois.
- **Quelle colonne joindre pour la source 1** : `CODGEO_2013` pour la feuille `COM_2011` et `CODGEO_2024` pour la feuille `COM_2022`, et non l'année du recensement. L'écart est nul dans les deux sens (hors les 20 arrondissements de Paris), ce qui rejoint la documentation de l'Insee.
- **Fusions et scissions** : 837 communes de 2025 sont formées de plusieurs codes de RP2011 (46 pour RP2022). Une scission rend le 1 pour 1 impossible : 55298 (2011) donne 55138 et 55298 ; 76108 et 76676 pour 2011 ; 15141 pour 2022 donne 5 communes. Aucune dans les 8 départements candidats (elles sont dans le 55, le 76 et le 15). Options : zone regroupée (recommandation de l'Insee), répartition par poids, ou exclusion.
- **Poids** : 4,93 % des codes de RP2011 (1,03 % des cadres en emploi) et 0,19 % de ceux de RP2022 (0,07 %) ne sont pas dans le COG 2025 mais ont une cible. Après passage, 18 communes de 2025 n'ont aucune ligne de source (Paris `75056` et Mayotte). Le critère « moins de 1 % sans correspondance » de l'étape B est tenable.
- **Écartés** : la table cumulée `table_passage_geo2003_geo2025` (sans année, mélange toutes les époques, pas d'arrondissements) et le fichier des mouvements `v_mvt_commune_2025.csv` (14 écarts avec la table annuelle sur la géographie 2013, des fusions suivies d'un rétablissement).
- **Changements de département** (4 entre 2011 et 2025) : Freigné 49144 vers 44180, Pont-Farcy 14513 vers 50592, Le Fresne-sur-Loire 44060 vers 49160, Gernicourt 02344 vers 51171. Tous couplés à une fusion.
- **Test** : un `assert` d'une seule cible par code source, sauf les scissions listées.

## 9. Variable à expliquer : séries historiques de population active (source 1)

- **Page** : `https://www.insee.fr/fr/statistiques/1893185`, « Structure de la population active de 25 à 54 ans selon la catégorie socioprofessionnelle, selon le niveau de diplôme, selon le sexe ou le secteur d'activité (1968 à 2022) », parue le 04/12/2025.
- **Fichier** : `https://www.insee.fr/fr/statistiques/fichier/1893185/pop-act2554-csp-cd-6822.zip` (27 601 928 octets ; un xlsx de 29 917 320 octets). sha256 du zip : `cdbcb350a9c1315135471fc7f40e60e578428735eb6b1f8756ec26da82d4e168`. **Pas de version CSV.** La même page propose 5 autres zips, dont `pop-act2554-empl-csp-cd-trav-6822.zip`, qui donne la CSP au **lieu de travail** : ce n'est pas celui-là.
- **Contenu** : 21 feuilles : `Présentation`, `Documentation`, `Modifications_territoriales`, `DEP_1968` à `DEP_2022`, `COM_1968`, `COM_1975`, `COM_1982`, `COM_1990`, `COM_1999`, `COM_2006`, `COM_2011`, `COM_2016`, `COM_2022`. Actifs de 25 à 54 ans, 6 groupes de CSP (1 agriculteurs, 2 artisans-commerçants-chefs d'entreprise, **3 cadres et professions intellectuelles supérieures**, 4 professions intermédiaires, 5 employés, 6 ouvriers), chacun croisé avec la position : 1 en emploi, 2 chômeur. Champ cité : « actifs ayant un emploi et chômeurs ayant déjà eu un emploi, âgés de 25 à 54 ans ».
- **Lecture** : feuille `COM_2022` ou `COM_2011`, noms de variables à la ligne Excel 16, données dès la ligne 17 : `pd.read_excel(chemin, sheet_name="COM_2022", header=15, dtype=str, engine="calamine")` → 38 214 lignes, 18 colonnes (testé), puis conversion des 12 colonnes de valeurs en nombres. Sans calamine : environ 1 000 lignes vides en fin de feuille.
- **Colonnes** : `RR`, `DR`, `CR`, `STABLE`, `DR24`, `LIBELLE`, puis 12 colonnes `csx_rec{CS}taxtypac_rec{T}rpop{ANNEE}` avec CS de 1 à 6 et T = 1 (en emploi) ou 2 (chômeurs). L'année change d'une feuille à l'autre (`rpop2011`, `rpop2016`, `rpop2022`) : construire les noms dans le code.
  - **Cadres** : `csx_rec3taxtypac_rec1rpop2022` + `csx_rec3taxtypac_rec2rpop2022`. Dénominateur : somme des 12 colonnes.
  - **Code commune** = `DR[:2] + CR` (métropole : `DR` sur 2 caractères ; Corse : `2A`/`2B` ; DOM : `DR` sur 3 caractères, prendre les 2 premiers pour obtenir `97101`).
  - Les 364 lignes `DR` = `20` sont des anciens codes corses vides.
- **Géographie** : `COM_2011` = COG au 01/01/2013 ; `COM_2022` = COG 2024 (écart nul avec le COG 2024 ; 68 codes absents du COG 2025 et 8 communes du COG 2025 manquantes). Voir la table de passage (§8).
- **Valeurs** : effectifs pondérés **décimaux** (exploitation complémentaire). Une cellule vide signifie que la commune n'existait pas ce recensement. Parts nationales de cadres : 16,18 % en 2011 et 20,27 % en 2022.
- **Couverture** : 38 214 codes distincts (union des communes de 1968 à 2024). Des données pour 36 683 communes en 2011, 34 937 en 2022, 34 934 aux deux dates ; 1 749 en 2011 seulement (fusionnées depuis) ; 3 en 2022 seulement (55138, 76095, 76601).
- **Petites communes** : 181 communes à zéro actif en 2022 (80 en 2011) : part indéfinie. 57,6 % des communes ont moins de 200 actifs en 2022, mais seulement 7 % des actifs.
- **Pièges** : `STABLE` = `0` s'il y a eu un événement géographique entre 1968 et 2024, ce qui ne rend pas la donnée inutilisable (Lille a `STABLE` = `0` mais inclut déjà Hellemmes et Lomme). Seize communes ont changé de département (feuille `Modifications_territoriales`) : Colombier-Saugnieu a une ligne `38119` vide et une ligne `69299` qui porte les données.
- **Lyon et Marseille** : seulement `69123` et `13055`. **Paris** : 75101-75120, sans 75056.

### Source de substitution : tableaux ACT5

Elle contient les arrondissements et reproduit exactement le fichier série pour les actifs occupés.
- **2022** : `https://www.insee.fr/fr/statistiques/fichier/8581605/TD_ACT5_2022_csv.zip` (11 Mo ; `TD_ACT5V3_2022.csv`, 63 Mo). `;`, format long `NIVGEO;CODGEO;LIBGEO;GS;AGEQ65;SEXE;NB`, 34 858 `COM` et 45 `ARM`. `GS` de 1 à 6 ; `AGEQ65` de `015` à `065` : les 25-54 ans sont `025,030,035,040,045,050`. Point décimal. **COG 2025 exactement.**
- **2011** : `https://www.insee.fr/fr/statistiques/fichier/2048156/BTT_TD_ACT5_2011.zip` (8,6 Mo ; `BTT_TD_ACT5_2011.txt`, 62,5 Mo). `NIVGEO;CODGEO;LIBGEO;CS1_6;AGEQ65;SEXE;NB`, 36 603 `COM` et 45 `ARM`. **Virgule décimale** ; `AGEQ65` de `15` à `65` sans zéro initial : les 25-54 ans sont `25,30,35,40,45,50`.
- **Limite** : actifs occupés seulement, sans les chômeurs. Écart de définition mesuré (cadres sur occupés, contre cadres sur occupés + chômeurs) : 17,38 % contre 16,18 % en 2011, 21,52 % contre 20,27 % en 2022, avec une corrélation de 0,996 entre communes (200 actifs et plus) et un écart médian de 0,62 à 0,69 point.
- **Vérification croisée** : en 2011, égalité avec le fichier série pour les 36 683 communes ; en 2022, égalité pour 34 827 communes sur 34 937, les 110 autres s'expliquant par les fusions de 2025.

## 10. Recensement 2022, évolution et structure de la population (source 2)

- **Page** : `https://www.insee.fr/fr/statistiques/8581696`. **Fichier** : `https://www.insee.fr/fr/statistiques/fichier/8581696/base-cc-evol-struct-pop-2022_csv.zip` (48 961 124 octets ; `base-cc-evol-struct-pop-2022.CSV`, 128,6 Mo, et `meta_base-cc-evol-struct-pop-2022.CSV`). Les données sont diffusées en géographie du 1er janvier 2025.
- **Format** : UTF-8 sans BOM, `;`, CRLF, en-tête ligne 1. 34 903 communes, 313 colonnes : `pd.read_csv(chemin, sep=';', dtype={'CODGEO': str})`.
- **Colonnes utiles** : `CODGEO` ; `P22_POP`, `P16_POP`, `P11_POP` ; tranches d'âge `P22_POP0014`, `P22_POP1529`, `P22_POP3044`, `P22_POP4559`, `P22_POP6074`, `P22_POP7589`, `P22_POP90P`.
  - `P22_POP` a du bruit flottant (`458.999999999999`) : arrondir.
  - Cadres des 15 ans ou plus (**robustesse du plan §2.3 : le plan voit juste**) : 2022 `C22_POP15P_STAT_GSEC13_23` sur `C22_POP15P` ; 2011 `C11_POP15P_CS3` sur `C11_POP15P`. Autres groupes 2022 : `…_GSEC11_21`, `…_GSEC12_22`, `…_GSEC14_24`, `…_GSEC15_25` (employés), `…_GSEC16_26` (ouvriers), `…_GSEC32` (retraités), `…_GSEC40` (autres sans activité). Les retraités et inactifs sont **dans** le dénominateur : ce n'est pas une part parmi les actifs. Parts nationales : 11,4 % en 2022 et 9,5 % en 2011.
  - Variantes par âge : `C22_POP2554_STAT_GSEC11_21` à `C22_POP2554_STAT_GSEC16_26` (les 6 groupes), `…_GSEC32` (retraités), `…_GSEC40` (autres sans activité, chômeurs n'ayant jamais travaillé compris), et en 2011 `C11_POP2554_CS1` à `CS8`. **Piège : `C22_POP2554` compte tous les 25-54 ans, inactifs compris** ; le dénominateur des actifs est la somme des 6 groupes (égale à `C22_POP2554` − `GSEC32` − `GSEC40`).
- **Variable à expliquer et Lyon, vérifié le 20/10** (aucune part ni aucun effectif de cadres des 8 aires n'a été lu : pour Lyon et les aires, seulement des présences et des écarts nuls) :
  - les 25-54 ans par groupe socioprofessionnel « actuel ou antérieur » donnent exactement la définition de la source 1 (occupés + chômeurs ayant déjà travaillé) : numérateur `C22_POP2554_STAT_GSEC13_23` et `C11_POP2554_CS3`, dénominateur la somme des 6 groupes. Totaux nationaux égaux à la source 1 (16,18 % en 2011, 20,27 % en 2022) ; hors des aires, égalité commune par commune avec la source 1 passée au COG 2025 par la table de passage (2022 : 32 701 sur 32 701 ; 2011 : 32 688 sur 32 692, les 4 écarts hors des aires) ; Paris et Marseille égaux ;
  - **les 9 arrondissements de Lyon y sont, en 2011 comme en 2022, en COG 2025** (avec aussi le parent 69123 : ne pas tout sommer) ; leur somme est égale à 69123, qui est égal à la source 1 ;
  - zip sha256 `cb4b918862289527232ad79fb3b712d5f4635c6de5bae762e8d22a132717ed83` (48 961 124 octets), CSV de 313 colonnes : lire avec `usecols` et `dtype={"CODGEO": str}`. Effectifs décimaux (exploitation complémentaire) : ne pas les mélanger avec `P22_POP` (exploitation principale). Le libellé des colonnes `C11_*` dans le fichier `meta` dit « 2010 », mais ce sont les valeurs du recensement 2011 ;
  - seconde voie pour 2022 : tableau détaillé `TD_POP6_2022` (format long, `STAT_GSEC` × `AGEQ65` × `SEXE`), égal pour toutes les communes et les arrondissements de Lyon ; aucun tableau ACT ne croise la CSP avec les chômeurs ;
  - téléchargement tronqué sans erreur observé de nouveau sur un fichier de l'Insee : contrôler la taille ou le sha256.
  - **Communes sans actif (A17), vérifié le 21/10 sans lire les cadres des 3 aires** : hors des 3 aires (34 103 communes), la somme des 6 groupes égale `C22_POP2554` − `C22_POP2554_STAT_GSEC32` − `C22_POP2554_STAT_GSEC40` (écart maximal 5e-10), et `C11_POP2554` − `C11_POP2554_CS7` − `C11_POP2554_CS8` en 2011 (2e-9). Calculé ainsi dans les 3 aires (789 unités, aucune valeur manquante), le dénominateur vaut au moins 12 en 2011 et 12,9 en 2022 : aucune commune sans actif à nommer.
- **Superficie absente de ce fichier.** La densité (§2.5) s'obtient depuis la **série historique 2022** (`https://www.insee.fr/fr/statistiques/fichier/8582555/base-cc-serie-historique-2022_csv.zip`, 6,7 Mo, `base-cc-serie-historique-2022.CSV`) : colonne `SUPERF` en km², sans manquants, même ordre de `CODGEO`, avec aussi `P22_POP` et `P11_POP`.
- **Série historique 2022, explorée le 20/10** (pour le critère (c) et la densité) :
  - zip de 6 714 257 octets, sha256 `ff0187ec6bb77fd2e5da639c08159368ff152cad0682ee0908358a829830c273` (identique sur deux téléchargements), avec `base-cc-serie-historique-2022.CSV` et `meta_base-cc-serie-historique-2022.CSV` ; `;`, UTF-8 sans BOM, CRLF, point décimal ; 34 903 lignes, 72 colonnes. Lire avec `dtype={"CODGEO": str}`. `P22_POP`, `P16_POP` et `P11_POP` sont des entiers sans manquant (pas de bruit flottant, contrairement à « évolution et structure ») ; `SUPERF` sans manquant ni zéro ;
  - COG 2025 : les 34 875 codes de l'AAV y sont, sauf Mayotte (17 codes) ; **les 45 arrondissements et leurs parents (69123, 13055, 75056) sont tous présents : double comptage** si l'on somme tout le fichier ou si l'on joint l'AAV et les arrondissements ensemble. Pour Lyon au grain arrondissement, prendre les 9 arrondissements sans 69123 ;
  - les 8 aires sont complètes. Somme de `P22_POP` (habitants) : Rennes 780 549, Nantes 1 041 894, Toulouse 1 513 396, Bordeaux 1 412 388, Lyon 2 327 861, Grenoble 724 742, Lille 1 528 848, Strasbourg 868 665 ;
  - la colonne `POPULATION` des contours cartiflette déjà en `raw/` vaut `P22_POP` pour les 2 179 unités des aires, arrondissements compris ;
  - `SUPERF` et la surface des contours en Lambert 93 diffèrent de plus de 10 % (rapporté à `SUPERF`) pour 28 unités sur 2 179 (44188 : 58,81 contre 97,82 km²) ; surtout des communes à grands plans d'eau ou estuaires (lac de Grand-Lieu, Hourtin-Carcans, Loire, Gironde), mais 9 ont une `SUPERF` plus grande que la surface IGN (jusqu'à 1,38, Saint-Alban-de-Roche), sans explication vérifiée. Corrélation de rang entre les deux densités d'au moins 0,997 dans chaque aire. **Décidé le 20/10 : `SUPERF`**, codé dans `collecte.serie_historique_rp2022` et `nettoyage.population` (à journaliser) ;
  - **densité très asymétrique** (de 4 à 19 232 hab/km² dans les 8 aires ; asymétrie 8,2, 0,4 en log) : dans les paires, 43 paires sur 5 890 (arrondissements de Lyon et Villeurbanne) font 34 % de la somme des carrés de `d_densite`, et `d_log_densite` est corrélé à `d_dist_lyc_prive_min` de −0,21 à −0,46 selon l'aire. Un contrôle linéaire en densité brute serait piloté par le centre de Lyon : forme et place du contrôle à fixer en `/pilotage` avant T5 ;
  - `P22_POP` est décrite par le fichier `meta` comme « Population en 2022 (princ) », c'est-à-dire de l'exploitation principale.
  - **piège de téléchargement** : un premier téléchargement d'« évolution et structure » (49 Mo) a été tronqué sans erreur (`curl` a rendu 0) ; seul le `sha256` le révèle.
- **Pièges**
  - **Dictionnaire de la page faux** : il nomme les employés `C22_POP15P_STAT_GSEC16_25` (en doublon avec `…_GSEC16_26`). Le fichier et le `meta_*.CSV` donnent `…_GSEC15_25`. Recopier les noms depuis l'en-tête.
  - `REG`, `DEP` et `LIBGEO` sont annoncés par la page mais absents du CSV ; les libellés sont dans `meta_*.CSV` (lignes `COD_VAR == 'CODGEO'`).
  - **Double comptage** : les parents 75056, 69123 et 13055 sont présents avec leurs arrondissements. Retirer les 3 parents garde la France hors Mayotte (71 272 267 → 67 760 573 habitants).
  - 4 communes entièrement vides (15031, 15035, 15047, 15171) ; 6 communes à population 0 (55039, 55050, 55139, 55189, 55239, 55307) : division par zéro à prévoir.
  - 17 communes diffèrent entre ce fichier et la série historique à cause des fusions, et `P11_POP` et `P16_POP` ne sont pas entièrement en COG 2025 (7 communes absorbées ont `P11_POP` manquant). Sans effet sur la robustesse 15+, qui n'utilise que 2022.
  - Les libellés de `meta_*` ne suivent pas le COG 2025.
- **Signalé** : la page « Dossier complet » (5359146, septembre 2026) propose des recensements plus récents (2012, 2017, 2023 en géographie 2026). Le plan reste sur 2022.

## 11. Ce qui n'a pas été vérifié

- **Source 1** : la comparabilité du groupe 3 (cadres) entre 2011 et 2022, qui repose sur la documentation de l'Insee.
- **Source 2** : que `P22_POP` soit la population municipale (cohérent avec 227 830 pour Rennes mais non écrit) ; le fichier xlsx ; la variable `SUPERF` du dossier complet.
- **Annuaire** : les deux jeux d'effectifs du catalogue.
- **IPS** : la pièce jointe de passage PCS vers IPS (absente de l'API) ; la méthode des colonnes `ips_national_*` ; le Parquet généré par data.gouv.
- **IVAL** : les guides 2016, 2020 et 2023 ; la concordance des `code_commune` avec le COG 2025.
- **cartiflette** : un SSPCloud neuf (extensions duckdb) ; le millésime de `POPULATION`.
- **Table de passage** : la légende des codes `MOD` du fichier de mouvements, déduite des lignes.

## 12. Part de cadres par IRIS : bases infracommunales « Activité des résidents » (explorées le 20/10)

Aucune valeur de cadres des 3 aires retenues n'a été lue : seulement des comptes d'IRIS. Les chiffres sur les cadres viennent d'autres aires.
- **2022** : `https://www.insee.fr/fr/statistiques/fichier/8647006/base-ic-activite-residents-2022_csv.zip` (35 900 269 octets, sha256 `f4aefb7fab425b9f7eb802e2afb475908bbf2186e0d88f542cf7a67fc70623cb`), `base-ic-activite-residents-2022.CSV` : `;`, CRLF, point décimal, 49 276 lignes × 119 colonnes, lire `IRIS` et `COM` en chaîne. Cadres `C22_ACT1564_STAT_GSEC13_23` ; 6 groupes `C22_ACT1564_STAT_GSEC11_21` à `…16_26`.
- **2011** : `https://www.insee.fr/fr/statistiques/fichier/2028668/infra-activite-resident-2011.zip` (39 644 845 octets, sha256 `05076a23c7a3e6bab7aadae8e1b12c17ed1a2aff395340edd59df1474719e7ea`), un seul xls : `pd.read_excel(f, sheet_name="IRIS", header=5, dtype=str, engine="calamine")`, 50 867 lignes. Cadres `C11_ACT1564_CS3` ; groupes `C11_ACT1564_CS1` à `CS6`. Feuille « Précision » : CV des cadres d'un IRIS de plus de 18 % sous 50 cadres, 14 % de 100 à 199, 10 % de 200 à 299, moins de 3 % à 1 000 et plus.
- **Piège principal : 15-64 ans seulement.** Aucun fichier IRIS ne croise les 25-54 ans avec la CSP (`P22_ACT2554` existe, sans CSP) : une carte à l'IRIS ne porte pas sur la variable du plan (§2.3). Hors des aires, corrélation de 0,977 entre les parts de cadres 15-64 et 25-54 ans des communes (ACT5 2022, 13 439 communes de 200 actifs et plus).
- **Dénominateur** : la somme des 6 groupes se reconstruit comme pour la commune (écart avec `…_ACT1564` : 1,5 % en 2022, chômeurs n'ayant jamais travaillé). La somme des IRIS égale `TD_ACT5_2022` pour 28 869 communes.
- **Géographie** : données 2022 en IRIS et COG 2024, données 2011 en géographie 2013. Lyon : `COM` en 693xx pour les 185 IRIS des arrondissements, `69123` absent. `69159` (2024) devient `69114` (2025).
- **3 aires** : 1 723 IRIS en 2022 (Nantes 344, Lyon 924, Strasbourg 455), 1 747 en 2011 ; IRIS non découpés (une commune entière) : 87, 342 et 246 ; dénominateur nul (IRIS d'activité ou divers) : 2, 6 et 3 en 2022.
- **Même IRIS en 2011 et 2022** : pas de table unique. Tables `reference_IRIS_geoAAAA.zip` de la page `https://www.insee.fr/fr/information/7708995` (feuille `Modifications_IRIS`, à enchaîner de 2016 à 2024). Dans les 3 aires : 1 695 IRIS stables sur 1 723 ; 13 communes fusionnées (sommer les constituantes de 2011) ; 15 IRIS sans équivalent (Pierre-Bénite, Dardilly, Lyon 9e, Sainte-Luce-sur-Loire, Divatte-sur-Loire).
- **Contours** : cartiflette 0.4.0 a un niveau IRIS, `carti_download(values=<code AAV>, borders="IRIS", filter_by="AIRE_ATTRACTION_VILLES", year=2025, simplification=0)` : 344, 924 et 455 polygones, EPSG:4326, `CODE_IRIS` unique ; millésimes 2025 et 2026 seulement. À Lyon, `INSEE_COM` vaut 69123 : joindre sur `CODE_IRIS` ou `INSEE_COG`. Alternative : IGN CONTOURS-IRIS en 7z (2013 et 2024), dont les polygones diffèrent pour un même code.
- **Plus fin** : les carreaux de 200 m (Filosofi 2019) n'ont aucune CSP.

## 13. Flux de cadres entre communes : fichier détail MIGCOM 2022 (exploré le 20/10)

- **Fichier** : `https://www.insee.fr/fr/statistiques/fichier/8589767/RP2022_migcom.parquet` (183 472 132 octets, sha256 `4c1f5814231c7f670bf190e3cb6711b9b2c48e1637da5a1d59ee90e810384732`), 17 357 182 lignes, 33 colonnes, toutes en chaîne sauf `IPONDI`. Page republiée le 20/10/2026 : à geler. Le zip CSV se télécharge tronqué sans erreur.
- **Variables** : `COMMUNE`, `ARM` (arrondissement, sinon `ZZZZZ`), `DCRAN` (commune un an avant, déjà au grain arrondissement ; `99999` = étranger), `IRAN` (2 = autre logement de la même commune, 3 à 5 = autre commune de métropole, 8 et 9 = étranger), `GS` (`3` = cadres), `GSM`, `AGEREVQ` (`025` à `050`), `LPRM` (`1` = personne de référence), `IPONDI`. Pas d'IRIS.
- **Pièges** :
  - **COG 2024**, pas 2025 : à Lyon, `69159` devient `69114`, qu'une jointure sur le COG 2025 perd sans erreur ;
  - `GS = 3` ne couvre que les cadres **en emploi** (96,2 % du numérateur du plan) : la part du §2.3 ne se refait pas avec MIGCOM ;
  - **sous-échantillon d'environ 1/5** (poids médian 5 dans les petites communes) : dans des aires témoins (Clermont-Ferrand, Grenoble), la commune médiane reçoit 1 à 2 lignes d'arrivées de cadres de 25-54 ans et presque toutes les paires origine-destination n'ont qu'une ligne. Lisible seulement agrégé (anneaux, pôle et couronne) ;
  - départs vers l'étranger invisibles : solde net biaisé.
- **2011** : pas de fichier comparable (premier millésime à 1 an : 2013 ; avec CSP : 2016, en `CS1`).

## 14. Ménages de cadres récemment emménagés par IRIS : fichier détail INDCVI 2022 (exploré le 20/10)

- **Fichiers** : zips régionaux, pas le Parquet national (tronqué sans erreur à 134 Mo sur 488). Zone C (Nantes, Strasbourg) `https://www.insee.fr/fr/statistiques/fichier/8647104/RP2022_indcvizc.zip` (92 019 001 octets, sha256 `a4954aef447625fb5b6a1d8a8b87616d616232a09c37e046a23fc82bfc6645ff`) ; zone E (Lyon) `…/RP2022_indcvize.zip` (131 779 069 octets, sha256 `0943dd298091a758635874afb3bcf7c863811cc9ed588b70455e7513f3d6be63`). Un téléchargement sur cinq s'est arrêté sans erreur : contrôler le sha256.
- **Variables** : `IRIS` (9 caractères, COG 2024), `CATIRIS`, `STAT_GSEC` (`13` et `23` = cadres occupés et chômeurs ayant travaillé, la définition du plan), `PCSL`, `ANEMR` (`00` = moins de 2 ans, `01` = 2 à 4 ans), `IRAN`, `AGEREVQ`, `LPRM`, `NE17FR`, `IPONDI`. Clé ménage `(CANTVILLE, NUMMI)`. Sommes vérifiées égales aux bases IRIS publiques.
- **Pièges** :
  - IRIS seulement pour les IRIS d'au moins 200 habitants des communes découpées : 62 à 72 % de la population des 3 aires ; ailleurs `XXXX` ou `ZZZZZZZZZ` ;
  - « moins de 2 ans » est bruité : environ 10 ménages de cadres par IRIS dans les aires témoins (CV d'environ 30 %), moins de 5 avec enfants ;
  - dans les communes de 10 000 habitants et plus, environ un cinquième des emménagés récents vient d'une pseudo-enquête 2016 (report de l'EAR 2021) ;
  - `ANEMR = 00` ne veut pas dire « arrivé l'an dernier » (24 % sont dans le même logement un an avant).
- **LOGEMT 2022** a l'IRIS et l'année d'emménagement détaillée mais aucune CSP. **INDCVI 2011** existe (texte, virgule décimale, `CS1`, `ANEMR`, sans `IRAN` ni `STAT_GSEC`).
- **Rien de plus fin que l'IRIS** sur la CSP n'est diffusé (secret statistique, arrêté du 19 juillet 2007) : aucune carte « à la rue » ou « par ménage » n'est possible avec des données publiques.

## 15. Gares de voyageurs, SNCF Gares & Connexions (source 12, explorée le 03/11)

- Export Opendatasoft `gares-de-voyageurs` (Parquet ou CSV `;` avec BOM), licence ODbL. data.gouv.fr ne fait que pointer vers ces exports. Retraité chaque jour (`update_frequency` DAILY), sans date ni version : copie gelée du 03/11/2026 (`raw/gares_voyageurs_20261103.parquet`, sha256 dans `config.py`).
- 2 792 lignes, 7 colonnes texte, aucune valeur manquante : `nom`, `libellecourt` (trigramme), `segment_drg`, `position_geographique`, `codeinsee`, `codes_uic`, `id`. Une ligne par gare au sens de G&C ; `id`, `nom`, trigramme et `codes_uic` uniques. 11 gares portent plusieurs codes UIC séparés par `;` (2 805 UIC une fois éclatés, sans doublon).
- Position : WGS84, en WKB dans le Parquet (x = longitude), « lat, lon » dans le CSV. Aucune gare sans position, aucune hors métropole. **Corse : 0 gare** (réseau CFC hors G&C) ; sans effet sur les 3 aires.
- Pas de type TGV / TER. `segment_drg` : A nationale (128), B régionale (1 075), C locale (1 579), combinaisons pour 10 gares multi-UIC. Fréquentation dans le jeu `frequentation-gares` (une ligne par UIC, `total_voyageurs_AAAA` de 2015 à 2024, sans coordonnées, jointure par UIC éclaté : 2 790 gares sur 2 792), non utilisée.
- Aucune colonne de statut : une gare fermée aux voyageurs ne peut pas être repérée dans ce fichier. Pas de halte routière évidente.
- Ordres de grandeur : 58 gares en Loire-Atlantique, 61 dans le Rhône, 94 dans le Bas-Rhin.

## 16. APL aux médecins généralistes, DREES (source 13, explorée le 03/11)

- La page de l'Observatoire des territoires n'offre pas de fichier ; la source est la pièce jointe « Indicateur d'APL aux médecins généralistes.xlsx » du jeu DREES `530_l-accessibilite-potentielle-localisee-apl` (URL dans `config.py`). Le même fichier change à chaque mise à jour annuelle (millésimes ajoutés, anciens archivés à part) : copie gelée du 03/11/2026 (`raw/apl_medecins_generalistes_20261103.xlsx`).
- Feuilles `Paramètres`, `APL 2022`, `APL 2023`, `APL 2024` ; 2024 est le dernier millésime. Titre et notes sur les lignes 0 à 6, en-tête ligne 8, unités ligne 9 (à sauter). Colonnes de 2024 : code et nom de la commune, APL tous âges, APL aux médecins de 65, 62 et 60 ans ou moins (noms finis par une espace en 2024, « et moins » en 2022-2023), population standardisée et population totale 2022 (flottants imprécis).
- Unité : consultations ou visites accessibles par an et par habitant standardisé. Aucune valeur manquante ; 523 zéros en France en 2024, aucun dans le 44, le 67 et le 69.
- Géographie de la feuille 2024 : fusions de 2024 et 2025 appliquées, arrondissements de Paris, Lyon et Marseille à la place de la commune parente, donc le grain du projet ; les 207 communes du 44, les 514 du 67 et les 265 du 69 plus 9 arrondissements y sont. Écarts au COG 2025 hors des aires : scission de 15141 non appliquée, 6 communes « mortes pour la France » de la Meuse et Mayotte absentes. Les feuilles 2022 et 2023 sont en COG antérieur (69152 et 69159 encore présents).
- Variante retenue : APL tous âges de la feuille 2024 (choix du 03/11, à valider par le groupe).

## 17. Équipements sportifs, Data ES (source 15, exploré le 03/11)

- **Piège** : la page data.gouv « recensement-des-equipements-sportifs-espaces-et-sites-de-pratiques-2 » du plan est publiée par la Région Île-de-France et ne couvre que l'Île-de-France (30 075 lignes). Source nationale : API Opendatasoft du ministère, jeu `data-es` (URL dans `config.py`), mis à jour chaque jour : copie gelée du 03/11/2026 (37 Mo).
- **Piège** : un export peut répondre HTTP 200 avec un flux tronqué par un message d'erreur (`ApiError(502 …)`) ; le gel contrôle que le Parquet est complet.
- 333 588 lignes, 115 colonnes ; une ligne par équipement (`equip_numero` unique), 152 034 installations (`inst_numero`), dont 147 277 en métropole. Les équipements d'une installation sont à 52 m les uns des autres en médiane (99e centile 3,3 km : sentiers, sites de nature).
- Position WGS84 en texte (`equip_x`, `equip_y`) ; 1 480 équipements de métropole sans coordonnées ; outre-mer par le préfixe 97 ou 98 de `new_code` (9 235 lignes). Corse incluse.
- Seul indicateur de fermeture : `inst_hs_bool` = « Oui » (462 lignes) ; aucune date de fermeture. `equip_ouv_public_bool` est un arrêté administratif, pas l'ouverture effective.
- Codes communes au COG 2025 à 3 codes près (69159, 25347, 25303, hors des communes utilisées comme référentiel, sans effet sur l'accès calculé par distance) ; arrondissements de Lyon présents. 29 familles, 185 types ; les plus nombreux (boucles de randonnée, terrains de football, city-stades, boulodromes) sont partout.
- Retenu : installations en service de métropole, une par `inst_numero`, au point de son premier équipement. La distance à la plus proche vaut 0,4 à 0,8 km en médiane selon l'aire et ne distingue pas les communes : mesure de H4 = log(1 + nombre d'installations à 5 km).

## 18. Équipements culturels, BPE 2025 de l'Insee (source 14, explorée le 03/11)

- **Piège** : la page data.gouv « base-permanente-des-equipements-2 » du plan est une republication de la BPE 2023 par l'Île-de-France. Source : fichier détail BPE 2025 de l'Insee, page 8217525, `BPE25.parquet` (172 Mo), « actualisé mensuellement » : copie gelée du 03/11/2026.
- **Piège** : le serveur de l'Insee coupe parfois le téléchargement (113 Mo, 47 Mo) en renvoyant HTTP 200, sans Content-Length ; le gel contrôle que le Parquet est complet et il faut parfois réessayer.
- 2 921 770 lignes, 96 colonnes ; une ligne par équipement d'une source administrative (Culture, CNC), sans SIRET pour la culture. Colonnes utiles : `SDOM`, `TYPEQU`, `DEPCOM` (arrondissements de Lyon), `LAMBERT_X`, `LAMBERT_Y`, `EPSG`, `QUALITE_XY`.
- Culture = sous-domaine F3, 7 types en 2025 : F303 cinéma (1 946 en métropole), F305 conservatoire (434), F307 bibliothèque (15 501), F312 exposition et médiation (2 097), F313 patrimoine (549), F314 archives (760), F315 arts du spectacle (1 372). Nomenclature refondue en 2021 : ne pas comparer aux millésimes antérieurs.
- Tous les équipements F3 de métropole ont des coordonnées en Lambert 93 (EPSG 2154) ; qualité bonne 81 %, acceptable 13 % (arrondie à 50 m), mauvaise 6 % (11 % dans le Rhône). DROM dans d'autres projections (UTM), Mayotte sans coordonnées : exclus par `EPSG`.
- Même type au même point : 427 lignes sur 208 points (musée et maison des Illustres, bibliothèque et siège de son réseau) ; dédoublonnées par type et position (219 lignes de moins, environ 1 %).
- Retenu : 22 440 équipements après dédoublonnage. La distance au plus proche vaut 0,8 à 1,8 km en médiane selon l'aire (les bibliothèques sont partout) : mesure de H4 = log(1 + nombre d'équipements à 5 km), comme pour le sport.
