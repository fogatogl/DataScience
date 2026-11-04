"""H3 : fiabilité de l'IVAL, population, estimation par bootstrap des grappes et verdict."""

import geopandas as gpd
import numpy as np
import pandas as pd

from cadres_lycees import accessibilite, analyse, config, nettoyage


def fiabilite_ival(
    base: gpd.GeoDataFrame, lycees: gpd.GeoDataFrame, sessions_ival: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie la fiabilité de `ival_moy_5km` (PLAN §3.2, A7), toutes aires ensemble puis par aire.

    `base` et `lycees` viennent de `pipeline.construire_base`, sur les 3 aires retenues. Pour
    chaque moitié de `config.MOITIES_IVAL`, `ival_moy_5km` est recalculée avec les lycées de la
    règle A1 qui ont assez de sessions dans les deux moitiés, et leurs poids A1. Colonnes : `r`
    (Pearson, après centrage par aire), `r_spearman_brown` (manquante si `r` est négatif),
    `n_communes_h3` (population de H3), `n_communes` (renseignées dans les deux moitiés) et
    `n_lycees` (lycées distincts à 5 km de ces communes). Seule la ligne « ensemble » tranche H3.
    """
    rayon = config.RAYON_PRINCIPAL_KM
    communes = base.set_index("code_commune")
    moities = [f"moitie_{rang}" for rang in range(1, len(config.MOITIES_IVAL) + 1)]

    retenus = lycees[lycees["ival"].notna()].copy()
    for moitie, (premiere, derniere) in zip(moities, config.MOITIES_IVAL, strict=True):
        ival = nettoyage.ival_par_lycee(
            sessions_ival, premiere, derniere, config.NB_SESSIONS_MIN_MOITIE
        )
        retenus[moitie] = retenus["uai"].map(ival["ival"])
    retenus = retenus.dropna(subset=moities)

    communes_h3 = communes[communes[f"n_lyc_{rayon}km"] > 0]
    par_commune = communes_h3[["aire"]].copy()
    for moitie in moities:
        acces = accessibilite.indicateurs(
            base, retenus, "lyc", rayons=(rayon,), attribut=moitie, poids="poids_ival"
        )
        par_commune[moitie] = acces[f"{moitie}_moy_{rayon}km"]
    # Une commune sort si aucun de ses lycées à 5 km n'a assez de sessions dans chaque moitié :
    # elle reste comptée dans `n_communes_h3`, pour que la perte se voie
    renseignees = par_commune.dropna(subset=moities)

    # Centrage par aire : H3 se lit dans chaque aire, les écarts entre aires ne doivent pas faire
    # la corrélation
    centrees = renseignees[moities] - renseignees.groupby("aire")[moities].transform("mean")
    centrees["aire"] = renseignees["aire"]
    # `indicateurs` ne dit pas quels lycées entrent dans chaque rayon : on refait la jointure
    # pour compter les lycées distincts
    centroides = communes.set_geometry("centroide")[["centroide"]]
    proches = gpd.sjoin(
        centroides.loc[centrees.index],
        retenus[["uai", "geometry"]],
        predicate="dwithin",
        distance=rayon * 1000,
    )

    groupes = {"ensemble": centrees}
    for aire, groupe in centrees.groupby("aire"):
        groupes[aire] = groupe
    lignes = {}
    for nom, groupe in groupes.items():
        assert len(groupe) >= 3, f"Trop peu de communes pour une corrélation ({nom})."
        r = groupe[moities[0]].corr(groupe[moities[1]])
        h3 = communes_h3 if nom == "ensemble" else communes_h3[communes_h3["aire"] == nom]
        lignes[nom] = {
            "r": r,
            # La formule suppose une fiabilité positive : pour r < 0, elle n'a pas de sens
            "r_spearman_brown": 2 * r / (1 + r) if r >= 0 else float("nan"),
            "n_communes_h3": len(h3),
            "n_communes": len(groupe),
            "n_lycees": proches.loc[groupe.index, "uai"].nunique(),
        }
    return pd.DataFrame.from_dict(lignes, orient="index")


def population_h3(base: gpd.GeoDataFrame, lycees: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie la population de H3 (§5.5, A16), une ligne par commune, indexée par son code.

    Les communes qui ont au moins un lycée retenu à 5 km. `avec_ival` dit si `ival_moy_5km` est
    renseignée (sinon, catégorie « sans IVAL », hors de l'estimation). Ajoute :
    `log_n_lyc_ival_5km` (logarithme du nombre de lycées à 5 km qui ont une IVAL) et
    `ival_reduite`, `log_n_reduit`, ces deux variables centrées réduites une seule fois dans
    chaque aire sur les communes avec IVAL ; `anneau`, l'anneau du §5.2 sans fusion ; `grappe`,
    l'UAI du lycée avec IVAL le plus proche du centroïde, unité du bootstrap.
    """
    rayon = config.RAYON_PRINCIPAL_KM
    avec_ival_lycees = lycees[lycees["ival"].notna()]
    population = base[base[f"n_lyc_{rayon}km"] > 0]
    comptes = accessibilite.indicateurs(population, avec_ival_lycees, "lyc_ival", rayons=(rayon,))

    centroides = gpd.GeoDataFrame(
        population[["code_commune"]], geometry=population["centroide"], crs=population.crs
    )
    proches = gpd.sjoin_nearest(centroides, avec_ival_lycees[["uai", "geometry"]])
    # Deux lycées à égale distance donneraient deux lignes : on garde le premier UAI, sans effet
    # sur l'estimation (ce n'est que le regroupement du bootstrap)
    proches = proches.sort_values("uai").drop_duplicates("code_commune")
    grappes = proches.set_index("code_commune")["uai"]

    colonnes = ["aire", "evol_cadres_pts", "ival_moy_5km", "dist_centre_km", "log_densite"]
    resultat = population.set_index("code_commune")[colonnes].copy()
    resultat["avec_ival"] = resultat["ival_moy_5km"].notna()
    nombre = comptes[f"n_lyc_ival_{rayon}km"].reindex(resultat.index)
    assert (nombre[resultat["avec_ival"]] >= 1).all(), "Commune avec IVAL sans lycée à IVAL."
    # Le logarithme n'est pris que là où il y a au moins un lycée à IVAL : la population estimée
    resultat["log_n_lyc_ival_5km"] = np.log(nombre.where(resultat["avec_ival"]))
    resultat["anneau"] = analyse.anneau(resultat["dist_centre_km"])
    resultat["grappe"] = grappes.reindex(resultat.index)
    assert resultat["grappe"].notna().all(), "Commune sans lycée avec IVAL le plus proche."

    estimees = resultat[resultat["avec_ival"]]
    for colonne, reduite in (
        ("ival_moy_5km", "ival_reduite"),
        ("log_n_lyc_ival_5km", "log_n_reduit"),
    ):
        par_aire = estimees.groupby("aire")[colonne]
        moyenne = resultat["aire"].map(par_aire.mean())
        ecart_type = resultat["aire"].map(par_aire.std())
        resultat[reduite] = (resultat[colonne] - moyenne) / ecart_type
    return resultat


def _tirages_grappes(communes_h3: pd.DataFrame) -> list[pd.Series]:
    """Renvoie les poids des communes dans chaque tirage du bootstrap par grappes de H3 (A16).

    Dans chaque aire, les grappes de `communes_h3` sont tirées avec remise, autant que l'aire en
    compte ; une commune pèse le nombre de fois que sa grappe est tirée. La graine est remise à
    chaque appel : deux appels sur les mêmes communes voient les mêmes tirages.
    """
    generateur = np.random.default_rng(config.GRAINE_BOOTSTRAP)
    tirages = []
    for _ in range(config.NB_TIRAGES_BOOTSTRAP):
        poids = []
        for _aire, communes in communes_h3.groupby("aire"):
            grappes = communes["grappe"].unique()
            tirees = generateur.choice(grappes, size=len(grappes), replace=True)
            poids.append(communes["grappe"].map(pd.Series(tirees).value_counts()).fillna(0))
        tirages.append(pd.concat(poids))
    return tirages


def _coefficients_h3(echantillon: pd.DataFrame, poids: pd.Series) -> np.ndarray | None:
    """Renvoie β_q et β_n de la régression de H3, ou None si les régresseurs sont colinéaires.

    Moindres carrés pondérés par `poids` (1 sans bootstrap) de `evol_cadres_pts` sur
    `ival_reduite`, `log_n_reduit`, `dist_centre_km`, `log_densite` et un effet fixe par
    aire × anneau, sans constante (les effets fixes en tiennent lieu). Seules les cellules
    présentes dans le tirage ont un effet fixe (A16).
    """
    gardees = echantillon[poids.loc[echantillon.index] > 0]
    cellule = gardees["aire"] + " " + gardees["anneau"].astype(str)
    effets_fixes = pd.get_dummies(cellule, dtype=float).to_numpy()
    regresseurs = gardees[["ival_reduite", "log_n_reduit", "dist_centre_km", "log_densite"]]
    x = np.column_stack([regresseurs.to_numpy(dtype=float), effets_fixes])
    y = gardees["evol_cadres_pts"].to_numpy(dtype=float)
    racine = np.sqrt(poids.loc[gardees.index].to_numpy(dtype=float))
    coefficients, _, rang, _ = np.linalg.lstsq(x * racine[:, None], y * racine, rcond=None)
    if rang < x.shape[1]:
        return None
    return coefficients[:2]


def estimation_h3(population: pd.DataFrame) -> pd.DataFrame:
    """Renvoie β_q, β_n et β_q − β_n de H3 avec leurs intervalles (§5.5, A16).

    `population` vient de `population_h3`. Estimation sur les communes avec IVAL, les 3 aires
    ensemble puis chaque aire (descriptif), sur les mêmes tirages des grappes de ces communes
    (`_tirages_grappes`), sans refaire la standardisation. Un tirage de rang incomplet
    est écarté et compté (`tirages_ecartes`) ; au-delà de `config.MAX_TIRAGES_ECARTES`,
    l'intervalle n'est pas rapporté. En points de part de cadres pour un écart-type. Index
    (`portee`, `coefficient`) ; colonnes `estimation`, `ic_bas`, `ic_haut`, `n_communes`,
    `n_grappes`, `tirages_ecartes`.
    """
    estimees = population[population["avec_ival"]]
    tirages = _tirages_grappes(estimees)
    portees = {"ensemble": estimees}
    for aire, communes_aire in estimees.groupby("aire"):
        portees[aire] = communes_aire
    lignes = []
    for portee, echantillon in portees.items():
        point = _coefficients_h3(echantillon, pd.Series(1.0, index=echantillon.index))
        assert point is not None, f"Régresseurs colinéaires dans l'estimation de H3 ({portee})."
        tires = [_coefficients_h3(echantillon, poids) for poids in tirages]
        valides = np.array([coefficients for coefficients in tires if coefficients is not None])
        ecartes = len(tires) - len(valides)
        estimations = {
            "β_q": (point[0], valides[:, 0]),
            "β_n": (point[1], valides[:, 1]),
            "β_q − β_n": (point[0] - point[1], valides[:, 0] - valides[:, 1]),
        }
        rapporte = ecartes <= config.MAX_TIRAGES_ECARTES
        for coefficient, (valeur, distribution) in estimations.items():
            lignes.append(
                {
                    "portee": portee,
                    "coefficient": coefficient,
                    "estimation": valeur,
                    "ic_bas": np.percentile(distribution, 2.5) if rapporte else np.nan,
                    "ic_haut": np.percentile(distribution, 97.5) if rapporte else np.nan,
                    "n_communes": len(echantillon),
                    "n_grappes": echantillon["grappe"].nunique(),
                    "tirages_ecartes": ecartes,
                }
            )
    return pd.DataFrame(lignes).set_index(["portee", "coefficient"])


def verdict_h3(estimation: pd.DataFrame, fiabilite: float) -> pd.DataFrame:
    """Renvoie le verdict de H3, toutes aires ensemble, par les règles du §5.5 (A1, A7, A16).

    `estimation` vient de `estimation_h3`, `fiabilite` est la valeur après Spearman-Brown de la
    ligne « ensemble » de `fiabilite_ival`. Première règle vérifiée, dans l'ordre du plan. Une
    ligne, `ensemble`, avec `verdict` et `fiabilite`, pour s'afficher comme `verdict_h1`.
    """
    ensemble = estimation.loc["ensemble"]
    qualite, ecart = ensemble.loc["β_q"], ensemble.loc["β_q − β_n"]
    if fiabilite < config.SEUIL_FIABILITE_IVAL:
        verdict = "non testable avec cette mesure"
    elif ensemble["ic_bas"].isna().any():
        # Trop de tirages écartés : l'intervalle n'est pas rapporté
        verdict = "non concluante"
    elif qualite["ic_haut"] < 0 or ecart["ic_haut"] < 0:
        verdict = "infirmée"
    elif qualite["ic_bas"] > 0 and ecart["ic_bas"] > 0:
        verdict = "confirmée"
    elif qualite["ic_bas"] > 0:
        verdict = "nuancée"
    else:
        verdict = "non concluante"
    return pd.DataFrame({"verdict": [verdict], "fiabilite": [fiabilite]}, index=["ensemble"])


def terciles_h3(population: pd.DataFrame) -> pd.DataFrame:
    """Renvoie la moyenne de `evol_cadres_pts` par tiers d'IVAL de chaque aire (`fig_h3`, §5.5).

    Tiers de `ival_moy_5km` calculés dans chaque aire sur les communes avec IVAL, plus la
    catégorie « sans IVAL ». Moyennes simples, intervalles à 95 % par `_tirages_grappes` sur
    toute la population : la catégorie « sans IVAL » a besoin des grappes de ses communes, que
    l'estimation ne tire pas. Un tirage sans aucune commune de la catégorie est écarté pour elle
    et compté (`tirages_ecartes`). Elles décrivent : le verdict se lit sur β_q et β_n. Index
    (`aire`, `categorie`) ; colonnes `moyenne`, `ic_bas`, `ic_haut`, `n_communes`,
    `tirages_ecartes`.
    """
    communes = population.copy()
    tiers = (
        communes[communes["avec_ival"]]
        .groupby("aire")["ival_moy_5km"]
        .transform(lambda ival: pd.qcut(ival, 3, labels=config.CATEGORIES_TIERS_IVAL[:3]))
    )
    communes["categorie"] = (
        tiers.astype(str).reindex(communes.index).fillna(config.CATEGORIES_TIERS_IVAL[3])
    )
    tirages = _tirages_grappes(population)
    lignes = []
    for (aire, categorie), groupe in communes.groupby(["aire", "categorie"]):
        moyennes = [
            np.average(groupe["evol_cadres_pts"], weights=poids.loc[groupe.index])
            for poids in tirages
            if poids.loc[groupe.index].sum() > 0
        ]
        ecartes = len(tirages) - len(moyennes)
        lignes.append(
            {
                "aire": aire,
                "categorie": categorie,
                "moyenne": groupe["evol_cadres_pts"].mean(),
                "ic_bas": np.percentile(moyennes, 2.5),
                "ic_haut": np.percentile(moyennes, 97.5),
                "n_communes": len(groupe),
                "tirages_ecartes": ecartes,
            }
        )
    return pd.DataFrame(lignes).set_index(["aire", "categorie"])
