"""Constantes du projet : les choix fixés par le plan et les paramètres des sources."""

from pathlib import Path

# Lambert 93 (mètres) pour les distances, WGS84 pour les cartes interactives
CRS_CALCUL = 2154
CRS_CARTES = 4326

# Rayons d'accessibilité en km : 5 est le principal, 3 et 10 servent en robustesse
RAYONS_KM = (3, 5, 10)
RAYON_PRINCIPAL_KM = 5

# Anneaux : bornes basses en km (le dernier est ouvert), effectif minimal de chaque groupe d'une
# cellule et écart maximal des distances moyennes au centre des deux groupes
ANNEAUX_KM = (0, 5, 10, 20, 30)
EFFECTIF_MIN_GROUPE = 15
ECART_DIST_MAX_KM = 2

# Paires contiguës : écarts de contrôle, tirages du bootstrap et graine (mêmes tirages partout)
CONTROLES_PAIRES = ("d_dist_centre_km", "d_log_densite")
NB_TIRAGES_BOOTSTRAP = 1000
GRAINE_BOOTSTRAP = 20261021
# Classes du nuage de `fig_paires` : environ 30 paires symétrisées par classe à Nantes
NB_CLASSES_NUAGE_PAIRES = 20

# H4 : variable de chaque mesure d'accès et son sens ; -1 retourne les distances pour qu'une
# pente positive dise toujours « plus d'accès, plus de cadres »
MESURES_H4 = {
    "Lycée privé sous contrat": ("dist_lyc_prive_min", -1),
    "Gare de voyageurs": ("dist_gare_min", -1),
    "Médecins généralistes (APL)": ("apl_mg", 1),
    "Installations sportives": ("log_n_sport_5km", 1),
    "Équipements culturels": ("log_n_culture_5km", 1),
}

CHEMIN_BASE = "final/base_communale.parquet"
CHEMIN_PAIRES = "final/paires.parquet"
CHEMIN_TABLEAU_SUPPORT = Path(__file__).parents[2] / "docs" / "tableau_support.md"
# Documents affichés en annexe du rapport : le dictionnaire et le journal des décisions du plan
CHEMIN_DICTIONNAIRE = Path(__file__).parents[2] / "docs" / "dictionnaire_variables.md"
CHEMIN_PLAN = Path(__file__).parents[2] / "docs" / "PLAN.md"
TITRE_JOURNAL_PLAN = "## 13. Journal des décisions"
# Rayons du tableau de support : le principal et le 10 km rapporté à côté
RAYONS_SUPPORT_KM = (5, 10)
# Aires de l'Ouest, dont au moins une doit être retenue (critère a)
AIRES_OUEST = ("Nantes", "Rennes")
# Aires proches d'une frontière terrestre, où les lycées étrangers manquent, et seuil de distance
AIRES_FRONTALIERES = ("Lille", "Strasbourg")
DIST_FRONTIERE_KM = 10
# Écarts calculés dans les paires ; ceux du tableau de support n'utilisent pas la part de cadres
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
AIRES_RETENUES = {aire: AIRES_CANDIDATES[aire] for aire in ("Nantes", "Lyon", "Strasbourg")}

# Stockage : S3 si les identifiants AWS et le nom du bucket sont définis, sinon le dossier data/
VARIABLES_AWS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
VARIABLE_BUCKET_S3 = "BUCKET_S3"
PREFIXE_S3 = "projet-cadres-lycees"
DOSSIER_LOCAL = Path(__file__).parents[2] / "data"
# Lecture publique des copies gelées : le bucket du projet, puis une release GitHub
URL_COPIES_S3 = "https://minio.lab.sspcloud.fr/gfogato/projet-cadres-lycees/"
URL_COPIES_RELEASE = (
    "https://github.com/gabrielwenger1-coder/DataScience/releases/download/donnees-20261020/"
)

# Annuaire de l'éducation : export complet de l'API, gelé car il change chaque jour
URL_ANNUAIRE = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-annuaire-education/exports/parquet"
)
CHEMIN_RAW_ANNUAIRE = "raw/annuaire_education_20261013.parquet"
SHA256_ANNUAIRE = "2c493f152bc8fc682aa8b1f063392015941bcff36bae2ae59a4d1a1e6334e94a"

# Gares de voyageurs de SNCF Gares & Connexions (H4), retraitées chaque jour : copie gelée
URL_GARES = (
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
    "gares-de-voyageurs/exports/parquet"
)
CHEMIN_RAW_GARES = "raw/gares_voyageurs_20261103.parquet"
SHA256_GARES = "61ccf3392b01cb6785268be7152337f1a95dda93fa9eadf9134901b5f366bc44"

# APL aux médecins généralistes de la DREES (H4) : chaque mise à jour retire des millésimes.
# Feuille 2024, au grain du projet ; en-tête à la ligne 8 (base 0), unités juste dessous
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

# Équipements sportifs, Data ES du ministère des Sports (H4), mis à jour chaque jour
URL_EQUIPEMENTS_SPORTIFS = (
    "https://equipements.sports.gouv.fr/api/explore/v2.1/catalog/datasets/data-es/exports/parquet"
)
CHEMIN_RAW_EQUIPEMENTS_SPORTIFS = "raw/equipements_sportifs_20261103.parquet"
SHA256_EQUIPEMENTS_SPORTIFS = "c78cb234bb591f54660277c5720e5a8275ec26ffacf7120b141024cfba936eef"

# Équipements culturels de la BPE 2025 (H4) : sous-domaine F3, coordonnées en Lambert 93 en
# métropole ; fichier actualisé chaque mois, d'où la copie gelée
URL_BPE = "https://www.insee.fr/fr/statistiques/fichier/8217525/BPE25.parquet"
CHEMIN_RAW_BPE = "raw/bpe_2025_20261103.parquet"
SHA256_BPE = "3bad0dc8b02eff0bee86832acf97fdeccef02116bbeb8a6dca2ad0e99d054f6a"
SOUS_DOMAINE_CULTURE_BPE = "F3"
EPSG_BPE_METROPOLE = "2154"
# Statistiques DVF d'Etalab (robustesse au prix) : fichier réécrit sans prévenir, copie gelée
URL_DVF = "https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/dvf/stats_whole_period.csv"
CHEMIN_RAW_DVF = "raw/statistiques_dvf_20261103.csv"
SHA256_DVF = "eca12b1b1b45274e315859135d5f4ac15137f3e084712ea9b614b11c4a100722"
COLONNE_VENTES_DVF = "nb_ventes_whole_apt_maison"
COLONNE_PRIX_DVF = "med_prix_m2_whole_apt_maison"
# Chefs-lieux (mairies) d'ADMIN EXPRESS COG 2025, lus par le WFS de l'IGN (robustesse)
URL_CHEFS_LIEUX = (
    "https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
    "&outputFormat=application/json&srsName=EPSG:2154&TYPENAMES={couche}"
    "&count={nombre}&startIndex={debut}"
)
COUCHES_CHEFS_LIEUX = {
    "ADMINEXPRESS-COG.2025:chef_lieu_de_commune": "code_insee_de_la_commune",
    "ADMINEXPRESS-COG.2025:chef_lieu_d_arrondissement_municipal": (
        "code_insee_de_l_arrondissement_municipal"
    ),
}
TAILLE_PAGE_WFS = 5000
CHEMIN_RAW_CHEFS_LIEUX = "raw/chefs_lieux_cog2025_20261103.parquet"
SHA256_CHEFS_LIEUX = "a43f55f677f463f10bb9487007426874fddf14a127a3e48021e787753e9849f6"
# Sous ce nombre de ventes, la médiane du prix d'une commune est manquante
MIN_VENTES_DVF = 10
# L'Alsace-Moselle n'est pas dans DVF : la robustesse au prix y est sans objet
AIRES_HORS_DVF = ("Strasbourg",)
# Délai de `requests` par lecture (pas la durée totale) et essais par URL
DELAI_TELECHARGEMENT_S = 120
NB_ESSAIS_TELECHARGEMENT = 3
# Zonage en aires d'attraction des villes 2020, géographie au 01/01/2025
URL_AAV = "https://www.insee.fr/fr/statistiques/fichier/4803954/AAV2020_au_01-01-2025.zip"
SHA256_AAV = "738f81b12832fe294bd24ddbfe3a31830c20d850143fc8b4393f18d4b8ee8181"
CHEMIN_RAW_AAV = "raw/AAV2020_au_01-01-2025.zip"
XLSX_AAV = "AAV2020_au_01-01-2025.xlsx"
FEUILLE_AAV = "Composition_communale"
ENTETE_AAV = 5
NB_COMMUNES_AAV = 34875
# `CATEAAV2020` : 11 commune-centre, 12 pôle principal, 13 pôle secondaire, 20 couronne, 30 hors
CATEGORIES_AAV = ("11", "12", "13", "20", "30")

# Série historique du recensement 2022 : population et superficie (km²), COG 2025
URL_SERIE_RP2022 = (
    "https://www.insee.fr/fr/statistiques/fichier/8582555/base-cc-serie-historique-2022_csv.zip"
)
SHA256_SERIE_RP2022 = "ff0187ec6bb77fd2e5da639c08159368ff152cad0682ee0908358a829830c273"
CHEMIN_RAW_SERIE_RP2022 = "raw/base-cc-serie-historique-2022_csv.zip"
CSV_SERIE_RP2022 = "base-cc-serie-historique-2022.CSV"
NB_LIGNES_SERIE_RP2022 = 34903

# « Évolution et structure de la population » 2022 : actifs de 25 à 54 ans par groupe
# socioprofessionnel en 2011 et 2022, COG 2025, arrondissements de Lyon compris
URL_EVOL_STRUCT_RP2022 = (
    "https://www.insee.fr/fr/statistiques/fichier/8581696/base-cc-evol-struct-pop-2022_csv.zip"
)
SHA256_EVOL_STRUCT_RP2022 = "cb4b918862289527232ad79fb3b712d5f4635c6de5bae762e8d22a132717ed83"
CHEMIN_RAW_EVOL_STRUCT_RP2022 = "raw/base-cc-evol-struct-pop-2022_csv.zip"
CSV_EVOL_STRUCT_RP2022 = "base-cc-evol-struct-pop-2022.CSV"
NB_LIGNES_EVOL_STRUCT_RP2022 = 34903
# Groupes 1 à 6 (occupés et chômeurs) : leur somme est le dénominateur, le groupe 3 le
# numérateur. Noms recopiés du fichier, qui dit `GSEC15_25` là où la page dit `GSEC16_25`
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
# Série historique des actifs de 25 à 54 ans par CSP : date -> géographie de sa feuille
URL_SERIE_CSP = "https://www.insee.fr/fr/statistiques/fichier/1893185/pop-act2554-csp-cd-6822.zip"
CHEMIN_RAW_SERIE_CSP = "raw/pop-act2554-csp-cd-6822.zip"
SHA256_SERIE_CSP = "cdbcb350a9c1315135471fc7f40e60e578428735eb6b1f8756ec26da82d4e168"
XLSX_SERIE_CSP = "pop-act2554-csp-cd-6822.xlsx"
ENTETE_SERIE_CSP = 15
GEOGRAPHIE_SERIE_CSP = {
    1999: "CODGEO_2003",
    2006: "CODGEO_2008",
    2011: "CODGEO_2013",
    2016: "CODGEO_2018",
    2022: "CODGEO_2024",
}
# Robustesse : cadres parmi la population de 15 ans ou plus en 2022
CADRES_15P_2022 = "C22_POP15P_STAT_GSEC13_23"
POP_15P_2022 = "C22_POP15P"
# Bases IRIS « Activité des résidents » : seuls les 15-64 ans y croisent la CSP
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
FEUILLE_ACTIVITE_IRIS_2011 = "IRIS"
ENTETE_ACTIVITE_IRIS_2011 = 5
NB_LIGNES_ACTIVITE_IRIS_2011 = 50867
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
# Contours des IRIS des aires retenues (cartiflette, COG 2025), copies gelées
CHEMIN_RAW_CONTOURS_IRIS = "raw/contours_iris_{aav}_20261021.parquet"
SHA256_CONTOURS_IRIS = {
    "008": "61e52233fcdd7fe09d0f0350b6a5060719ca83f0a56c7710848a5ae35d34ff23",
    "002": "5c77cb03f2cfb55e3e2634218f4f94b6b43f13ed1496e85572919dc271b43018",
    "010": "15b57329479d4261de4a443b9b4458332f92692b286caecbb270a3b678aad82c",
}
# Code IRIS des contours (COG 2025) -> code des données 2022 (COG 2024) : Porte des Pierres Dorées
IRIS_RECODES_2025_2024 = {"691140000": "691590000"}
# Table de passage des codes communes 2025 : repère les fusions entre 2013 et 2024
URL_PASSAGE_COG = (
    "https://www.insee.fr/fr/statistiques/fichier/7671867/table_passage_annuelle_2025.zip"
)
SHA256_PASSAGE_COG = "803527a040748f4c7dc5e97777cb5838e8b7d4cc36d0b182f53a83e9787d595b"
CHEMIN_RAW_PASSAGE_COG = "raw/table_passage_annuelle_2025.zip"
XLSX_PASSAGE_COG = "table_passage_annuelle_2025.xlsx"
FEUILLE_PASSAGE_COG = "COM"
ENTETE_PASSAGE_COG = 5
NB_LIGNES_PASSAGE_COG = 36760

# Lycées retenus : `code_nature` 300, 301, 302 et 306 (général, technologique, polyvalent)
NATURES_LYCEES = (300, 301, 302, 306)
# `code_type_contrat_prive` du privé sous contrat d'association
CONTRATS_PRIVE_RETENUS = ("30", "31")
# Robustesse : lycées professionnels (320) et privé hors contrat (10) réintégrés
NATURES_LYCEES_ROBUSTESSE = (*NATURES_LYCEES, 320)
CONTRATS_PRIVE_ROBUSTESSE = (*CONTRATS_PRIVE_RETENUS, "10")
# Lycées de cette robustesse sans coordonnées, écartés nommément ; tout autre fait échouer
UAI_SANS_POSITION_ROBUSTESSE = (
    "0443105L",
    "0313176J",
    "0581019T",
    "0783920M",
    "0212319G",
    "0756899S",
    "0756960H",
)
# Lycée retenu sans statut public ou privé dans l'annuaire (Eure, loin des aires) : écarté
UAI_SANS_STATUT = ("0271911F",)

# Contours communaux de cartiflette : sans `year`, il prendrait l'année courante ; sans
# simplification nulle, les centroïdes bougeraient
ANNEE_COG = 2025
SIMPLIFICATION_CONTOURS = 0
# Une copie gelée par aire : le serveur et le client de cartiflette changent
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
# Contours des départements : leur union donne le contour de la métropole (frontière)
CHEMIN_RAW_DEPARTEMENTS = "raw/contours_departements_20261020.parquet"
SHA256_DEPARTEMENTS = "a6e4d3b3a7657f61b8fe9b710efa5f50c0cab76cde0d522f4cfd4adfdbe405ca"
NB_DEPARTEMENTS_METROPOLE = 96
# Pôle ou couronne selon `CATEAAV2020` ; un autre code fait échouer le référentiel
POLE_COURONNE_AAV = {"11": "pole", "12": "pole", "20": "couronne"}
# Communes à arrondissements municipaux des aires candidates et leur nombre
NB_ARRONDISSEMENTS = {"69123": 9}
CATEGORIE_COMMUNE_CENTRE = "11"

# IPS des lycées : export de l'API, copie gelée
URL_IPS = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-ips-lycees-ap2023/exports/csv"
)
SHA256_IPS = "31b2aafd8fb4597608c55f8f78f7144444a350df795111a651fb5222ee9c8aa7"
CHEMIN_RAW_IPS = "raw/ips_lycees_20261013.csv"
NB_LIGNES_IPS = 10905
# Rentrée la plus récente, voie générale et technologique ; lycées professionnels exclus
RENTREE_IPS = "2025-2026"
COLONNE_IPS = "ips_voie_gt"
TYPES_LYCEES_IPS = ("LEGT", "LPO")
# Lycées de l'IPS situés dans les 8 aires candidates mais pas retenus (fusionnés sous un autre
# UAI, hors contrat dans l'annuaire, agricole ou climatique) : à revoir si la rentrée change
UAI_IPS_NON_RETENUS = (
    "0352867B",
    "0380097Z",
    "0440256P",
    "0440279P",
    "0441653H",
    "0596281G",
    "0596681S",
)

# IVAL des lycées généraux et technologiques : export de l'API, copie gelée
URL_IVAL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-indicateurs-de-resultat-des-lycees-gt_v2/exports/csv"
)
SHA256_IVAL = "6ab77b391e3405f5157bb942d4548d5f1cfbacd94e76dd52b93db9b370de8658"
CHEMIN_RAW_IVAL = "raw/ival_lycees_gt_20261020.csv"
NB_LIGNES_IVAL = 32485
# Sessions du bac entre les deux recensements et nombre minimal de sessions renseignées
PREMIERE_SESSION_IVAL = 2012
DERNIERE_SESSION_IVAL = 2022
NB_SESSIONS_MIN_IVAL = 5
# Valeur ajoutée du taux d'accès de la seconde au bac ; taux de réussite et 2012-2025 en robustesse
INDICATEUR_IVAL = "va_acces_2nde"
INDICATEUR_IVAL_ROBUSTESSE = "va_reu_total"
DERNIERE_SESSION_IVAL_ROBUSTESSE = 2025
# Fiabilité de l'IVAL : deux moitiés, sessions minimales dans chacune, seuil de testabilité de H3
MOITIES_IVAL = ((2012, 2017), (2018, 2022))
NB_SESSIONS_MIN_MOITIE = 3
SEUIL_FIABILITE_IVAL = 0.5
# Au-delà de 5 % de tirages écartés (rang incomplet), l'intervalle n'est pas rapporté
MAX_TIRAGES_ECARTES = 50
CATEGORIES_TIERS_IVAL = ("1er tiers", "2e tiers", "3e tiers", "sans IVAL")
# Seuil des petites communes (actifs de 25 à 54 ans) et permutations de l'indice de Moran
ACTIFS_MIN_ROBUSTESSE = 200
NB_PERMUTATIONS_MORAN = 999
# Lycées publiés dans l'IVAL sous un autre UAI que dans l'annuaire -> UAI de l'annuaire
UAI_IVAL_RATTACHES = {
    "0440256P": "0443088T",
    "0440279P": "0443088T",
    "0441653H": "0443088T",
    "0332835C": "0332346W",
    "0690535G": "0690574Z",
}
# Lycées de l'IVAL des 8 aires candidates qui ne sont pas des lycées retenus (professionnels,
# agricole, climatique, hors contrat, absent de l'annuaire)
UAI_IVAL_NON_RETENUS = (
    "0330018R",
    "0380097Z",
    "0590125R",
    "0593113N",
    "0596281G",
    "0596681S",
    "0694086S",
)

# Secteur de l'annuaire, puis de l'IPS -> secteur du projet
SECTEURS = {"Public": "public", "Privé": "prive"}
SECTEURS_IPS = {"public": "public", "privé sous contrat": "prive"}
# Charte des figures : bleu et orange pour les secteurs, lisibles en cas de daltonisme
COULEURS_SECTEURS = {"public": "#2a78d6", "prive": "#eb6834"}
COULEUR_TEXTE = "#52514e"
COULEUR_LIAISON = "#c3c2b7"
COULEUR_GRILLE = "#ececea"
COULEUR_FOND_RETENUES = "#f0efec"
DATE_ANNUAIRE = "13/10/2026"
LIBELLES_SECTEURS = {"public": "public", "prive": "privé sous contrat"}
# Taille des notes sous les figures, lisible une fois la figure réduite à la colonne
TAILLE_NOTE_FIGURES = 10.5
# Une couleur par aire (palette d'Okabe et Ito), distincte des couleurs des secteurs
COULEURS_AIRES = {"Nantes": "#009e73", "Lyon": "#a2559c", "Strasbourg": "#9c6b1f"}


# `carte_acces` : bornes supérieures (incluses) des classes de distance ; « 5 km ou moins »
# équivaut à au moins un lycée privé dans le rayon principal
BORNES_DISTANCE_KM = (*RAYONS_KM, 20)
# ColorBrewer « Greens », du plus proche (foncé) au plus loin
COULEURS_DISTANCE = ("#006d2c", "#31a354", "#74c476", "#bae4b3", "#edf8e9")
# Simplification des contours pour l'affichage seulement (limites déplacées de 150 m au plus)
SIMPLIFICATION_CARTE_M = 50
# Fonds de carte sans clé d'accès, nommés comme dans xyzservices
FONDS_CARTE = {"Fond gris (Esri)": "Esri.WorldGrayCanvas", "Plan IGN": "GeoportailFrance.plan"}

# Carte IRIS : classes de part de cadres en % (borne basse incluse), ColorBrewer « Purples »
BORNES_PART_CADRES_IRIS = (10, 20, 30, 40, 50)
COULEURS_PART_CADRES_IRIS = ("#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8", "#756bb1", "#54278f")
COULEUR_IRIS_NON_COMPARABLE = "#e3e2de"
# Demi-côté du zoom sur la commune-centre : 9 km couvrent celle de Strasbourg et Villeurbanne
ZOOM_IRIS_KM = 9

# Fichiers bruts lus par le projet et leur sha256, listés en annexe ; `{aav}` : un par aire
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
    (CHEMIN_RAW_DVF, SHA256_DVF),
    (CHEMIN_RAW_CHEFS_LIEUX, SHA256_CHEFS_LIEUX),
    (CHEMIN_RAW_AAV, SHA256_AAV),
    (CHEMIN_RAW_PASSAGE_COG, SHA256_PASSAGE_COG),
    (CHEMIN_RAW_SERIE_RP2022, SHA256_SERIE_RP2022),
    (CHEMIN_RAW_EVOL_STRUCT_RP2022, SHA256_EVOL_STRUCT_RP2022),
    (CHEMIN_RAW_SERIE_CSP, SHA256_SERIE_CSP),
    (CHEMIN_RAW_ACTIVITE_IRIS_2011, SHA256_ACTIVITE_IRIS_2011),
    (CHEMIN_RAW_ACTIVITE_IRIS_2022, SHA256_ACTIVITE_IRIS_2022),
)
