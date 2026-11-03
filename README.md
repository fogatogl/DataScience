# Lycées et géographie des cadres dans trois aires urbaines de province

Projet du cours « Python pour la data science » (ENSAE), rendu le 24 novembre 2026.

## Question

Dans des aires urbaines de province aux traditions scolaires contrastées, les communes offrant un meilleur accès à des lycées privés ou à forte valeur ajoutée concentrent-elles davantage de cadres que leurs voisines, et ce lien résiste-t-il face aux autres infrastructures ?

Le plan complet et le journal des décisions sont dans [`docs/PLAN.md`](docs/PLAN.md). La méthode tient en une page ci-dessous.

## Méthode en bref

**Unité et périmètre.** La commune (les arrondissements à Lyon), au COG 2025, dans trois aires d'attraction des villes (zonage Insee 2020) : Nantes, Lyon et Strasbourg. Elles ont été choisies parmi 8 candidates sur le [tableau de support](docs/tableau_support.md) (poids du privé, taille, nombre de lycées privés, support de l'exposition), avant toute donnée sur les cadres.

**Variable à expliquer.** La part des cadres et professions intellectuelles supérieures parmi les actifs de 25 à 54 ans (occupés et chômeurs ayant déjà travaillé), en 2011 et en 2022, et son évolution en points (Insee, « Évolution et structure de la population » 2022).

**Accès aux lycées.** Lycées généraux, technologiques et polyvalents, publics et privés sous contrat (annuaire de l'éducation du 13/10/2026). Depuis le centroïde de chaque commune, à vol d'oiseau : nombre de lycées à 5 km (3 et 10 km en robustesse), distance au lycée privé le plus proche, valeur ajoutée moyenne des lycées à 5 km (IVAL, taux d'accès de la seconde au bac, sessions 2012 à 2022). Tous les lycées de métropole comptent, y compris hors des aires.

**Contrôles.** Distance au centre de l'aire, densité (en logarithme), aire. Ne sont jamais des contrôles, car en partie des conséquences de la part de cadres : le niveau de vie, l'IPS des lycées et la croissance de la population.

**Hypothèses et comparaisons.**

| | Énoncé | Estimation principale |
|---|---|---|
| H1 | À distance égale du centre, plus de cadres là où l'accès au privé sous contrat est meilleur | Paires de communes contiguës : écart de part de cadres sur l'écart de distance au lycée privé le plus proche, avec les écarts de distance au centre et de densité, sans constante ; intervalles par bootstrap des communes. En complément : anneaux de distance au centre, cellules d'au moins 15 communes exposées et 15 non exposées et d'écart de distance au centre d'au plus 2 km |
| H2 | Lien plus faible dans l'Ouest (Nantes), où le privé est plus répandu | H1 aire par aire, comparée sans test |
| H3 | La qualité des lycées (IVAL), plus que leur nombre, accompagne la hausse de la part de cadres | Régression de l'évolution sur l'IVAL et le nombre de lycées, centrés réduits dans l'aire, effet fixe aire × anneau ; bootstrap par grappes de communes |
| H4 | Lien plus fort avec les lycées qu'avec les autres équipements | Même mesure d'accès pour les gares, les médecins et les équipements |

**Règles de verdict, fixées avant les données.** H1 est « confirmée » si la pente principale va dans le sens attendu avec un intervalle à 95 % qui exclut zéro, si la pente secondaire (nombre de lycées privés à 5 km) va dans le même sens, et si les anneaux estimables aux deux rayons concordent. Elle est « nuancée » ou « infirmée » selon des règles symétriques. Un résultat nul n'est dit « établi » que s'il existe un anneau estimable aux deux rayons ; sinon le verdict est « non concluant ». H3 n'est testable que si la mesure de l'IVAL est assez fiable (au moins 0,5 ; 0,608 mesuré le 20/10), et son verdict se lit sur la différence entre la pente de la qualité et celle du nombre. Les règles complètes sont au §5 du plan.

**Garde-fous.** Les choix sont écrits avant les résultats et chaque écart est daté dans le journal (§13 du plan). Les sources qui changent sans prévenir sont lues dans des copies gelées contrôlées par leur `sha256`. Le projet décrit des associations, pas des effets causaux : causalité inverse (un lycée privé s'installe là où vivent déjà des cadres), sélection résidentielle non observée, distances à vol d'oiseau.

## Résultats clés

À compléter par le groupe une fois l'analyse terminée.

## Reproduire le projet

Python 3.13 et [uv](https://docs.astral.sh/uv/) sont nécessaires.

```bash
uv sync                          # installe les dépendances figées dans uv.lock
uv run pre-commit install        # active nb-clean et ruff avant chaque commit
uv run pytest                    # lance les tests
```

Le rapport est `rapport.ipynb` (pour l'instant le plan du rapport, les Fig. 1 et 3 à 7, les verdicts de H1 et H3, le tableau de robustesse, l'indice de Moran et la carte IRIS ; le texte reste à écrire). Le site se construit avec [Quarto](https://quarto.org/), déjà installé sur le SSPCloud :

```bash
uv run quarto render             # exécute rapport.ipynb et écrit le site dans _site/
```

`uv run` est nécessaire : il donne à Quarto le Python de l'environnement du projet, où `cadres_lycees` est installé.

Sur un compte neuf, les données sont téléchargées depuis les copies gelées publiques décrites ci-dessous, puis gardées dans `data/`.

### Stockage des données

Les données ne sont pas dans Git. `stockage.py` les lit et les écrit :

- sur le S3 du SSPCloud si `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (définies sur un service SSPCloud) et `BUCKET_S3` sont définies. Le nom du bucket dépend du compte : `export BUCKET_S3=<nom du bucket>` (un `export` fait dans un terminal n'est pas vu par un noyau Jupyter déjà lancé). Les fichiers sont dans `s3://<bucket>/projet-cadres-lycees/`, et l'adresse du serveur est lue par s3fs dans `AWS_ENDPOINT_URL`, que le SSPCloud définit aussi ;
- sinon dans le dossier local `data/`, avec un avertissement (c'est le cas d'un compte qui n'a pas défini `BUCKET_S3`).

### Copies gelées des données

Les sources qui changent sans prévenir sont lues dans une copie datée, jamais directement à leur API. Chaque copie est cherchée dans le dossier public `https://minio.lab.sspcloud.fr/gfogato/projet-cadres-lycees/raw/`, puis, si elle y manque ou diffère, dans la release GitHub [`donnees-20261020`](https://github.com/gabrielwenger1-coder/DataScience/releases/tag/donnees-20261020) du dépôt, avec un avertissement. Le code échoue si aucune des deux ne fournit un fichier au `sha256` attendu, et il recontrôle le `sha256` à chaque lecture d'une copie déjà téléchargée.

| Copie | Date | Origine | `sha256` |
|---|---|---|---|
| `annuaire_education_20261013.parquet` | 13/10/2026 | https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/parquet | `2c493f152bc8fc682aa8b1f063392015941bcff36bae2ae59a4d1a1e6334e94a` |
| `gares_voyageurs_20261103.parquet` | 03/11/2026 | https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/gares-de-voyageurs/exports/parquet | `61ccf3392b01cb6785268be7152337f1a95dda93fa9eadf9134901b5f366bc44` |
| `apl_medecins_generalistes_20261103.xlsx` | 03/11/2026 | https://data.drees.solidarites-sante.gouv.fr/api/explore/v2.1/catalog/datasets/530_l-accessibilite-potentielle-localisee-apl/attachments/indicateur_d_apl_aux_medecins_generalistes_xlsx | `21c73deff57dc7a83a3cd6fcfd5b5ceb8c7a40e98590a50b5b1194f2dd4d75a2` |
| `equipements_sportifs_20261103.parquet` | 03/11/2026 | https://equipements.sports.gouv.fr/api/explore/v2.1/catalog/datasets/data-es/exports/parquet | `c78cb234bb591f54660277c5720e5a8275ec26ffacf7120b141024cfba936eef` |
| `bpe_2025_20261103.parquet` | 03/11/2026 | https://www.insee.fr/fr/statistiques/fichier/8217525/BPE25.parquet | `3bad0dc8b02eff0bee86832acf97fdeccef02116bbeb8a6dca2ad0e99d054f6a` |
| `statistiques_dvf_20261103.csv` | 03/11/2026 | https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/dvf/stats_whole_period.csv | `eca12b1b1b45274e315859135d5f4ac15137f3e084712ea9b614b11c4a100722` |
| `ips_lycees_20261013.csv` | 13/10/2026 | https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-ips-lycees-ap2023/exports/csv | `31b2aafd8fb4597608c55f8f78f7144444a350df795111a651fb5222ee9c8aa7` |
| `ival_lycees_gt_20261020.csv` | 20/10/2026 | https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-indicateurs-de-resultat-des-lycees-gt_v2/exports/csv | `6ab77b391e3405f5157bb942d4548d5f1cfbacd94e76dd52b93db9b370de8658` |
| `contours_departements_20261020.parquet` | 20/10/2026 | `cartiflette==0.4.0`, départements de France entière, COG 2025, sans simplification | `a6e4d3b3a7657f61b8fe9b710efa5f50c0cab76cde0d522f4cfd4adfdbe405ca` |
| `contours_aav_<code>_20261013.parquet` | 13/10/2026 | `cartiflette==0.4.0`, contours des communes et arrondissements par aire, COG 2025, sans simplification | `002` : `5fc255ef5f92c540c5037f793c15c24007642c7cdce256a1e4f47d516176f231`<br>`004` : `6ff1e4bc0675ab567b7af3eb506774c0740ab855c5f333c66ee6b8fe1eb89982`<br>`005` : `c42afd4910a9a6907c54e2f8d476b8a4b6db3630bf9ffdff7b41cedf8a3b2c6e`<br>`006` : `6e0cb9a94a69887fd123a2d57c49068aa25b207da9541813652c00f1b2930c28`<br>`008` : `54665ed725b9ae364166d6dc76cd09b71b8e42397916e6fe564d8f0308786e59`<br>`010` : `454d27768198bb48be5882987f3aa36f88902add34bf443dff0cd37cc8be7790`<br>`013` : `c846f8d895d3121435037f5c04054a9e2275bb95e2de1791cae61498550b4cec`<br>`014` : `a1d13c20cc9565de3e2b3bb78b8d020076bae7c2a94ac2648d7aa96aa0699357` |
| `contours_iris_<code>_20261021.parquet` | 21/10/2026 | `cartiflette==0.4.0`, contours des IRIS par aire retenue, COG 2025, sans simplification | `008` : `61e52233fcdd7fe09d0f0350b6a5060719ca83f0a56c7710848a5ae35d34ff23`<br>`002` : `5c77cb03f2cfb55e3e2634218f4f94b6b43f13ed1496e85572919dc271b43018`<br>`010` : `15b57329479d4261de4a443b9b4458332f92692b286caecbb270a3b678aad82c` |

Les fichiers de l'Insee (zonage en aires d'attraction, série historique du recensement 2022, bases IRIS « Activité des résidents » 2011 et 2022, table de passage des codes communes) sont permanents : ils sont lus à leur URL d'origine, avec le même contrôle du `sha256` (voir `src/cadres_lycees/config.py`).

**Refaire un gel** (seulement si le groupe décide de changer de copie, à journaliser au plan) :

```python
from cadres_lycees import collecte

collecte.geler_annuaire("raw/annuaire_education_AAAAMMJJ.parquet")  # renvoie le sha256
collecte.geler_gares("raw/gares_voyageurs_AAAAMMJJ.parquet")
collecte.geler_apl("raw/apl_medecins_generalistes_AAAAMMJJ.xlsx")
collecte.geler_equipements_sportifs("raw/equipements_sportifs_AAAAMMJJ.parquet")
collecte.geler_bpe("raw/bpe_2025_AAAAMMJJ.parquet")
collecte.geler_dvf("raw/statistiques_dvf_AAAAMMJJ.csv")
collecte.geler_contours(
    "raw/contours_aav_013_AAAAMMJJ.parquet",
    valeur="013",
    maille="COMMUNE_ARRONDISSEMENT",
    filtre="AIRE_ATTRACTION_VILLES",
)
collecte.geler_contours(
    "raw/contours_departements_AAAAMMJJ.parquet",
    valeur="France",
    maille="DEPARTEMENT",
    filtre="FRANCE_ENTIERE",
)
collecte.geler_contours(
    "raw/contours_iris_008_AAAAMMJJ.parquet",
    valeur="008",
    maille="IRIS",
    filtre="AIRE_ATTRACTION_VILLES",
)
```

Ces fonctions refusent d'écraser un chemin existant. Il faut ensuite reporter le chemin et le `sha256` dans `config.py`, publier le fichier aux deux adresses ci-dessus et mettre à jour ce tableau.

## Organisation

- `src/cadres_lycees/` : le code du pipeline, un module par étape (voir PLAN §7).
- `tests/` : les tests des calculs critiques (accessibilité et paires de communes contiguës).
- `notebooks/exploration/` : brouillons individuels, jamais rendus.
- `docs/` : le plan, les notes sur les sources de données et le [dictionnaire des variables](docs/dictionnaire_variables.md) de la base communale (`pipeline.construire_base`).
