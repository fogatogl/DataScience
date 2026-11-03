"""Collecte des sources de données : copies brutes dans raw/, contrôlées par leur sha256."""

import hashlib
import io
import zipfile

import geopandas as gpd
import pandas as pd
import requests
from cartiflette import carti_download

from cadres_lycees import config, stockage


def _copies_publiques(chemin: str) -> list[str]:
    """Renvoie les URL publiques d'une copie gelée : le bucket du projet, puis la release."""
    return [config.URL_COPIES_S3 + chemin, config.URL_COPIES_RELEASE + chemin.removeprefix("raw/")]


def geler_annuaire(chemin: str) -> str:
    """Écrit à `chemin` l'export complet de l'annuaire par l'API et renvoie son sha256.

    Produit une copie gelée : celle du 13/10/2026 vient de là. Le rapport ne l'appelle pas, il
    lit la copie gelée (`annuaire_education`). Mode d'emploi dans le README.
    """
    return _geler_export_parquet(config.URL_ANNUAIRE, chemin)


def geler_gares(chemin: str) -> str:
    """Écrit à `chemin` l'export complet des gares de voyageurs et renvoie son sha256.

    Produit la copie gelée du 03/11/2026 ; le rapport lit cette copie (`gares`). Mode d'emploi
    dans le README.
    """
    return _geler_export_parquet(config.URL_GARES, chemin)


def geler_apl(chemin: str) -> str:
    """Écrit à `chemin` le fichier de l'APL aux médecins généralistes et renvoie son sha256.

    Produit la copie gelée du 03/11/2026 ; le rapport lit cette copie (`apl_medecins`).
    """
    assert not stockage.existe(chemin), f"{chemin} existe déjà : choisir un autre chemin daté."
    reponse = requests.get(config.URL_APL, timeout=config.DELAI_TELECHARGEMENT_S)
    reponse.raise_for_status()
    # Un xlsx est une archive zip : testzip relit chaque fichier et échoue si l'archive est tronquée
    assert zipfile.ZipFile(io.BytesIO(reponse.content)).testzip() is None, (
        "Le fichier de l'APL est abîmé : rien n'a été enregistré."
    )
    stockage.ecrire_octets(reponse.content, chemin)
    return hashlib.sha256(reponse.content).hexdigest()


def geler_equipements_sportifs(chemin: str) -> str:
    """Écrit à `chemin` l'export complet de Data ES et renvoie son sha256.

    Produit la copie gelée du 03/11/2026 ; le rapport lit cette copie (`equipements_sportifs`).
    Le serveur peut répondre 200 avec un flux tronqué par une erreur : le contrôle de
    `_geler_export_parquet` le refuse.
    """
    return _geler_export_parquet(config.URL_EQUIPEMENTS_SPORTIFS, chemin)


def geler_bpe(chemin: str) -> str:
    """Écrit à `chemin` le fichier détail de la BPE 2025 et renvoie son sha256.

    Produit la copie gelée du 03/11/2026 ; le rapport lit cette copie (`equipements_culturels`).
    """
    return _geler_export_parquet(config.URL_BPE, chemin)


def _geler_export_parquet(url: str, chemin: str) -> str:
    """Écrit à `chemin` l'export Parquet téléchargé à `url` et renvoie son sha256."""
    # Un chemin daté déjà pris est une copie gelée, peut-être publique : on ne l'écrase jamais
    assert not stockage.existe(chemin), f"{chemin} existe déjà : choisir un autre chemin daté."
    reponse = requests.get(url, timeout=config.DELAI_TELECHARGEMENT_S)
    reponse.raise_for_status()
    # Une réponse 200 peut être tronquée ; "PAR1" ouvre et ferme tout fichier Parquet
    assert reponse.content.startswith(b"PAR1") and reponse.content.endswith(b"PAR1"), (
        f"L'export de {url} n'est pas un fichier Parquet complet : rien n'a été enregistré."
    )
    stockage.ecrire_octets(reponse.content, chemin)
    return hashlib.sha256(reponse.content).hexdigest()


def annuaire_education() -> gpd.GeoDataFrame:
    """Renvoie les lycées de France métropolitaine de l'annuaire de l'éducation.

    Lycées généraux, technologiques et polyvalents, publics ou privés sous contrat (PLAN §2.4),
    repérés par `code_nature` car les `voie_*` de l'annuaire sont trop souvent vides. Toute la
    métropole est gardée, pas seulement les aires et une marge autour : le lycée le plus proche
    d'une commune du bord peut être bien au-delà de l'aire. Une ligne par site : un UAI
    multi-sites apparaît plusieurs fois (dédoublonné au nettoyage). Lu dans la copie gelée du
    13/10/2026, jamais dans l'API, qui change chaque jour.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_ANNUAIRE),
        config.CHEMIN_RAW_ANNUAIRE,
        config.SHA256_ANNUAIRE,
    )
    annuaire = gpd.read_parquet(io.BytesIO(contenu))

    # L'annuaire écrit les départements sur trois caractères : de "001" à "095", "02A" et "02B"
    # en métropole, à partir de "971" outre-mer
    metropole = annuaire["code_departement"].str.startswith("0")
    # Le type "Lycée" isole la partie lycée d'une cité scolaire, dont la partie collège
    # (type "Collège") porte le même UAI
    est_lycee = annuaire["type_etablissement"] == "Lycée"
    nature_retenue = annuaire["code_nature"].isin(config.NATURES_LYCEES)
    # `lycee_agricole` est parfois vide : on exclut aussi sur la tutelle
    pas_agricole = (annuaire["ministere_tutelle"] != "AGRICULTURE") & (
        annuaire["lycee_agricole"] != "1"
    )
    candidats = metropole & est_lycee & nature_retenue & pas_agricole

    # Un statut vide fait échouer les deux comparaisons plus bas : sans ce contrôle, le
    # lycée serait écarté sans bruit. Seuls les cas connus de `config` sont écartés
    statut_vide = candidats & annuaire["statut_public_prive"].isna()
    uai_sans_statut = sorted(annuaire.loc[statut_vide, "identifiant_de_l_etablissement"])
    assert uai_sans_statut == sorted(config.UAI_SANS_STATUT), (
        f"Lycées sans statut public ou privé : {uai_sans_statut}, attendus : "
        f"{sorted(config.UAI_SANS_STATUT)} (config.UAI_SANS_STATUT)."
    )

    est_public = annuaire["statut_public_prive"] == "Public"
    est_prive = annuaire["statut_public_prive"] == "Privé"
    contrat_retenu = annuaire["code_type_contrat_prive"].isin(config.CONTRATS_PRIVE_RETENUS)
    lycees = annuaire[candidats & (est_public | (est_prive & contrat_retenu))]
    return lycees.reset_index(drop=True)


def aav_2020() -> pd.DataFrame:
    """Renvoie la composition communale du zonage en aires d'attraction des villes 2020.

    Une ligne par commune du COG 2025, avec `AAV2020` (code de l'aire, "000" hors aire) et
    `CATEAAV2020` (commune-centre, pôle ou couronne). Tout est lu en chaîne : "013" perdrait son
    zéro en entier. Lyon, Marseille et Paris n'y figurent que par leur commune parente, pas par
    leurs arrondissements. Le zip de l'Insee est permanent : il est lu à son URL d'origine.
    """
    contenu = stockage.copie_controlee([config.URL_AAV], config.CHEMIN_RAW_AAV, config.SHA256_AAV)
    with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
        classeur = io.BytesIO(archive.read(config.XLSX_AAV))
    aav = pd.read_excel(
        classeur,
        sheet_name=config.FEUILLE_AAV,
        header=config.ENTETE_AAV,
        dtype=str,
        engine="calamine",
    )

    assert len(aav) == config.NB_COMMUNES_AAV, (
        f"{len(aav)} communes dans l'AAV, {config.NB_COMMUNES_AAV} attendues (COG 2025)."
    )
    assert aav["CODGEO"].is_unique, "Des codes communes sont en double dans l'AAV."
    categories_inconnues = set(aav["CATEAAV2020"]) - set(config.CATEGORIES_AAV)
    assert not categories_inconnues, f"Catégories AAV inconnues : {sorted(categories_inconnues)}"
    return aav


def serie_historique_rp2022() -> pd.DataFrame:
    """Renvoie la population et la superficie du recensement 2022, par commune ou arrondissement.

    Colonnes `CODGEO`, `P22_POP` et `SUPERF` (km²), en COG 2025. Les arrondissements de Lyon,
    Marseille et Paris y figurent avec leur commune parente : sommer tout le fichier compterait
    ces villes deux fois. Le zip de l'Insee est permanent : il est lu à son URL d'origine.
    """
    contenu = stockage.copie_controlee(
        [config.URL_SERIE_RP2022], config.CHEMIN_RAW_SERIE_RP2022, config.SHA256_SERIE_RP2022
    )
    with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
        csv = io.BytesIO(archive.read(config.CSV_SERIE_RP2022))
    # Lu en nombre, "01001" deviendrait 1001 ; une colonne disparue fait échouer la lecture
    serie = pd.read_csv(
        csv, sep=";", usecols=["CODGEO", "P22_POP", "SUPERF"], dtype={"CODGEO": str}
    )

    assert len(serie) == config.NB_LIGNES_SERIE_RP2022, (
        f"{len(serie)} lignes dans la série historique, {config.NB_LIGNES_SERIE_RP2022} attendues."
    )
    assert serie["CODGEO"].is_unique, "Des codes communes sont en double dans la série historique."
    return serie


def evol_struct_rp2022() -> pd.DataFrame:
    """Renvoie les actifs de 25 à 54 ans par groupe socioprofessionnel, en 2011 et en 2022.

    Une ligne par commune ou arrondissement (`CODGEO`), en COG 2025, avec les colonnes de
    `config.ACTIFS_2554_2011` et `config.ACTIFS_2554_2022`. Les effectifs sont décimaux
    (exploitation complémentaire du recensement). Les arrondissements de Lyon, Marseille et Paris
    y figurent avec leur commune parente : sommer tout le fichier compterait ces villes deux
    fois. Le zip de l'Insee est permanent : il est lu à son URL d'origine.
    """
    contenu = stockage.copie_controlee(
        [config.URL_EVOL_STRUCT_RP2022],
        config.CHEMIN_RAW_EVOL_STRUCT_RP2022,
        config.SHA256_EVOL_STRUCT_RP2022,
    )
    with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
        csv = io.BytesIO(archive.read(config.CSV_EVOL_STRUCT_RP2022))
    colonnes = ["CODGEO", *config.ACTIFS_2554_2011, *config.ACTIFS_2554_2022]
    # Lu en nombre, "01001" deviendrait 1001 ; une colonne disparue fait échouer la lecture
    effectifs = pd.read_csv(csv, sep=";", usecols=colonnes, dtype={"CODGEO": str})

    assert len(effectifs) == config.NB_LIGNES_EVOL_STRUCT_RP2022, (
        f"{len(effectifs)} lignes dans « Évolution et structure », "
        f"{config.NB_LIGNES_EVOL_STRUCT_RP2022} attendues."
    )
    assert effectifs["CODGEO"].is_unique, "Des codes communes sont en double."
    return effectifs


def ival_lycees() -> pd.DataFrame:
    """Renvoie les indicateurs de valeur ajoutée des lycées GT : une ligne par lycée et session.

    Lu dans la copie gelée du 20/10/2026 de l'export de l'API (`config.URL_IVAL`). Tout est lu en
    chaîne, pour garder les codes communes tels quels (« 2A004 », zéros
    en tête) : la conversion des valeurs se fait au nettoyage.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_IVAL), config.CHEMIN_RAW_IVAL, config.SHA256_IVAL
    )
    ival = pd.read_csv(io.BytesIO(contenu), sep=";", encoding="utf-8-sig", dtype=str)

    assert len(ival) == config.NB_LIGNES_IVAL, (
        f"{len(ival)} lignes dans l'IVAL, {config.NB_LIGNES_IVAL} attendues."
    )
    assert not ival.duplicated(["uai", "annee"]).any(), "Lycée en double dans l'IVAL."
    return ival


def geler_contours(chemin: str, valeur: str, maille: str, filtre: str) -> str:
    """Écrit à `chemin` des contours téléchargés par cartiflette et renvoie leur sha256.

    `valeur`, `maille` et `filtre` sont les arguments `values`, `borders` et `filter_by` de
    `carti_download` : un code d'aire, "COMMUNE_ARRONDISSEMENT" et "AIRE_ATTRACTION_VILLES" pour
    les contours d'une aire ; "France", "DEPARTEMENT" et "FRANCE_ENTIERE" pour les départements.
    Produit une copie gelée : celles du 13/10 et du 20/10/2026 viennent de là. Le rapport ne
    l'appelle pas, il lit la copie gelée. Le sha256 fige une sérialisation (versions de geopandas
    et de pyarrow comprises), pas seulement des données. Mode d'emploi dans le README.
    """
    assert not stockage.existe(chemin), f"{chemin} existe déjà : choisir un autre chemin daté."
    contours = carti_download(
        values=valeur,
        borders=maille,
        filter_by=filtre,
        year=config.ANNEE_COG,
        simplification=config.SIMPLIFICATION_CONTOURS,
    )
    stockage.ecrire_parquet(contours, chemin)
    return hashlib.sha256(stockage.lire_octets(chemin)).hexdigest()


def contours_aire(code_aav: str) -> gpd.GeoDataFrame:
    """Renvoie les contours des communes d'une aire d'attraction, en WGS84 (COG 2025).

    Les arrondissements municipaux remplacent leur commune parente (Lyon 69123 devient 69381 à
    69389) ; `INSEE_COM` garde le code de la commune parente et `INSEE_COG` celui de l'unité. Lu
    dans la copie gelée du 13/10/2026.
    """
    chemin = config.CHEMIN_RAW_CONTOURS.format(aav=code_aav)
    contenu = stockage.copie_controlee(
        _copies_publiques(chemin), chemin, config.SHA256_CONTOURS[code_aav]
    )
    return gpd.read_parquet(io.BytesIO(contenu))


def contours_departements() -> gpd.GeoDataFrame:
    """Renvoie les contours des départements, DOM compris, en WGS84 (COG 2025).

    Leur union donne le contour de la France métropolitaine (`geo.distance_contour_national_km`).
    Lu dans la copie gelée du 20/10/2026.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_DEPARTEMENTS),
        config.CHEMIN_RAW_DEPARTEMENTS,
        config.SHA256_DEPARTEMENTS,
    )
    return gpd.read_parquet(io.BytesIO(contenu))


def ips_lycees() -> pd.DataFrame:
    """Renvoie l'IPS des lycées : une ligne par lycée et par rentrée, de 2023-2024 à 2025-2026.

    Lu dans la copie gelée du 13/10/2026 de l'export de l'API (`config.URL_IPS`). Tout est lu en
    chaîne, la conversion en nombres se fait au nettoyage.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_IPS), config.CHEMIN_RAW_IPS, config.SHA256_IPS
    )
    ips = pd.read_csv(io.BytesIO(contenu), sep=";", encoding="utf-8-sig", dtype=str)

    assert len(ips) == config.NB_LIGNES_IPS, (
        f"{len(ips)} lignes dans l'IPS, {config.NB_LIGNES_IPS} attendues."
    )
    assert not ips.duplicated(["uai", "rentree_scolaire"]).any(), "Lycée en double dans l'IPS."
    return ips


def gares() -> gpd.GeoDataFrame:
    """Renvoie les gares de voyageurs de SNCF Gares & Connexions, en Lambert 93 (H4, §5.7).

    Une ligne par gare (`id_gare`), avec `nom_gare`, `code_commune` et `segment_drg` (A nationale,
    B régionale, C locale ; plusieurs lettres pour une gare à plusieurs codes UIC). Toutes les
    gares sont gardées, comme les lycées : la gare la plus proche d'une commune du bord peut être
    hors de l'aire. Le fichier ne dit pas si une gare est fermée aux voyageurs. Lu dans la copie
    gelée du 03/11/2026.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_GARES), config.CHEMIN_RAW_GARES, config.SHA256_GARES
    )
    brut = pd.read_parquet(io.BytesIO(contenu))
    # L'export Opendatasoft donne la position en WKB, longitude et latitude en WGS84
    position = gpd.GeoSeries.from_wkb(brut["position_geographique"], crs=4326)
    liste = gpd.GeoDataFrame(
        {
            "id_gare": brut["id"],
            "nom_gare": brut["nom"],
            "code_commune": brut["codeinsee"],
            "segment_drg": brut["segment_drg"],
        },
        geometry=position.to_numpy(),
        crs=4326,
    ).to_crs(config.CRS_CALCUL)
    assert liste["id_gare"].is_unique, "Identifiant de gare en double."
    assert not (liste.geometry.is_empty | liste.geometry.isna()).any(), "Gare sans position."
    outre_mer = liste["code_commune"].str.startswith("97")
    assert not outre_mer.any(), f"Gares hors métropole : {list(liste.loc[outre_mer, 'nom_gare'])}."
    return liste


def apl_medecins() -> pd.Series:
    """Renvoie l'APL 2024 aux médecins généralistes, tous âges, par commune (H4, §5.7).

    Index `code_commune`, arrondissements municipaux à la place de leur commune parente, comme
    dans le référentiel. Indicateur déjà calculé par la DREES, utilisé tel quel (§5.7). Lu dans la
    copie gelée du 03/11/2026.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_APL), config.CHEMIN_RAW_APL, config.SHA256_APL
    )
    feuille = pd.read_excel(
        io.BytesIO(contenu),
        sheet_name=config.FEUILLE_APL,
        header=config.LIGNE_ENTETE_APL,
        skiprows=[config.LIGNE_ENTETE_APL + 1],
        dtype={config.COLONNE_CODE_APL: str},
        engine="calamine",
    )
    apl = feuille.set_index(config.COLONNE_CODE_APL)[config.COLONNE_APL].rename("apl_mg")
    assert apl.index.is_unique, "Code commune en double dans l'APL."
    assert apl.notna().all() and (apl >= 0).all(), "APL manquante ou négative."
    return apl.rename_axis("code_commune")


def equipements_sportifs() -> gpd.GeoDataFrame:
    """Renvoie les installations sportives en service de France métropolitaine, en Lambert 93.

    Une ligne par installation (`id_installation`), placée au point de son premier équipement
    dans l'ordre des numéros : les équipements d'une installation sont à 52 m les uns des autres
    en médiane, mais une moyenne de leurs points tomberait n'importe où pour un sentier ou un
    site de nature. Écartées : les installations hors service (`inst_hs_bool`, seul indicateur
    de fermeture), les équipements sans coordonnées et l'outre-mer. Toutes les familles sont
    gardées (H4, §5.7). Lu dans la copie gelée du 03/11/2026.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_EQUIPEMENTS_SPORTIFS),
        config.CHEMIN_RAW_EQUIPEMENTS_SPORTIFS,
        config.SHA256_EQUIPEMENTS_SPORTIFS,
    )
    colonnes = ["equip_numero", "inst_numero", "inst_hs_bool", "new_code", "equip_x", "equip_y"]
    brut = pd.read_parquet(io.BytesIO(contenu), columns=colonnes)
    assert brut["equip_numero"].is_unique, "Numéro d'équipement en double dans Data ES."
    # Outre-mer : codes 97x et 98x ; deux équipements n'ont pas de code commune
    metropole = brut["new_code"].notna() & ~brut["new_code"].str[:2].isin(["97", "98"])
    en_service = brut["inst_hs_bool"] != "Oui"
    situes = brut["equip_x"].notna() & brut["equip_y"].notna()
    retenus = brut[metropole & en_service & situes].sort_values("equip_numero")
    installations = retenus.drop_duplicates("inst_numero")
    points = gpd.points_from_xy(
        installations["equip_x"].astype(float), installations["equip_y"].astype(float), crs=4326
    )
    return gpd.GeoDataFrame(
        {
            "id_installation": installations["inst_numero"].to_numpy(),
            "code_commune": installations["new_code"].to_numpy(),
        },
        geometry=points,
    ).to_crs(config.CRS_CALCUL)


def equipements_culturels() -> gpd.GeoDataFrame:
    """Renvoie les équipements culturels de France métropolitaine de la BPE 2025, en Lambert 93.

    Une ligne par type d'équipement et par point (`type_equipement`) : une même adresse porte
    parfois deux labels du même type (un musée qui est aussi une maison des Illustres, une
    bibliothèque et le siège de son réseau), comptés une fois. Tous les équipements culturels de
    métropole sont géolocalisés, à 50 m près pour une qualité acceptable. Lu dans la copie gelée
    du 03/11/2026.
    """
    contenu = stockage.copie_controlee(
        _copies_publiques(config.CHEMIN_RAW_BPE), config.CHEMIN_RAW_BPE, config.SHA256_BPE
    )
    colonnes = ["SDOM", "TYPEQU", "DEPCOM", "EPSG", "LAMBERT_X", "LAMBERT_Y"]
    bpe = pd.read_parquet(
        io.BytesIO(contenu),
        columns=colonnes,
        filters=[("SDOM", "==", config.SOUS_DOMAINE_CULTURE_BPE)],
    )
    culture = bpe[bpe["EPSG"] == config.EPSG_BPE_METROPOLE]
    assert culture[["LAMBERT_X", "LAMBERT_Y"]].notna().all().all(), (
        "Équipement culturel de métropole sans coordonnées."
    )
    lieux = culture.drop_duplicates(["TYPEQU", "LAMBERT_X", "LAMBERT_Y"])
    return gpd.GeoDataFrame(
        {
            "type_equipement": lieux["TYPEQU"].to_numpy(),
            "code_commune": lieux["DEPCOM"].to_numpy(),
        },
        geometry=gpd.points_from_xy(lieux["LAMBERT_X"], lieux["LAMBERT_Y"]),
        crs=config.CRS_CALCUL,
    )
