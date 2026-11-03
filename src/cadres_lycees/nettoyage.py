"""Nettoyage et jointures des sources : lycées (aire, IPS, IVAL), population, part de cadres."""

import geopandas as gpd
import numpy as np
import pandas as pd

from cadres_lycees import config


def lycees_geo(
    annuaire: gpd.GeoDataFrame,
    ips: pd.DataFrame,
    sessions_ival: pd.DataFrame,
    referentiel: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Renvoie les lycées de l'annuaire avec leur aire, leur secteur, leur IPS et leur IVAL.

    Une ligne par lycée, en Lambert 93, avec `uai`, `nom_lycee`, `code_commune`, `secteur`,
    `aire` (manquante hors des aires), `ips`, `ival`, `poids_ival` et `geometry`. `annuaire`,
    `ips` et `sessions_ival` viennent de `collecte`, `referentiel` de `geo.referentiel_communes`.
    """
    lycees = _un_lycee_par_uai(annuaire)
    lycees = _ajouter_aire(lycees, referentiel)
    lycees = _ajouter_ips(lycees, ips, referentiel)
    return _ajouter_ival(lycees, sessions_ival, referentiel)


def lycees_prives(annuaire: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Renvoie les lycées privés de l'annuaire filtré, un par UAI, en Lambert 93.

    Pour la robustesse « lycées professionnels et privé hors contrat inclus » (§5.6), qui n'a
    besoin que des positions : ni aire, ni IPS, ni IVAL. Les lycées sans coordonnées de
    `config.UAI_SANS_POSITION_ROBUSTESSE` sont écartés.
    """
    sans_position = annuaire.geometry.isna() | annuaire.geometry.is_empty
    uai_sans_position = sorted(annuaire.loc[sans_position, "identifiant_de_l_etablissement"])
    assert uai_sans_position == sorted(config.UAI_SANS_POSITION_ROBUSTESSE), (
        f"Lycées sans coordonnées : {uai_sans_position}, attendus : "
        f"{sorted(config.UAI_SANS_POSITION_ROBUSTESSE)} (config.UAI_SANS_POSITION_ROBUSTESSE)."
    )
    lycees = _un_lycee_par_uai(annuaire[~sans_position])
    return lycees[lycees["secteur"] == "prive"]


def _un_lycee_par_uai(annuaire: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Renvoie une ligne par UAI de l'annuaire filtré, renommée, avec son secteur, en Lambert 93.

    La sélection des lycées est faite par `collecte.annuaire_education`. Un UAI multi-sites
    compte pour un lycée. Tous les lycées doivent avoir des coordonnées.
    """
    # Un UAI multi-sites occupe plusieurs lignes, avec la même commune et les mêmes coordonnées
    nb_communes = annuaire.groupby("identifiant_de_l_etablissement")["code_commune"].nunique()
    assert (nb_communes == 1).all(), "Un UAI a plusieurs communes dans l'annuaire."
    lycees = annuaire.drop_duplicates("identifiant_de_l_etablissement")
    # L'annuaire nomme `position` sa colonne de coordonnées, le reste du code attend `geometry`
    lycees = lycees.rename_geometry("geometry").rename(
        columns={"identifiant_de_l_etablissement": "uai", "nom_etablissement": "nom_lycee"}
    )

    lycees["secteur"] = lycees["statut_public_prive"].map(config.SECTEURS)
    colonnes = ["uai", "nom_lycee", "code_commune", "secteur", "geometry"]
    lycees = lycees[colonnes].to_crs(config.CRS_CALCUL)

    # Tous les lycées servent aux distances : un lycée sans position les fausserait sans bruit
    sans_position = lycees.geometry.isna() | lycees.geometry.is_empty
    assert not sans_position.any(), (
        f"Lycées sans coordonnées : {lycees.loc[sans_position, 'uai'].tolist()}."
    )
    return lycees


def _ajouter_aire(lycees: gpd.GeoDataFrame, referentiel: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ajoute l'aire du lycée, d'après le code de sa commune.

    L'annuaire nomme les arrondissements de Lyon (693xx) comme le référentiel. Un lycée hors des
    aires garde une aire manquante : il compte quand même dans l'accessibilité des communes
    proches.
    """
    # On vérifie que la position dit la même chose que le code (code dans le référentiel si et
    # seulement si position dans une aire) : une commune fusionnée sous un nouveau code
    # laisserait sinon son lycée sans aire, sans bruit. La position des lycées hors des aires
    # n'est pas contrôlée
    zone = referentiel.geometry.union_all()
    commune_connue = lycees["code_commune"].isin(referentiel["code_commune"])
    dans_une_aire = lycees.geometry.within(zone)
    desaccord = commune_connue != dans_une_aire
    assert not desaccord.any(), (
        f"Code commune et position en désaccord pour {lycees.loc[desaccord, 'uai'].tolist()}."
    )
    lycees = lycees.merge(
        referentiel[["code_commune", "aire"]], on="code_commune", how="left", validate="many_to_one"
    )
    assert set(lycees["aire"].dropna()) == set(referentiel["aire"]), "Une aire n'a aucun lycée."
    return lycees


def _ajouter_ips(
    lycees: gpd.GeoDataFrame, ips: pd.DataFrame, referentiel: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Ajoute l'IPS de la rentrée et de la mesure choisies dans `config`.

    Il reste manquant pour un lycée sans IPS : une valeur manquante ne se remplace pas.
    """
    ips_rentree = ips[
        (ips["rentree_scolaire"] == config.RENTREE_IPS)
        & ips["type_de_lycee"].isin(config.TYPES_LYCEES_IPS)
    ].copy()
    assert not ips_rentree.empty, f"Pas d'IPS pour la rentrée {config.RENTREE_IPS}."
    ips_rentree["ips"] = pd.to_numeric(ips_rentree[config.COLONNE_IPS])
    ips_rentree["secteur_ips"] = ips_rentree["secteur"].map(config.SECTEURS_IPS)
    # Un UAI mal recopié dans la liste ne serait jamais attendu ci-dessous, donc jamais vu
    absents = sorted(set(config.UAI_IPS_NON_RETENUS) - set(ips_rentree["uai"]))
    assert not absents, f"UAI de config.UAI_IPS_NON_RETENUS absents de l'IPS : {absents}."

    # Des lycées de l'IPS situés dans les aires manquent aux lycées des aires, car l'annuaire les
    # filtre, les regroupe sous un autre UAI ou les place ailleurs : on exige que ce soient ceux
    # de `config` situés dans les aires étudiées
    dans_les_aires = ips_rentree["code_insee_de_la_commune"].isin(referentiel["code_commune"])
    uai_des_aires = set(ips_rentree.loc[dans_les_aires & ips_rentree["ips"].notna(), "uai"])
    non_retenus = sorted(uai_des_aires - set(lycees.loc[lycees["aire"].notna(), "uai"]))
    attendus = sorted(uai_des_aires & set(config.UAI_IPS_NON_RETENUS))
    assert non_retenus == attendus, (
        f"Lycées de l'IPS absents des lycées des aires : {non_retenus}, attendus : {attendus} "
        "(config.UAI_IPS_NON_RETENUS)."
    )

    lycees = lycees.merge(
        ips_rentree[["uai", "ips", "secteur_ips"]], on="uai", how="left", validate="many_to_one"
    )
    # Un secteur différent d'une source à l'autre attribuerait l'IPS au mauvais secteur
    secteur_different = lycees["secteur_ips"].notna() & (lycees["secteur"] != lycees["secteur_ips"])
    uai_differents = lycees.loc[secteur_different, "uai"].tolist()
    assert not uai_differents, f"Secteur différent dans l'annuaire et l'IPS : {uai_differents}."
    return lycees.drop(columns="secteur_ips")


def _ajouter_ival(
    lycees: gpd.GeoDataFrame, sessions_ival: pd.DataFrame, referentiel: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Ajoute `ival` et `poids_ival` (voir `ival_par_lycee`) ; manquants hors de la règle A1."""
    ival = ival_par_lycee(
        sessions_ival,
        config.PREMIERE_SESSION_IVAL,
        config.DERNIERE_SESSION_IVAL,
        config.NB_SESSIONS_MIN_IVAL,
    )
    # Un UAI mal recopié dans la liste ne serait jamais attendu ci-dessous, donc jamais vu
    absents = sorted(set(config.UAI_IVAL_NON_RETENUS) - set(ival.index))
    assert not absents, f"UAI de config.UAI_IVAL_NON_RETENUS absents de l'IVAL : {absents}."
    # Comme pour l'IPS : des lycées de l'IVAL situés dans les aires ne sont pas des lycées
    # retenus (nature, contrat, fermeture) ; on exige que ce soient ceux de `config` situés dans
    # les aires étudiées, pour qu'un lycée publié sous un autre UAI ne perde pas son IVAL sans
    # erreur
    dans_les_aires = sessions_ival["code_commune"].isin(referentiel["code_commune"])
    uai_des_aires = set(sessions_ival.loc[dans_les_aires, "uai"].replace(config.UAI_IVAL_RATTACHES))
    uai_avec_ival = uai_des_aires & set(ival.index)
    non_retenus = sorted(uai_avec_ival - set(lycees["uai"]))
    attendus = sorted(uai_avec_ival & set(config.UAI_IVAL_NON_RETENUS))
    assert non_retenus == attendus, (
        f"Lycées de l'IVAL absents des lycées retenus : {non_retenus}, attendus : {attendus} "
        "(config.UAI_IVAL_NON_RETENUS)."
    )
    return lycees.merge(ival, left_on="uai", right_index=True, how="left", validate="many_to_one")


def population(serie: pd.DataFrame, referentiel: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie la population 2022 et la densité des communes du référentiel, par `code_commune`.

    `serie` vient de `collecte.serie_historique_rp2022`. `densite` est en habitants par km², avec
    `SUPERF`, la superficie de l'Insee, et non la surface des contours : même source que la
    population (journal du 20/10). `log_densite` est la forme sous laquelle la
    densité sert de contrôle (A7), tant sa distribution est asymétrique. Les communes sont celles
    du référentiel, au grain des arrondissements à Lyon : la commune parente 69123 n'est jamais
    lue, ce qui évite de compter Lyon deux fois. Le résultat se joint par `code_commune`.
    """
    pop_superficie = _lignes_du_referentiel(serie, referentiel, ["P22_POP", "SUPERF"])
    assert pop_superficie.notna().all().all(), "Population ou superficie manquante."
    assert (pop_superficie["SUPERF"] > 0).all(), "Superficie nulle ou négative."
    # Une commune sans habitant aurait une densité nulle, et un logarithme infini
    assert (pop_superficie["P22_POP"] > 0).all(), "Commune sans habitant."

    densite = pop_superficie["P22_POP"] / pop_superficie["SUPERF"]
    return pd.DataFrame(
        {"pop_2022": pop_superficie["P22_POP"], "densite": densite, "log_densite": np.log(densite)}
    )


def part_cadres(effectifs: pd.DataFrame, referentiel: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie la part de cadres parmi les actifs de 25 à 54 ans en 2011 et en 2022.

    `effectifs` vient de `collecte.evol_struct_rp2022`. La part est le groupe 3 (cadres et
    professions intellectuelles supérieures) divisé par la somme des 6 groupes, c'est-à-dire les
    actifs occupés et les chômeurs ayant déjà travaillé (PLAN §2.3, A11) : une fraction entre 0
    et 1. `evol_cadres_pts` est la part de 2022 moins celle de 2011, en points de pourcentage.
    `actifs_2022` sert de poids (§3.2) ; le seuil de 200 actifs de H3 se lit sur le plus petit de
    `actifs_2011` et `actifs_2022` (A17). `part_cadres_15p_2022`, les cadres parmi la population
    de 15 ans ou plus en 2022, sert à la robustesse (§2.3). Lyon est lue au grain de ses
    arrondissements, comme dans `population`. Une commune sans actif à une date n'a pas de part à
    cette date : A17 veut ces communes nommées dans `config`, mais aucune des aires retenues
    n'est dans ce cas (voir `config.ACTIFS_2554_2011`) ; une commune sans actif fait donc
    échouer. Le résultat se joint par `code_commune`.
    """
    colonnes = [
        *config.ACTIFS_2554_2011,
        *config.ACTIFS_2554_2022,
        config.CADRES_15P_2022,
        config.POP_15P_2022,
    ]
    actifs = _lignes_du_referentiel(effectifs, referentiel, colonnes)
    assert actifs.notna().all().all(), "Effectif d'actifs de 25 à 54 ans manquant."
    actifs_2011 = actifs[list(config.ACTIFS_2554_2011)].sum(axis=1)
    actifs_2022 = actifs[list(config.ACTIFS_2554_2022)].sum(axis=1)
    sans_actif = sorted(actifs.index[(actifs_2011 <= 0) | (actifs_2022 <= 0)])
    assert not sans_actif, (
        f"Communes sans actif de 25 à 54 ans en 2011 ou 2022, à nommer dans config (A17) : "
        f"{sans_actif}"
    )

    part_2011 = actifs[config.CADRES_2554_2011] / actifs_2011
    part_2022 = actifs[config.CADRES_2554_2022] / actifs_2022
    assert (actifs[config.POP_15P_2022] > 0).all(), "Commune sans habitant de 15 ans ou plus."
    part_15p_2022 = actifs[config.CADRES_15P_2022] / actifs[config.POP_15P_2022]
    # Le numérateur est une partie du dénominateur : hors de [0, 1], un effectif est négatif
    parts = (part_2011, part_2022, part_15p_2022)
    assert all(part.between(0, 1).all() for part in parts), "Part de cadres hors de [0, 1]."
    return pd.DataFrame(
        {
            "part_cadres_2011": part_2011,
            "part_cadres_2022": part_2022,
            "evol_cadres_pts": (part_2022 - part_2011) * 100,
            "actifs_2011": actifs_2011,
            "actifs_2022": actifs_2022,
            "part_cadres_15p_2022": part_15p_2022,
        }
    )


def prix_m2(dvf: pd.DataFrame, referentiel: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie le prix médian au m² de chaque commune, et son logarithme (§3.2, robustesse).

    `dvf` vient de `collecte.statistiques_dvf`. `prix_m2_med` est manquant sous
    `config.MIN_VENTES_DVF` ventes (appartements et maisons), et pour toute l'Alsace-Moselle,
    absente de DVF. `log_prix_m2` sert de contrôle, comme `log_densite` (A7). Indexé par
    `code_commune` ; toute commune du référentiel doit être dans le fichier.
    """
    par_code = dvf.set_index("code_geo")
    manquantes = sorted(set(referentiel["code_commune"]) - set(par_code.index))
    assert not manquantes, f"Communes absentes des statistiques DVF : {manquantes[:10]}."
    lignes = par_code.loc[referentiel["code_commune"]]
    assez_de_ventes = lignes[config.COLONNE_VENTES_DVF] >= config.MIN_VENTES_DVF
    prix = lignes[config.COLONNE_PRIX_DVF].where(assez_de_ventes)
    assert (prix.dropna() > 0).all(), "Prix au m² nul ou négatif."
    return pd.DataFrame({"prix_m2_med": prix, "log_prix_m2": np.log(prix)}).rename_axis(
        "code_commune"
    )


def _lignes_du_referentiel(
    fichier_insee: pd.DataFrame, referentiel: gpd.GeoDataFrame, colonnes: list[str]
) -> pd.DataFrame:
    """Renvoie `colonnes` d'un fichier communal de l'Insee pour les communes du référentiel.

    `fichier_insee` a une colonne `CODGEO` ; le résultat est indexé par `code_commune`. Une
    commune du référentiel absente du fichier fait échouer, en nommant les colonnes cherchées.
    """
    fichier_insee = fichier_insee.set_index("CODGEO")
    manquantes = sorted(set(referentiel["code_commune"]) - set(fichier_insee.index))
    assert not manquantes, f"Communes absentes du fichier de {colonnes} : {manquantes}"
    return fichier_insee.loc[referentiel["code_commune"], colonnes].rename_axis("code_commune")


def part_cadres_iris(
    activite_2011: pd.DataFrame, activite_2022: pd.DataFrame, passage: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie la part de cadres parmi les actifs de 15 à 64 ans par IRIS, en 2011 et en 2022.

    Une ligne par IRIS de 2022 (index `iris`, codes de la géographie 2024). La part est le groupe
    3 sur la somme des 6 groupes, comme pour la commune (§2.3), mais sur les 15-64 ans, seule
    tranche que les bases IRIS croisent avec la CSP. Elle manque sans actif (IRIS d'activité ou de
    loisirs, ce qui n'est pas une erreur, contrairement à une commune sans actif en T5), et en 2011
    si le code n'existait pas. `comparable` est vrai si l'IRIS a le même code et une part aux
    deux dates, sauf l'IRIS unique (commune + 0000) d'une commune non découpée qui en a absorbé
    une autre entre les géographies 2013 et 2024 : il garde son code, mais pas son territoire
    (A18). Les arguments viennent de `collecte.activite_iris_2011`, `collecte.activite_iris_2022`
    et `collecte.passage_communes`.
    """
    actifs_2011, part_2011 = _actifs_et_part(
        activite_2011, config.ACTIFS_1564_IRIS_2011, config.CADRES_1564_IRIS_2011
    )
    actifs_2022, part_2022 = _actifs_et_part(
        activite_2022, config.ACTIFS_1564_IRIS_2022, config.CADRES_1564_IRIS_2022
    )
    # Les IRIS de 2022 font l'index ; un IRIS sans code en 2011 y a des valeurs manquantes
    parts = pd.DataFrame(
        {
            "actifs_1564_2011": actifs_2011,
            "part_cadres_1564_2011": part_2011,
            "actifs_1564_2022": actifs_2022,
            "part_cadres_1564_2022": part_2022,
        },
        index=actifs_2022.index,
    ).rename_axis("iris")

    # Une filiation à case vide (commune créée ou disparue) ne dit rien d'une fusion entre 2013
    # et 2024 ; une commune peut avoir plusieurs lignes, d'où les paires uniques
    filiations = passage.dropna().drop_duplicates()
    communes_2013 = filiations.groupby("CODGEO_2024")["CODGEO_2013"].nunique()
    fusionnees = communes_2013.index[communes_2013 > 1]
    # Dans une commune découpée, le territoire absorbé reçoit de nouveaux codes, déjà écartés
    # parce qu'absents en 2011 : seul l'IRIS unique d'une commune non découpée change en gardant
    # son code
    commune = activite_2022.set_index("IRIS")["COM"]
    iris_unique = parts.index.str.endswith("0000")
    agrandi = commune.isin(fusionnees).to_numpy() & iris_unique
    meme_code = parts.index.isin(actifs_2011.index)
    # Un IRIS sans actif à une date n'a pas de part à comparer
    deux_parts = parts[["part_cadres_1564_2011", "part_cadres_1564_2022"]].notna().all(axis=1)
    parts["comparable"] = meme_code & ~agrandi & deux_parts
    return parts


def _actifs_et_part(
    activite: pd.DataFrame, groupes: tuple[str, ...], cadres: str
) -> tuple[pd.Series, pd.Series]:
    """Renvoie, par IRIS, les actifs (somme des 6 groupes) et la part de cadres parmi eux."""
    effectifs = activite.set_index("IRIS")[list(groupes)]
    actifs = effectifs.sum(axis=1)
    part = (effectifs[cadres] / actifs).where(actifs > 0)
    assert part.dropna().between(0, 1).all(), "Part de cadres hors de [0, 1]."
    return actifs, part


def ival_par_lycee(
    sessions_ival: pd.DataFrame, premiere: int, derniere: int, nb_sessions_min: int
) -> pd.DataFrame:
    """Renvoie l'IVAL de chaque lycée sur les sessions `premiere` à `derniere`, indexée par `uai`.

    `ival` est la moyenne simple des `va_acces_2nde` de ces sessions, pour les lycées qui en ont
    au moins `nb_sessions_min` où la valeur ajoutée est renseignée ; `poids_ival` est la moyenne
    de `presents_total` sur ces sessions. Les autres lycées sont absents du résultat. La règle A1
    (PLAN §2.4) correspond aux valeurs de `config` ; le test de fiabilité (§3.2) l'applique à
    chaque moitié. Les sessions des UAI de
    `config.UAI_IVAL_RATTACHES` sont rattachées à l'UAI de l'annuaire : quand plusieurs sites
    publient la même session, elle vaut la valeur ajoutée moyenne des sites renseignés, pondérée
    par leurs présents, et ses présents sont ceux de ces sites additionnés.
    """
    rattaches = config.UAI_IVAL_RATTACHES
    assert set(rattaches) <= set(sessions_ival["uai"]), "Un UAI rattaché manque à l'IVAL."

    sessions = pd.DataFrame(
        {
            "uai": sessions_ival["uai"].replace(rattaches),
            "annee": sessions_ival["annee"].astype(int),
            "va_acces_2nde": pd.to_numeric(sessions_ival["va_acces_2nde"]),
            "presents_total": pd.to_numeric(sessions_ival["presents_total"]),
        }
    )
    dans_la_periode = sessions["annee"].between(premiere, derniere)
    valides = sessions[dans_la_periode & sessions["va_acces_2nde"].notna()].copy()
    assert (valides["presents_total"] > 0).all(), "Session valide sans présents."

    # Pour un lycée d'un seul site, la moyenne pondérée d'une session est sa valeur ajoutée
    valides["va_x_presents"] = valides["va_acces_2nde"] * valides["presents_total"]
    par_session = valides.groupby(["uai", "annee"])[["va_x_presents", "presents_total"]].sum()
    par_session["va"] = par_session["va_x_presents"] / par_session["presents_total"]

    par_lycee = par_session.groupby("uai").agg(
        ival=("va", "mean"),
        poids_ival=("presents_total", "mean"),
        nb_sessions=("va", "size"),
    )
    retenus = par_lycee[par_lycee["nb_sessions"] >= nb_sessions_min]
    return retenus[["ival", "poids_ival"]]
