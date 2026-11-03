"""Constantes du projet : les choix fixés par le plan (§2) et les paramètres des sources."""

from pathlib import Path

# Lambert 93 (mètres) pour tous les calculs de distance, WGS84 pour les cartes interactives
CRS_CALCUL = 2154
CRS_CARTES = 4326

# Rayons d'accessibilité en km : 5 est le rayon principal, 3 et 10 servent en robustesse
RAYONS_KM = (3, 5, 10)
RAYON_PRINCIPAL_KM = 5

# Comparaison par anneaux (PLAN §5.2, A6) : bornes basses des anneaux de distance au centre, en km
# (le dernier va jusqu'à l'infini), effectif minimal de chaque groupe d'une cellule (exposées et
# non exposées, hérité du plan d'origine) et écart maximal des distances moyennes au centre des
# deux groupes (20 % de la largeur d'un anneau de 10 km, borne validée le 20/10)
ANNEAUX_KM = (0, 5, 10, 20, 30)
EFFECTIF_MIN_GROUPE = 15
ECART_DIST_MAX_KM = 2

# H1, paires de communes contiguës (§5.3, A6) : écarts de contrôle des pentes, estimées sans
# constante (§2.5, A7) ; bootstrap des communes : nombre de tirages et graine fixée, pour des
# résultats reproductibles et des pentes comparées sur les mêmes tirages
CONTROLES_PAIRES = ("d_dist_centre_km", "d_log_densite")
NB_TIRAGES_BOOTSTRAP = 1000
GRAINE_BOOTSTRAP = 20261021
# Fig. 5 : nombre de classes d'effectifs égaux du nuage par classes, dans chaque aire. Avec 20
# classes, une classe réunit environ 30 paires symétrisées dans l'aire qui en a le moins (Nantes,
# 301 paires, 602 symétrisées)
NB_CLASSES_FIG5 = 20

# H4 (§5.7) : mesures d'accès comparées, avec leur sens. Le sens -1 retourne les distances pour
# que, pour toutes les mesures, une pente positive dise « plus d'accès, plus de cadres » : être
# plus près d'une gare, c'est avoir un meilleur accès, comme avoir une APL plus haute. Le lycée
# privé y entre par la mesure principale de H1, pour être comparé aux autres sur la même échelle
MESURES_H4 = {
    "Lycée privé sous contrat": ("dist_lyc_prive_min", -1),
    "Gare de voyageurs": ("dist_gare_min", -1),
    "Médecins généralistes (APL)": ("apl_mg", 1),
    "Installations sportives": ("log_n_sport_5km", 1),
    "Équipements culturels": ("log_n_culture_5km", 1),
}

# Sorties de `pipeline.construire_base` (PLAN §4, étape G)
CHEMIN_BASE = "final/base_communale.parquet"
CHEMIN_PAIRES = "final/paires.parquet"
# Tableau de support du choix des aires (§5.2), livrable commité dans le dépôt
CHEMIN_TABLEAU_SUPPORT = Path(__file__).parents[2] / "docs" / "tableau_support.md"
# Documents du dépôt affichés en annexe du rapport (PLAN §6) : le dictionnaire des variables et le
# plan, dont on montre le journal des décisions (§13)
CHEMIN_DICTIONNAIRE = Path(__file__).parents[2] / "docs" / "dictionnaire_variables.md"
CHEMIN_PLAN = Path(__file__).parents[2] / "docs" / "PLAN.md"
TITRE_JOURNAL_PLAN = "## 13. Journal des décisions"
# Rayons du tableau de support : le principal et le 10 km rapporté à côté (§5.2)
RAYONS_SUPPORT_KM = (5, 10)
# Aires candidates de l'Ouest, dont au moins une doit être retenue (§2.2, critère a)
AIRES_OUEST = ("Nantes", "Rennes")
# Aires candidates proches d'une frontière terrestre, où les lycées étrangers manquent, et
# distance au contour national en deçà de laquelle une commune est comptée (§5.2, A6). Elle ne
# suit pas `RAYONS_KM` : le plan la fixe à 10 km
AIRES_FRONTALIERES = ("Lille", "Strasbourg")
DIST_FRONTIERE_KM = 10
# Écarts calculés dans les paires de communes contiguës. Sans la part de cadres, pour le tableau
# de support (A3) : accès principal et secondaire (§5.3), contrôles (§2.5, A7) et exposition 0/1
# pour compter les paires de statut différent (§5.2, A6). Puis l'accès aux autres
# infrastructures (H4, §5.7), qui n'entre que dans la base des aires retenues
VARIABLES_PAIRES_SANS_CADRES = (
    "dist_lyc_prive_min",
    "n_lyc_prive_5km",
    "dist_centre_km",
    "log_densite",
    "expose_lyc_prive_5km",
    "expose_lyc_prive_10km",
)
VARIABLES_PAIRES_H4 = ("dist_gare_min", "apl_mg", "log_n_sport_5km", "log_n_culture_5km")
VARIABLES_PAIRES = ("part_cadres_2022", *VARIABLES_PAIRES_SANS_CADRES, *VARIABLES_PAIRES_H4)

# Aires d'attraction des villes 2020 candidates : nom -> code AAV2020 (chaîne, le zéro compte)
AIRES_CANDIDATES = {
    "Rennes": "013",
    "Nantes": "008",
    "Toulouse": "005",
    "Bordeaux": "006",
    "Lyon": "002",
    "Grenoble": "014",
    "Lille": "004",
    "Strasbourg": "010",
}
# Aires retenues le 20/10 parmi les candidates, sur le tableau de support (PLAN §2.2, §13)
AIRES_RETENUES = {aire: AIRES_CANDIDATES[aire] for aire in ("Nantes", "Lyon", "Strasbourg")}

# Stockage (PLAN §7) : le S3 du SSPCloud si les identifiants AWS et le nom du bucket sont dans
# l'environnement, sinon le dossier data/ à la racine du dépôt (ignoré par git), avec un
# avertissement
VARIABLES_AWS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
# Le nom du bucket dépend du compte : chacun le définit dans cette variable d'environnement
VARIABLE_BUCKET_S3 = "BUCKET_S3"
PREFIXE_S3 = "projet-cadres-lycees"
DOSSIER_LOCAL = Path(__file__).parents[2] / "data"
# Adresses de lecture publique des copies gelées des sources qui changent sans prévenir (PLAN §7,
# A2) : le dossier raw/ du bucket du projet sur le SSPCloud, qui doit rester accessible jusqu'à
# la soutenance, puis en repli une release GitHub du dépôt (les deux hébergements, journal du
# 20/10). Le sha256 de chaque copie est contrôlé à chaque lecture, quelle que soit sa provenance
URL_COPIES_S3 = "https://minio.lab.sspcloud.fr/gfogato/projet-cadres-lycees/"
URL_COPIES_RELEASE = (
    "https://github.com/gabrielwenger1-coder/DataScience/releases/download/donnees-20261020/"
)

# Annuaire de l'éducation (source 3) : export complet de l'API, gelé le 13/10/2026. L'annuaire
# change chaque jour : le 20/10, un lycée sans coordonnées (0451844K) y est apparu
URL_ANNUAIRE = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-annuaire-education/exports/parquet"
)
CHEMIN_RAW_ANNUAIRE = "raw/annuaire_education_20261013.parquet"
SHA256_ANNUAIRE = "2c493f152bc8fc682aa8b1f063392015941bcff36bae2ae59a4d1a1e6334e94a"

# Gares de voyageurs (source 12, H4) : export complet de SNCF Gares & Connexions, gelé le
# 03/11/2026, car il est retraité chaque jour. Une ligne par gare (2 792), métropole continentale
# seulement : la Corse n'a aucune gare dans ce fichier, ce qui est sans effet sur les 3 aires
URL_GARES = (
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
    "gares-de-voyageurs/exports/parquet"
)
CHEMIN_RAW_GARES = "raw/gares_voyageurs_20261103.parquet"
SHA256_GARES = "61ccf3392b01cb6785268be7152337f1a95dda93fa9eadf9134901b5f366bc44"

# APL aux médecins généralistes (source 13, H4), DREES : un xlsx dont chaque mise à jour annuelle
# ajoute une feuille et retire des millésimes, gelé le 03/11/2026. Feuille du millésime 2024, le
# dernier, déjà au grain du projet (arrondissements de Lyon, fusions de 2024 et 2025 appliquées) ;
# en-tête à la ligne 8 (base 0), ligne des unités juste dessous. APL tous âges de médecins, en
# consultations accessibles par an et par habitant standardisé
URL_APL = (
    "https://data.drees.solidarites-sante.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "530_l-accessibilite-potentielle-localisee-apl/attachments/"
    "indicateur_d_apl_aux_medecins_generalistes_xlsx"
)
CHEMIN_RAW_APL = "raw/apl_medecins_generalistes_20261103.xlsx"
SHA256_APL = "21c73deff57dc7a83a3cd6fcfd5b5ceb8c7a40e98590a50b5b1194f2dd4d75a2"
FEUILLE_APL = "APL 2024"
LIGNE_ENTETE_APL = 8
COLONNE_CODE_APL = "Code commune INSEE"
COLONNE_APL = "APL aux médecins généralistes"

# Équipements sportifs, Data ES du ministère des Sports (source 15, H4) : export complet de l'API
# nationale (la page data.gouv « …-pratiques-2 » du plan ne couvre que l'Île-de-France), mis à
# jour chaque jour, gelé le 03/11/2026. Une ligne par équipement ; on compte les installations
# (un lieu qui regroupe des équipements, 2 en moyenne) : sinon un club de 10 courts de tennis
# pèserait 10 fois. Position en WGS84 dans `equip_x` et `equip_y`, sous forme de texte
URL_EQUIPEMENTS_SPORTIFS = (
    "https://equipements.sports.gouv.fr/api/explore/v2.1/catalog/datasets/data-es/exports/parquet"
)
CHEMIN_RAW_EQUIPEMENTS_SPORTIFS = "raw/equipements_sportifs_20261103.parquet"
SHA256_EQUIPEMENTS_SPORTIFS = "c78cb234bb591f54660277c5720e5a8275ec26ffacf7120b141024cfba936eef"

# Équipements culturels, BPE 2025 de l'Insee, fichier détail géolocalisé (source 14, H4). La
# page data.gouv du plan est une republication de la BPE 2023 par l'Île-de-France : on prend le
# fichier de l'Insee, actualisé chaque mois (anonymisation Sirene), gelé le 03/11/2026. Le serveur
# coupe parfois le téléchargement sans erreur ni Content-Length : le gel contrôle le Parquet.
# Culture : les 7 types du sous-domaine F3 (cinéma, conservatoire, bibliothèque, exposition,
# patrimoine, archives, arts du spectacle) ; les librairies (B324) sont des commerces. Métropole :
# coordonnées en Lambert 93 (EPSG 2154), celles des DROM sont dans d'autres projections
URL_BPE = "https://www.insee.fr/fr/statistiques/fichier/8217525/BPE25.parquet"
CHEMIN_RAW_BPE = "raw/bpe_2025_20261103.parquet"
SHA256_BPE = "3bad0dc8b02eff0bee86832acf97fdeccef02116bbeb8a6dca2ad0e99d054f6a"
SOUS_DOMAINE_CULTURE_BPE = "F3"
EPSG_BPE_METROPOLE = "2154"
# Délai d'attente de `requests` par lecture, pas durée totale (le téléchargement dure ~12 s)
DELAI_TELECHARGEMENT_S = 120
# Zonage en aires d'attraction des villes 2020 (source 8), géographie au 01/01/2025. Le zip de
# l'Insee est permanent : il est lu à son URL d'origine, et son sha256 est contrôlé à chaque lecture
URL_AAV = "https://www.insee.fr/fr/statistiques/fichier/4803954/AAV2020_au_01-01-2025.zip"
SHA256_AAV = "738f81b12832fe294bd24ddbfe3a31830c20d850143fc8b4393f18d4b8ee8181"
CHEMIN_RAW_AAV = "raw/AAV2020_au_01-01-2025.zip"
XLSX_AAV = "AAV2020_au_01-01-2025.xlsx"
FEUILLE_AAV = "Composition_communale"
# Les noms de variables sont à la ligne 6 de la feuille, les lignes 1 à 4 sont des métadonnées
ENTETE_AAV = 5
# Nombre de communes du COG 2025, le même que dans les contours de cartiflette
NB_COMMUNES_AAV = 34875
# Codes de `CATEAAV2020` (feuille Documentation du classeur) : 11 commune-centre, 12 autre commune
# du pôle principal, 13 commune d'un pôle secondaire, 20 commune de la couronne, 30 commune hors
# attraction des villes. Un code inconnu fait échouer la lecture
CATEGORIES_AAV = ("11", "12", "13", "20", "30")

# Série historique du recensement 2022 : population et superficie (km²) en COG 2025,
# arrondissements municipaux et communes parentes ensemble. Elle remplace la source 2 du plan
# (« Évolution et structure », §3.1) pour la population et la superficie, que ce fichier-là n'a
# pas ; P22_POP y est identique dans les 8 aires. Le zip de l'Insee est permanent : il est lu à son
# URL d'origine, et son sha256 (observé le 20/10) est contrôlé à chaque lecture
URL_SERIE_RP2022 = (
    "https://www.insee.fr/fr/statistiques/fichier/8582555/base-cc-serie-historique-2022_csv.zip"
)
SHA256_SERIE_RP2022 = "ff0187ec6bb77fd2e5da639c08159368ff152cad0682ee0908358a829830c273"
CHEMIN_RAW_SERIE_RP2022 = "raw/base-cc-serie-historique-2022_csv.zip"
CSV_SERIE_RP2022 = "base-cc-serie-historique-2022.CSV"
# Communes et arrondissements du COG 2025, Mayotte exceptée
NB_LIGNES_SERIE_RP2022 = 34903

# « Évolution et structure de la population » du recensement 2022 (source 2) : actifs de 25 à 54
# ans par groupe socioprofessionnel en 2011 et en 2022, en COG 2025, arrondissements de Lyon
# compris (PLAN §2.3, A11). Zip permanent de l'Insee, lu à son URL d'origine ; son sha256
# (observé le 20/10) est contrôlé à chaque lecture
URL_EVOL_STRUCT_RP2022 = (
    "https://www.insee.fr/fr/statistiques/fichier/8581696/base-cc-evol-struct-pop-2022_csv.zip"
)
SHA256_EVOL_STRUCT_RP2022 = "cb4b918862289527232ad79fb3b712d5f4635c6de5bae762e8d22a132717ed83"
CHEMIN_RAW_EVOL_STRUCT_RP2022 = "raw/base-cc-evol-struct-pop-2022_csv.zip"
CSV_EVOL_STRUCT_RP2022 = "base-cc-evol-struct-pop-2022.CSV"
# Communes et arrondissements du COG 2025, Mayotte exceptée
NB_LIGNES_EVOL_STRUCT_RP2022 = 34903
# Actifs de 25 à 54 ans (occupés et chômeurs ayant déjà travaillé) des 6 groupes
# socioprofessionnels, du groupe 1 au groupe 6 : leur somme est le dénominateur de la part de
# cadres, et le groupe 3 en est le numérateur. 2022 en PCS 2020 : `GSEC13_23` réunit les
# cadres en emploi (13) et au chômage (23). 2011 en PCS 2003 (`CS3`). Les deux premiers niveaux
# sont les mêmes dans les deux nomenclatures, selon la documentation de l'Insee (§2.3, A17). Noms
# recopiés de l'en-tête du fichier : la page de l'Insee nomme les employés `…_GSEC16_25`, alors
# que le fichier dit `…_GSEC15_25`. Aucune commune des aires retenues n'a 0 actif en 2011 ou en
# 2022 (au moins 12) : vérifié le 21/10 sans lire les cadres, avec le dénominateur calculé comme
# `C.._POP2554` moins les retraités et les autres inactifs. A17 n'a donc aucune commune à nommer
ACTIFS_2554_2022 = (
    "C22_POP2554_STAT_GSEC11_21",
    "C22_POP2554_STAT_GSEC12_22",
    "C22_POP2554_STAT_GSEC13_23",
    "C22_POP2554_STAT_GSEC14_24",
    "C22_POP2554_STAT_GSEC15_25",
    "C22_POP2554_STAT_GSEC16_26",
)
ACTIFS_2554_2011 = (
    "C11_POP2554_CS1",
    "C11_POP2554_CS2",
    "C11_POP2554_CS3",
    "C11_POP2554_CS4",
    "C11_POP2554_CS5",
    "C11_POP2554_CS6",
)
CADRES_2554_2022 = "C22_POP2554_STAT_GSEC13_23"
CADRES_2554_2011 = "C11_POP2554_CS3"
# Robustesse (§2.3, §5.6) : cadres parmi la population de 15 ans ou plus en 2022, inactifs et
# retraités compris (`docs/exploration_sources.md`, « Évolution et structure »)
CADRES_15P_2022 = "C22_POP15P_STAT_GSEC13_23"
POP_15P_2022 = "C22_POP15P"
# Carte de la part de cadres par IRIS (source 16 bis, A18) : bases infracommunales « Activité
# des résidents », en IRIS et COG 2024 pour 2022, en géographie 2013 pour 2011. Seule la tranche
# des 15-64 ans y croise la CSP : ce n'est pas la variable du §2.3 (25-54 ans). Zips permanents
# de l'Insee, sha256 observés le 20/10
URL_ACTIVITE_IRIS_2022 = (
    "https://www.insee.fr/fr/statistiques/fichier/8647006/base-ic-activite-residents-2022_csv.zip"
)
SHA256_ACTIVITE_IRIS_2022 = "f4aefb7fab425b9f7eb802e2afb475908bbf2186e0d88f542cf7a67fc70623cb"
CHEMIN_RAW_ACTIVITE_IRIS_2022 = "raw/base-ic-activite-residents-2022_csv.zip"
CSV_ACTIVITE_IRIS_2022 = "base-ic-activite-residents-2022.CSV"
NB_LIGNES_ACTIVITE_IRIS_2022 = 49276
URL_ACTIVITE_IRIS_2011 = (
    "https://www.insee.fr/fr/statistiques/fichier/2028668/infra-activite-resident-2011.zip"
)
SHA256_ACTIVITE_IRIS_2011 = "05076a23c7a3e6bab7aadae8e1b12c17ed1a2aff395340edd59df1474719e7ea"
CHEMIN_RAW_ACTIVITE_IRIS_2011 = "raw/infra-activite-resident-2011.zip"
XLS_ACTIVITE_IRIS_2011 = "base-ic-activite-residents-2011.xls"
# Feuille des IRIS ; noms de variables à la ligne 6, après les titres
FEUILLE_ACTIVITE_IRIS_2011 = "IRIS"
ENTETE_ACTIVITE_IRIS_2011 = 5
NB_LIGNES_ACTIVITE_IRIS_2011 = 50867
# Actifs de 15 à 64 ans des 6 groupes socioprofessionnels, du groupe 1 au groupe 6 (le 3 : cadres)
ACTIFS_1564_IRIS_2022 = (
    "C22_ACT1564_STAT_GSEC11_21",
    "C22_ACT1564_STAT_GSEC12_22",
    "C22_ACT1564_STAT_GSEC13_23",
    "C22_ACT1564_STAT_GSEC14_24",
    "C22_ACT1564_STAT_GSEC15_25",
    "C22_ACT1564_STAT_GSEC16_26",
)
ACTIFS_1564_IRIS_2011 = (
    "C11_ACT1564_CS1",
    "C11_ACT1564_CS2",
    "C11_ACT1564_CS3",
    "C11_ACT1564_CS4",
    "C11_ACT1564_CS5",
    "C11_ACT1564_CS6",
)
CADRES_1564_IRIS_2022 = "C22_ACT1564_STAT_GSEC13_23"
CADRES_1564_IRIS_2011 = "C11_ACT1564_CS3"
# Contours des IRIS des aires retenues (cartiflette 0.4.0, COG 2025, sans simplification),
# copies gelées du 21/10
CHEMIN_RAW_CONTOURS_IRIS = "raw/contours_iris_{aav}_20261021.parquet"
SHA256_CONTOURS_IRIS = {
    "008": "61e52233fcdd7fe09d0f0350b6a5060719ca83f0a56c7710848a5ae35d34ff23",
    "002": "5c77cb03f2cfb55e3e2634218f4f94b6b43f13ed1496e85572919dc271b43018",
    "010": "15b57329479d4261de4a443b9b4458332f92692b286caecbb270a3b678aad82c",
}
# Code IRIS des contours (COG 2025) -> code des données 2022 (COG 2024), quand il a changé :
# Porte des Pierres Dorées, 69159 en 2024, devenue 69114 en 2025
IRIS_RECODES_2025_2024 = {"691140000": "691590000"}
# Table de passage annuelle des codes communes 2025 (source 9) : elle repère les communes qui en
# ont absorbé d'autres entre la géographie des données 2011 (2013) et celle de 2022 (2024)
URL_PASSAGE_COG = (
    "https://www.insee.fr/fr/statistiques/fichier/7671867/table_passage_annuelle_2025.zip"
)
SHA256_PASSAGE_COG = "803527a040748f4c7dc5e97777cb5838e8b7d4cc36d0b182f53a83e9787d595b"
CHEMIN_RAW_PASSAGE_COG = "raw/table_passage_annuelle_2025.zip"
XLSX_PASSAGE_COG = "table_passage_annuelle_2025.xlsx"
# Feuille des communes et arrondissements ; noms de variables à la ligne 6, après les titres
FEUILLE_PASSAGE_COG = "COM"
ENTETE_PASSAGE_COG = 5
# Une ligne par chemin de filiation (exploration §8)
NB_LIGNES_PASSAGE_COG = 36760

# Codes du filtre des lycées (PLAN §2.4) ; les libellés de la source ("Lycée", "Public"...)
# restent dans collecte.py. `code_nature` : 300 général et technologique, 301 technologique,
# 302 général, 306 polyvalent
NATURES_LYCEES = (300, 301, 302, 306)
# `code_type_contrat_prive` du privé sous contrat : 30 association (toutes classes), 31 (partie)
CONTRATS_PRIVE_RETENUS = ("30", "31")
# Robustesse (§2.4, §5.6) : lycées professionnels (320) et privé hors contrat (10) réintégrés
NATURES_LYCEES_ROBUSTESSE = (*NATURES_LYCEES, 320)
CONTRATS_PRIVE_ROBUSTESSE = (*CONTRATS_PRIVE_RETENUS, "10")
# Lycées privés hors contrat de cette robustesse sans coordonnées dans l'annuaire du 13/10/2026,
# presque tous ouverts en 2026 : écartés nommément, tout autre lycée sans position fait échouer.
# 0443105L est au Landreau (44079), dans l'aire de Nantes
UAI_SANS_POSITION_ROBUSTESSE = (
    "0443105L",
    "0313176J",
    "0581019T",
    "0783920M",
    "0212319G",
    "0756899S",
    "0756960H",
)
# Lycées de métropole retenus par le type, la nature et la tutelle, mais dont l'annuaire du
# 13/10/2026 ne donne pas le statut public ou privé : leur secteur est inconnu, ils sont écartés.
# 0271911F (Eure, ouvert en 2024) n'est pas non plus dans l'IPS ; il est à 188 km de l'aire
# candidate la plus proche
UAI_SANS_STATUT = ("0271911F",)

# Contours communaux (source 7), via cartiflette. Le COG de référence est celui de 2025
# (PLAN §2.1) : sans `year`, cartiflette prendrait l'année courante ; sans `simplification=0`, il
# simplifierait les contours (les centroïdes bougeraient jusqu'à 52 m) ; il ne publie qu'en WGS84
ANNEE_COG = 2025
SIMPLIFICATION_CONTOURS = 0
# Une copie gelée par aire d'attraction, du 13/10/2026 : les données de cartiflette sont lues sur
# son serveur, qui peut changer, et son client a déjà changé de comportement par défaut
CHEMIN_RAW_CONTOURS = "raw/contours_aav_{aav}_20261013.parquet"
SHA256_CONTOURS = {
    "002": "5fc255ef5f92c540c5037f793c15c24007642c7cdce256a1e4f47d516176f231",
    "004": "6ff1e4bc0675ab567b7af3eb506774c0740ab855c5f333c66ee6b8fe1eb89982",
    "005": "c42afd4910a9a6907c54e2f8d476b8a4b6db3630bf9ffdff7b41cedf8a3b2c6e",
    "006": "6e0cb9a94a69887fd123a2d57c49068aa25b207da9541813652c00f1b2930c28",
    "008": "54665ed725b9ae364166d6dc76cd09b71b8e42397916e6fe564d8f0308786e59",
    "010": "454d27768198bb48be5882987f3aa36f88902add34bf443dff0cd37cc8be7790",
    "013": "c846f8d895d3121435037f5c04054a9e2275bb95e2de1791cae61498550b4cec",
    "014": "a1d13c20cc9565de3e2b3bb78b8d020076bae7c2a94ac2648d7aa96aa0699357",
}
# Contours des départements, copie gelée du 20/10/2026 : leur union donne le contour de la France
# métropolitaine, dont on mesure la distance pour Lille et Strasbourg (frontière, A6)
CHEMIN_RAW_DEPARTEMENTS = "raw/contours_departements_20261020.parquet"
SHA256_DEPARTEMENTS = "a6e4d3b3a7657f61b8fe9b710efa5f50c0cab76cde0d522f4cfd4adfdbe405ca"
# Départements de métropole, Corse comprise (2A et 2B)
NB_DEPARTEMENTS_METROPOLE = 96
# Pôle ou couronne d'après `CATEAAV2020`. Les codes 13 (pôle secondaire, aucun dans les 8 aires
# candidates) et 30 (hors aire) n'y sont pas : ils feraient échouer `geo.referentiel_communes`
POLE_COURONNE_AAV = {"11": "pole", "12": "pole", "20": "couronne"}
# Communes à arrondissements municipaux des aires candidates (Paris et Marseille n'en font pas
# partie) : Lyon en a 9, de 69381 à 69389. Toute autre commune est une seule unité
NB_ARRONDISSEMENTS = {"69123": 9}
# La commune-centre de l'aire, définie par l'Insee (`CATEAAV2020` = 11, PLAN §2.5)
CATEGORIE_COMMUNE_CENTRE = "11"

# IPS des lycées (source 5) : export de l'API gelé le 13/10/2026 ; le rapport lit la copie gelée,
# jamais l'API
URL_IPS = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-ips-lycees-ap2023/exports/csv"
)
SHA256_IPS = "31b2aafd8fb4597608c55f8f78f7144444a350df795111a651fb5222ee9c8aa7"
CHEMIN_RAW_IPS = "raw/ips_lycees_20261013.csv"
NB_LIGNES_IPS = 10905
# Rentrée et mesure de l'écart d'IPS public/privé (Fig. 1, critère (b) du §2.2) : la rentrée la
# plus récente, et `ips_voie_gt` pour rester sur la voie générale et technologique
RENTREE_IPS = "2025-2026"
COLONNE_IPS = "ips_voie_gt"
# Types de lycée de l'IPS retenus : les lycées professionnels (LP) sortent du périmètre du §2.4
TYPES_LYCEES_IPS = ("LEGT", "LPO")
# Lycées de l'IPS situés dans les communes des 8 aires candidates mais absents des lycées retenus
# (annuaire du 13/10/2026, pour la rentrée et la mesure ci-dessus : en changer impose de revoir
# cette liste) : trois privés de Saint-Sébastien-sur-Loire fusionnés dans l'annuaire sous l'UAI
# 0443088T, Averroès (hors contrat dans l'annuaire, sous contrat dans l'IPS), un lycée agricole
# privé (Genech), un lycée climatique (nature 310) et une section agricole publique. Seuls ceux
# des aires étudiées sont attendus : la liste vaut pour toute partie des 8 candidates
UAI_IPS_NON_RETENUS = (
    "0352867B",
    "0380097Z",
    "0440256P",
    "0440279P",
    "0441653H",
    "0596281G",
    "0596681S",
)

# IVAL des lycées généraux et technologiques (source 6) : export de l'API gelé le 20/10/2026 ;
# le rapport lit la copie gelée, jamais l'API
URL_IVAL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-indicateurs-de-resultat-des-lycees-gt_v2/exports/csv"
)
SHA256_IVAL = "6ab77b391e3405f5157bb942d4548d5f1cfbacd94e76dd52b93db9b370de8658"
CHEMIN_RAW_IVAL = "raw/ival_lycees_gt_20261020.csv"
NB_LIGNES_IVAL = 32485
# Règle A1 (PLAN §2.4) : sessions du bac retenues, entre les deux recensements, et nombre
# minimal de sessions où la valeur ajoutée est renseignée
PREMIERE_SESSION_IVAL = 2012
DERNIERE_SESSION_IVAL = 2022
NB_SESSIONS_MIN_IVAL = 5
# Test de fiabilité de l'IVAL (PLAN §3.2, A7) : les deux moitiés de la période et le nombre minimal
# de sessions valides dans chacune
MOITIES_IVAL = ((2012, 2017), (2018, 2022))
NB_SESSIONS_MIN_MOITIE = 3
# Seuil de fiabilité (Spearman-Brown, toutes aires ensemble) en dessous duquel H3 est « non
# testable avec cette mesure » (A1, A7)
SEUIL_FIABILITE_IVAL = 0.5
# Bootstrap : au-delà de ce nombre de tirages écartés (rang incomplet), soit 5 % des tirages,
# l'intervalle n'est pas rapporté. Règle de H3 (§5.5, A16, verdict alors « non concluante »),
# reprise pour les pentes des paires, où seule une robustesse peut écarter des tirages
MAX_TIRAGES_ECARTES = 50
# Fig. 6 : les trois tiers d'IVAL de chaque aire, puis les communes sans IVAL
CATEGORIES_FIG6 = ("1er tiers", "2e tiers", "3e tiers", "sans IVAL")
# Robustesse (§5.6) : seuil des petites communes, en actifs de 25 à 54 ans en 2022 (§3.2), et
# nombre de permutations de l'indice de Moran (p-valeur à 1/1000 près)
ACTIFS_MIN_ROBUSTESSE = 200
NB_PERMUTATIONS_MORAN = 999
# Lycées publiés dans l'IVAL sous un autre UAI que celui de l'annuaire du 13/10/2026 : leurs
# sessions sont rattachées à l'UAI de l'annuaire, avec la même règle dans toutes les aires (choix
# du 20/10). Les trois lycées privés de Saint-Sébastien-sur-Loire, regroupés en 2026 sous un
# nouvel UAI ; la section d'enseignement général du lycée Philippe Cousteau (Bordeaux), qui
# porte son IVAL ; Chevreul Lestonnac (Lyon 7e), absorbé en 2019
UAI_IVAL_RATTACHES = {
    "0440256P": "0443088T",
    "0440279P": "0443088T",
    "0441653H": "0443088T",
    "0332835C": "0332346W",
    "0690535G": "0690574Z",
}
# Lycées de l'IVAL situés dans les communes des 8 aires candidates, qui remplissent la règle A1
# mais ne sont pas des lycées retenus (après rattachement) : lycées professionnels (0330018R,
# 0590125R), lycée climatique (0380097Z), lycée agricole (0596281G), hors contrat dans
# l'annuaire (0596681S Averroès, 0694086S Al Kindi) et Sainte-Claire (0593113N), absent de
# l'annuaire. Seuls ceux des aires étudiées sont attendus : la liste vaut pour toute partie des
# 8 candidates. Changer de règle impose de la revoir
UAI_IVAL_NON_RETENUS = (
    "0330018R",
    "0380097Z",
    "0590125R",
    "0593113N",
    "0596281G",
    "0596681S",
    "0694086S",
)

# Secteur de l'annuaire (`statut_public_prive`) -> secteur du projet
SECTEURS = {"Public": "public", "Privé": "prive"}
# Secteur de l'IPS (`secteur`) -> secteur du projet
SECTEURS_IPS = {"public": "public", "privé sous contrat": "prive"}
# Couleurs des figures, les mêmes partout : bleu et orange pour les secteurs, qui restent
# distincts en cas de daltonisme ; gris pour le texte et pour relier deux points
COULEURS_SECTEURS = {"public": "#2a78d6", "prive": "#eb6834"}
COULEUR_TEXTE = "#52514e"
COULEUR_LIAISON = "#c3c2b7"
# Grille des axes, très claire pour rester en arrière-plan
COULEUR_GRILLE = "#ececea"
# Bande de fond qui met en avant les aires retenues parmi les candidates (Fig. 1, PLAN §5.1)
COULEUR_FOND_RETENUES = "#f0efec"
# Date de l'annuaire de l'éducation affichée dans la source des figures
DATE_ANNUAIRE = "13/10/2026"
# Secteurs écrits en toutes lettres dans les légendes et les infobulles
LIBELLES_SECTEURS = {"public": "public", "prive": "privé sous contrat"}
# Une couleur par aire retenue, la même dans toutes les figures (PLAN §6) : vert, violet et brun
# de la palette d'Okabe et Ito, lisibles en cas de daltonisme et distincts du bleu et de l'orange
# des secteurs
COULEURS_AIRES = {"Nantes": "#009e73", "Lyon": "#a2559c", "Strasbourg": "#9c6b1f"}

# Fig. 2 : la courbe de chaque aire relie les parts moyennes des communes par tranche de distance
# au centre, pondérées par les actifs (§3.2). Une tranche de 2,5 km découpe chaque anneau du §5.2
# en deux au moins ; une tranche de moins de 5 communes n'a pas de point, trop bruité
PAS_COURBE_FIG2_KM = 2.5
MIN_COMMUNES_TRANCHE_FIG2 = 5

# Fig. 3 : classes de distance au lycée privé le plus proche, par leurs bornes supérieures en km
# (incluses). Les rayons du §2.4 en sont les premières bornes : être à 5 km ou moins du plus
# proche, c'est avoir au moins un lycée privé dans le rayon de 5 km. Au-delà de 20 km, les
# communes les plus éloignées sont regroupées
BORNES_DISTANCE_KM = (*RAYONS_KM, 20)
# Palette ColorBrewer « Greens » à 5 classes, du plus proche (foncé) au plus loin (clair) : une
# seule teinte, ni bleu ni orange, réservés aux secteurs des lycées
COULEURS_DISTANCE = ("#006d2c", "#31a354", "#74c476", "#bae4b3", "#edf8e9")
# Tolérance de simplification des contours, pour l'affichage seulement : à peu près la racine
# carrée de l'aire des triangles retirés (algorithme de Visvalingam-Whyatt de shapely), soit
# des limites déplacées jusqu'à 150 m environ. Le GeoJSON des 8 aires passe de 14,5 à 7 Mo ;
# les calculs gardent les contours exacts
SIMPLIFICATION_CARTE_M = 50
# Fonds de carte sans clé d'accès, nommés comme dans xyzservices (folium les reconnaît) : le
# gris laisse lire les couleurs des communes, le plan IGN donne les noms de lieux. CARTO, le fond
# clair habituel, exige une clé depuis 2026 (constaté le 20/10)
FONDS_CARTE = {"Fond gris (Esri)": "Esri.WorldGrayCanvas", "Plan IGN": "GeoportailFrance.plan"}

# Carte IRIS (A18) : classes de la part de cadres parmi les actifs de 15 à 64 ans, en %, par
# leurs bornes (basse incluse), les mêmes pour 2011 et 2022 et fixées sans regarder les aires
# retenues ; palette ColorBrewer « Purples » à 6 classes, une seule teinte, ni bleu ni orange
# (secteurs) ni vert (Fig. 3). Les IRIS non comparables sont hachurés en gris
BORNES_PART_CADRES_IRIS = (10, 20, 30, 40, 50)
COULEURS_PART_CADRES_IRIS = ("#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8", "#756bb1", "#54278f")
COULEUR_IRIS_NON_COMPARABLE = "#e3e2de"
# Demi-côté, en km, du carré de zoom sur la commune-centre, où les IRIS sont trop petits pour se
# lire à l'échelle de l'aire. 9 km couvrent les communes-centres des 3 aires, Strasbourg compris
# (17,3 km du nord au sud), et Villeurbanne avec Lyon
ZOOM_IRIS_KM = 9

# Fichiers bruts lus par le projet, avec leur sha256 contrôlé à chaque lecture : copies gelées et
# zips de l'Insee, listés dans l'annexe « Reproduire le projet » (`pipeline.fichiers_bruts`). Un
# chemin qui contient `{aav}` a un sha256 par aire
FICHIERS_BRUTS = (
    (CHEMIN_RAW_ANNUAIRE, SHA256_ANNUAIRE),
    (CHEMIN_RAW_IPS, SHA256_IPS),
    (CHEMIN_RAW_IVAL, SHA256_IVAL),
    (CHEMIN_RAW_CONTOURS, SHA256_CONTOURS),
    (CHEMIN_RAW_DEPARTEMENTS, SHA256_DEPARTEMENTS),
    (CHEMIN_RAW_CONTOURS_IRIS, SHA256_CONTOURS_IRIS),
    (CHEMIN_RAW_GARES, SHA256_GARES),
    (CHEMIN_RAW_APL, SHA256_APL),
    (CHEMIN_RAW_EQUIPEMENTS_SPORTIFS, SHA256_EQUIPEMENTS_SPORTIFS),
    (CHEMIN_RAW_BPE, SHA256_BPE),
    (CHEMIN_RAW_AAV, SHA256_AAV),
    (CHEMIN_RAW_PASSAGE_COG, SHA256_PASSAGE_COG),
    (CHEMIN_RAW_SERIE_RP2022, SHA256_SERIE_RP2022),
    (CHEMIN_RAW_EVOL_STRUCT_RP2022, SHA256_EVOL_STRUCT_RP2022),
    (CHEMIN_RAW_ACTIVITE_IRIS_2011, SHA256_ACTIVITE_IRIS_2011),
    (CHEMIN_RAW_ACTIVITE_IRIS_2022, SHA256_ACTIVITE_IRIS_2022),
)
