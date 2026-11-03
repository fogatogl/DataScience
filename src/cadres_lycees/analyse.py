"""Statistiques descriptives et comparaisons sur la base communale et les lycées."""

import itertools

import geopandas as gpd
import numpy as np
import pandas as pd

from cadres_lycees import accessibilite, config, nettoyage


def profil_aires(lycees: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie une ligne par aire : lycées, part de privé sous contrat et IPS moyen par secteur.

    `part_prive` compte les lycées ; `part_prive_candidats` pondère chaque lycée par ses candidats
    au bac (`poids_ival`, moyenne des présents au bac général et technologique 2012-2022), sur
    les `n_avec_candidats` lycées qui ont une IVAL : plus proche d'une part d'élèves, sans en être
    une au sens de la DEPP. L'IPS moyen est une moyenne simple des lycées qui ont un IPS, car la
    source ne donne pas d'effectifs. `ecart_ips` est l'IPS moyen du privé moins celui du public,
    en points d'IPS ; `n_ips_public` et `n_ips_prive` sont les nombres de lycées sur lesquels
    reposent ces moyennes. Seuls les lycées situés dans les communes de l'aire comptent ; une
    aire sans lycée privé, sans IPS dans un secteur ou sans IVAL dans un secteur fait échouer.
    """
    lycees = lycees[lycees["aire"].notna()]
    prives = lycees[lycees["secteur"] == "prive"]
    profil = pd.DataFrame(
        {
            "n_lycees": lycees.groupby("aire").size(),
            "n_prive": prives.groupby("aire").size(),
        }
    )
    profil["part_prive"] = profil["n_prive"] / profil["n_lycees"]

    avec_candidats = lycees[lycees["poids_ival"].notna()]
    par_secteur = avec_candidats.groupby(["aire", "secteur"])["poids_ival"].sum()
    candidats_par_secteur = par_secteur.unstack("secteur")
    profil["part_prive_candidats"] = candidats_par_secteur["prive"] / (
        candidats_par_secteur["prive"] + candidats_par_secteur["public"]
    )
    profil["n_avec_candidats"] = avec_candidats.groupby("aire").size()

    ips = lycees.groupby(["aire", "secteur"])["ips"].agg(["mean", "count"]).unstack("secteur")
    profil["ips_public"] = ips[("mean", "public")]
    profil["ips_prive"] = ips[("mean", "prive")]
    profil["ecart_ips"] = profil["ips_prive"] - profil["ips_public"]
    profil["n_ips_public"] = ips[("count", "public")]
    profil["n_ips_prive"] = ips[("count", "prive")]

    colonnes = ["n_prive", "part_prive_candidats", "ips_public", "ips_prive"]
    manquants = profil[colonnes].isna().any(axis=1)
    assert not manquants.any(), (
        f"Pas de lycée privé, d'IVAL ou d'IPS dans un secteur : {profil.index[manquants].tolist()}."
    )
    return profil


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

    population_h3 = communes[communes[f"n_lyc_{rayon}km"] > 0]
    par_commune = population_h3[["aire"]].copy()
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
        h3 = population_h3 if nom == "ensemble" else population_h3[population_h3["aire"] == nom]
        lignes[nom] = {
            "r": r,
            # La formule suppose une fiabilité positive : pour r < 0, elle n'a pas de sens
            "r_spearman_brown": 2 * r / (1 + r) if r >= 0 else float("nan"),
            "n_communes_h3": len(h3),
            "n_communes": len(groupe),
            "n_lycees": proches.loc[groupe.index, "uai"].nunique(),
        }
    return pd.DataFrame.from_dict(lignes, orient="index")


def _distances_groupes(
    communes_aire: pd.DataFrame, colonne_exposition: str, bas: float, haut: float
) -> tuple[pd.Series, pd.Series]:
    """Renvoie les distances au centre des communes exposées, puis non exposées, de [bas, haut)."""
    dans_la_cellule = communes_aire["dist_centre_km"].between(bas, haut, inclusive="left")
    cellule = communes_aire[dans_la_cellule]
    exposee = cellule[colonne_exposition] == 1
    return cellule.loc[exposee, "dist_centre_km"], cellule.loc[~exposee, "dist_centre_km"]


def cellules_anneaux(communes: pd.DataFrame, rayon: int) -> pd.DataFrame:
    """Renvoie, aire par aire, les cellules d'anneaux de distance au centre après fusion (§5.2).

    Règles fixées par A6 avant tout calcul. Une cellule remplit la condition si les communes
    exposées (`expose_lyc_prive_<rayon>km` vaut 1) et les non exposées sont chacune au moins
    `config.EFFECTIF_MIN_GROUPE`. Tant qu'une cellule échoue, la plus proche du centre est
    fusionnée avec sa voisine qui compte le moins de communes, la plus proche du centre à
    égalité ; un anneau vide reste une cellule et peut donc être absorbé. Une cellule qui remplit
    la condition n'est estimable que si `ecart_dist_km`, l'écart des distances moyennes au
    centre des deux groupes, vaut au plus `config.ECART_DIST_MAX_KM`, sans nouvelle fusion. Une
    aire dont la dernière cellule échoue est non estimable : une seule ligne, `estimable` faux.
    Les anneaux vont de leur borne basse, incluse, à leur borne haute, exclue.
    """
    colonne_exposition = f"expose_lyc_prive_{rayon}km"
    assert communes[colonne_exposition].isin([0, 1]).all(), (
        f"{colonne_exposition} doit valoir 0 ou 1."
    )
    assert (communes["dist_centre_km"] >= 0).all(), "Distance au centre manquante ou négative."
    bornes = [*config.ANNEAUX_KM, float("inf")]

    lignes = []
    for aire, communes_aire in communes.groupby("aire"):
        # Une cellule est une suite d'anneaux contigus : ses bornes suffisent à la décrire
        cellules = list(itertools.pairwise(bornes))
        while True:
            groupes = [
                _distances_groupes(communes_aire, colonne_exposition, bas, haut)
                for bas, haut in cellules
            ]
            remplies = [
                min(len(dist_exposees), len(dist_non_exposees)) >= config.EFFECTIF_MIN_GROUPE
                for dist_exposees, dist_non_exposees in groupes
            ]
            if all(remplies) or len(cellules) == 1:
                break
            rang = remplies.index(False)
            voisines = [voisine for voisine in (rang - 1, rang + 1) if 0 <= voisine < len(cellules)]
            nb_communes = [
                len(dist_exposees) + len(dist_non_exposees)
                for dist_exposees, dist_non_exposees in groupes
            ]
            # La voisine qui compte le moins de communes ; à égalité, le plus petit rang, donc
            # la plus proche du centre
            voisine = min(voisines, key=lambda candidate: (nb_communes[candidate], candidate))
            interieure, exterieure = sorted((rang, voisine))
            cellules[interieure] = (cellules[interieure][0], cellules[exterieure][1])
            del cellules[exterieure]

        for (bas, haut), (dist_exposees, dist_non_exposees), remplie in zip(
            cellules, groupes, remplies, strict=True
        ):
            ecart = abs(dist_exposees.mean() - dist_non_exposees.mean())
            lignes.append(
                {
                    "aire": aire,
                    "bas_km": bas,
                    "haut_km": haut,
                    "n_exposees": len(dist_exposees),
                    "n_non_exposees": len(dist_non_exposees),
                    "dist_moy_exposees": dist_exposees.mean(),
                    "dist_moy_non_exposees": dist_non_exposees.mean(),
                    "ecart_dist_km": ecart,
                    # Une cellule en échec n'est jamais estimable, même équilibrée
                    "estimable": bool(remplie and ecart <= config.ECART_DIST_MAX_KM),
                }
            )
    return pd.DataFrame(lignes)


def tableau_support(
    base: gpd.GeoDataFrame, paires: pd.DataFrame, cellules: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie le support de l'exposition, une ligne par aire et par rayon (§2.2 e, §5.2).

    `base` et `paires` viennent de `pipeline.ecrire_tableau_support` : base sans la part de
    cadres, paires sur `config.VARIABLES_PAIRES_SANS_CADRES` (A3) ; `cellules` vient de
    `cellules_anneaux`, avec une colonne `rayon_km`, pour chaque rayon de
    `config.RAYONS_SUPPORT_KM`. Colonnes : `communes`, `exposees` et `part_exposees` (au moins un
    lycée privé sous contrat dans le rayon), `cellules_estimables`, `paires_statut_different`
    (l'exposition 0/1 diffère entre les deux voisines) et `correlation_non_centree` entre
    `d_dist_lyc_prive_min` et `d_dist_centre_km` dans les paires : sans centrage, elle ne
    dépend pas du sens i − j, qui suit l'ordre des codes (A6).
    """
    x, y = paires["d_dist_lyc_prive_min"], paires["d_dist_centre_km"]
    produits = pd.DataFrame({"xy": x * y, "xx": x**2, "yy": y**2, "aire": paires["aire"]})
    sommes = produits.groupby("aire").sum()
    correlation = sommes["xy"] / (sommes["xx"] * sommes["yy"]) ** 0.5

    lignes = []
    for rayon in config.RAYONS_SUPPORT_KM:
        colonne_exposition = f"expose_lyc_prive_{rayon}km"
        par_aire = base.groupby("aire")[colonne_exposition]
        cellules_rayon = cellules[cellules["rayon_km"] == rayon]
        estimables = cellules_rayon.groupby("aire")["estimable"].sum()
        statut_different = paires[f"d_{colonne_exposition}"] != 0
        support = pd.DataFrame(
            {
                "communes": par_aire.size(),
                "exposees": par_aire.sum(),
                "part_exposees": par_aire.mean(),
                "cellules_estimables": estimables,
                "paires_statut_different": statut_different.groupby(paires["aire"]).sum(),
                "correlation_non_centree": correlation,
            }
        )
        support.insert(0, "rayon_km", rayon)
        lignes.append(support)
    resultat = pd.concat(lignes).rename_axis("aire").reset_index()
    # Une aire sans cellule à un rayon ou sans paire aurait des valeurs manquantes
    manquantes = resultat.columns[resultat.isna().any()].tolist()
    assert not manquantes, f"Valeurs manquantes dans le tableau de support : {manquantes}."
    return resultat


def pente_paires(paires: pd.DataFrame, acces: str, poids: pd.Series | None = None) -> float:
    """Renvoie la pente de `d_part_cadres_2022` sur l'écart d'accès `acces` dans les paires (§5.3).

    Moindres carrés sans constante, avec les écarts de `config.CONTROLES_PAIRES` en contrôle. Le
    sens i − j suit l'ordre des codes : changer le signe de toutes les colonnes d'une paire ne
    change pas cette pente, alors qu'une constante en dépendrait (A6). `poids`, aligné sur
    `paires`, pondère les paires (bootstrap) ; sans poids, chaque paire compte une fois.
    """
    colonnes = [acces, *config.CONTROLES_PAIRES]
    x = paires[colonnes].to_numpy(dtype=float)
    y = paires["d_part_cadres_2022"].to_numpy(dtype=float)
    assert not (np.isnan(x).any() or np.isnan(y).any()), "Écart manquant dans les paires."
    if poids is None:
        poids_paires = np.ones(len(paires))
    else:
        # `.loc` échoue si une paire n'a pas de poids, là où `reindex` mettrait une valeur manquante
        poids_paires = poids.loc[paires.index].to_numpy(dtype=float)
    assert (poids_paires >= 0).all(), "Poids de paire négatif ou manquant."
    # Σ w(y − xb)² = Σ (√w·y − √w·xb)² : les moindres carrés ordinaires sur les lignes
    # multipliées par √w sont les moindres carrés pondérés, et un poids entier k revient à
    # compter la paire k fois
    racine = np.sqrt(poids_paires)
    coefficients, _, rang, _ = np.linalg.lstsq(x * racine[:, None], y * racine, rcond=None)
    # lstsq rend une solution même si des régresseurs sont colinéaires : on l'interdit
    assert rang == len(colonnes), f"Régresseurs colinéaires dans les paires (rang {rang})."
    return float(coefficients[0])


def poids_bootstrap(paires: pd.DataFrame, tirage: pd.Series) -> pd.Series:
    """Renvoie le poids de chaque paire dans un tirage du bootstrap par commune (§5.3).

    `tirage` donne, par code commune, le nombre de fois que la commune est tirée. Une même commune
    est dans plusieurs paires, qui ne sont donc pas indépendantes : on tire les communes, et une
    paire compte autant de fois que le produit des tirages de ses deux communes.
    """
    tirage_i = paires["code_commune_i"].map(tirage)
    tirage_j = paires["code_commune_j"].map(tirage)
    assert tirage_i.notna().all() and tirage_j.notna().all(), (
        "Communes des paires absentes du tirage."
    )
    return tirage_i * tirage_j


def pentes_paires_par_aire(paires: pd.DataFrame, acces: str) -> pd.DataFrame:
    """Renvoie, aire par aire, la pente des paires et son intervalle à 95 % (§5.3).

    `paires` vient de `pipeline.construire_base`. Intervalle : percentiles 2,5 et 97,5 des pentes
    de `config.NB_TIRAGES_BOOTSTRAP` tirages avec remise des communes de l'aire (voir
    `poids_bootstrap`). La graine `config.GRAINE_BOOTSTRAP` est remise à chaque appel : le
    résultat est reproductible, et deux appels sur les mêmes paires (principale et secondaire,
    lycées et autres équipements pour H4) voient les mêmes tirages. Les tirages d'une aire
    dépendent des aires traitées avant elle. Colonnes : `pente`, `ic_bas`, `ic_haut`, `n_paires`,
    `n_communes` ; index : l'aire.
    """
    generateur = np.random.default_rng(config.GRAINE_BOOTSTRAP)
    lignes = {}
    for aire, paires_aire in paires.groupby("aire"):
        communes = pd.unique(
            pd.concat([paires_aire["code_commune_i"], paires_aire["code_commune_j"]])
        )
        pentes = []
        for _ in range(config.NB_TIRAGES_BOOTSTRAP):
            tirees = generateur.choice(communes, size=len(communes), replace=True)
            tirage = pd.Series(tirees).value_counts().reindex(communes, fill_value=0)
            pentes.append(pente_paires(paires_aire, acces, poids_bootstrap(paires_aire, tirage)))
        lignes[aire] = {
            "pente": pente_paires(paires_aire, acces),
            "ic_bas": np.percentile(pentes, 2.5),
            "ic_haut": np.percentile(pentes, 97.5),
            "n_paires": len(paires_aire),
            "n_communes": len(communes),
        }
    return pd.DataFrame.from_dict(lignes, orient="index").rename_axis("aire")


def nuage_paires(paires: pd.DataFrame, acces: str) -> pd.DataFrame:
    """Renvoie le nuage par classes des paires d'une aire, à contrôles donnés (Fig. 5, §5.3).

    On retire à `d_part_cadres_2022` et à l'écart d'accès `acces` leur partie expliquée par les
    écarts de `config.CONTROLES_PAIRES` (régressions sans constante, comme `pente_paires`). Par
    le théorème de Frisch-Waugh-Lovell, la pente des résidus de l'un sur les résidus de l'autre
    est exactement celle de `pente_paires` : les points et la droite de la figure disent la même
    chose. Les paires sont symétrisées (chaque paire dans les deux sens, A6), ce qui centre le
    nuage sur zéro sans changer la pente, puis réparties en `config.NB_CLASSES_FIG5` classes
    d'effectifs égaux de l'écart d'accès résiduel. Une ligne par classe : `acces_residuel` et
    `cadres_residuel` (moyennes de la classe ; fraction pour les cadres) et `n_paires`.
    """
    controles = paires[list(config.CONTROLES_PAIRES)].to_numpy(dtype=float)
    residus = {}
    for nom, colonne in (("acces_residuel", acces), ("cadres_residuel", "d_part_cadres_2022")):
        y = paires[colonne].to_numpy(dtype=float)
        coefficients, _, rang, _ = np.linalg.lstsq(controles, y, rcond=None)
        assert rang == controles.shape[1], f"Contrôles colinéaires dans les paires (rang {rang})."
        residus[nom] = y - controles @ coefficients
    residus = pd.DataFrame(residus)
    assert residus.notna().all().all(), "Écart manquant dans les paires."
    symetrisees = pd.concat([residus, -residus], ignore_index=True)
    classe = pd.qcut(symetrisees["acces_residuel"], config.NB_CLASSES_FIG5, labels=False)
    return (
        symetrisees.groupby(classe)
        .agg(
            acces_residuel=("acces_residuel", "mean"),
            cadres_residuel=("cadres_residuel", "mean"),
            n_paires=("acces_residuel", "size"),
        )
        .rename_axis("classe")
    )


def pentes_h4(base: pd.DataFrame, paires: pd.DataFrame) -> pd.DataFrame:
    """Renvoie, pour chaque mesure d'accès de H4 et chaque aire, la pente des paires (§5.7).

    Chaque mesure de `config.MESURES_H4` est centrée réduite dans chaque aire (moyenne et
    écart-type simples des communes de `base`), puis orientée par son sens : la pente se lit en
    points de part de cadres pour un écart-type d'accès en plus. Dans une paire, la moyenne
    s'annule : seul l'écart-type compte. Pente, contrôles et intervalle sont ceux de
    `pentes_paires_par_aire` (sans constante, bootstrap par commune), avec les mêmes tirages pour
    toutes les mesures. Index (`mesure`, `aire`) ; colonnes de `pentes_paires_par_aire`.
    """
    resultats = []
    for mesure, (variable, sens) in config.MESURES_H4.items():
        ecart_type = base.groupby("aire")[variable].std()
        assert (ecart_type > 0).all(), f"{variable} ne varie pas dans une aire."
        colonne = f"d_{variable}_reduit"
        reduites = paires.assign(
            **{colonne: sens * paires[f"d_{variable}"] / paires["aire"].map(ecart_type)}
        )
        pentes = pentes_paires_par_aire(reduites, colonne)
        resultats.append(pentes.assign(mesure=mesure).set_index("mesure", append=True))
    return pd.concat(resultats).reorder_levels(["mesure", "aire"])


def resume_acces(base: pd.DataFrame) -> pd.DataFrame:
    """Résume, aire par aire, l'accès des communes aux lycées et aux autres infrastructures.

    Tableau descriptif, sans donnée sur les cadres (sections 2.3 et 5 du rapport) : nombre de
    communes, part des communes exposées (au moins un lycée privé sous contrat au rayon principal)
    et médiane de chaque mesure d'accès. Médianes simples des communes : les distances et les
    comptes sont très asymétriques.
    """
    rayon = config.RAYON_PRINCIPAL_KM
    mesures = [
        "dist_lyc_prive_min",
        "dist_lyc_public_min",
        "dist_gare_min",
        "apl_mg",
        f"n_sport_{rayon}km",
        f"n_culture_{rayon}km",
    ]
    par_aire = base.groupby("aire")
    effectifs = par_aire.agg(
        communes=("code_commune", "size"),
        part_exposees=(f"expose_lyc_prive_{rayon}km", "mean"),
    )
    return effectifs.join(par_aire[mesures].median())


def ecart_cellule(cellule: pd.DataFrame, colonne_exposition: str, poids: pd.Series) -> float:
    """Renvoie l'écart de part de cadres entre communes exposées et non exposées d'une cellule.

    Coefficient de `colonne_exposition` (0/1) dans la régression de `part_cadres_2022` sur
    l'exposition, `dist_centre_km` et `log_densite` avec constante, pondérée par `poids` (§5.2,
    A6). Dans une cellule, la constante est sans danger : il n'y a pas de sens i − j.
    """
    colonnes = [colonne_exposition, "dist_centre_km", "log_densite"]
    x = np.column_stack([np.ones(len(cellule)), cellule[colonnes].to_numpy(dtype=float)])
    y = cellule["part_cadres_2022"].to_numpy(dtype=float)
    w = poids.loc[cellule.index].to_numpy(dtype=float)
    assert not (np.isnan(x).any() or np.isnan(y).any()), "Valeur manquante dans la cellule."
    # Moindres carrés pondérés par les lignes multipliées par √w, comme dans `pente_paires`
    racine = np.sqrt(w)
    coefficients, _, rang, _ = np.linalg.lstsq(x * racine[:, None], y * racine, rcond=None)
    assert rang == x.shape[1], f"Régresseurs colinéaires dans la cellule (rang {rang})."
    return float(coefficients[1])


def ecarts_anneaux(base: pd.DataFrame) -> pd.DataFrame:
    """Renvoie l'écart avec/sans lycée privé de chaque cellule d'anneaux, à 5 et 10 km (§5.2).

    Cellules de `cellules_anneaux`, les mêmes que celles du tableau de support. Dans chaque
    cellule estimable : `ecart`, l'écart à contrôles donnés pondéré par `actifs_2022`
    (`ecart_cellule`), son intervalle à 95 % (`ic_bas`, `ic_haut`) par `config.
    NB_TIRAGES_BOOTSTRAP` tirages avec remise des communes dans chacun des deux groupes, et
    `ecart_brut`, l'écart des parts moyennes pondérées. Une commune sans actif en 2022 (A17)
    compte dans la cellule mais n'a pas de part : elle sort de l'estimation (`n_sans_part`). Les
    écarts sont en fraction ; une cellule non estimable a des valeurs manquantes.
    """
    generateur = np.random.default_rng(config.GRAINE_BOOTSTRAP)
    lignes = []
    for rayon in config.RAYONS_SUPPORT_KM:
        colonne_exposition = f"expose_lyc_prive_{rayon}km"
        cellules = cellules_anneaux(base, rayon)
        for cellule in cellules.itertuples(index=False):
            ligne = {"rayon_km": rayon, **cellule._asdict()}
            dans_la_cellule = (base["aire"] == cellule.aire) & base["dist_centre_km"].between(
                cellule.bas_km, cellule.haut_km, inclusive="left"
            )
            communes = base[dans_la_cellule]
            ligne["n_sans_part"] = int(communes["part_cadres_2022"].isna().sum())
            if cellule.estimable:
                avec_part = communes[communes["part_cadres_2022"].notna()]
                exposee = avec_part[colonne_exposition] == 1
                actifs = avec_part["actifs_2022"]
                ecarts = []
                for _ in range(config.NB_TIRAGES_BOOTSTRAP):
                    # Tirage dans chaque groupe : les deux effectifs restent ceux de la cellule
                    tirees = np.concatenate(
                        [
                            generateur.choice(groupe.index, size=len(groupe), replace=True)
                            for groupe in (avec_part[exposee], avec_part[~exposee])
                        ]
                    )
                    tirage = pd.Series(tirees).value_counts().reindex(avec_part.index, fill_value=0)
                    ecarts.append(ecart_cellule(avec_part, colonne_exposition, actifs * tirage))
                parts_moyennes = [
                    np.average(groupe["part_cadres_2022"], weights=groupe["actifs_2022"])
                    for groupe in (avec_part[exposee], avec_part[~exposee])
                ]
                ligne |= {
                    "ecart": ecart_cellule(avec_part, colonne_exposition, actifs),
                    "ic_bas": np.percentile(ecarts, 2.5),
                    "ic_haut": np.percentile(ecarts, 97.5),
                    "ecart_brut": parts_moyennes[0] - parts_moyennes[1],
                }
            lignes.append(ligne)
    return pd.DataFrame(lignes)


def _concordent(a: pd.Series, b: pd.Series) -> bool:
    """Dit si deux estimations concordent : même signe et intervalles qui se recoupent (§5.3)."""
    meme_signe = np.sign(a["ecart"]) == np.sign(b["ecart"])
    return bool(meme_signe and a["ic_bas"] <= b["ic_haut"] and b["ic_bas"] <= a["ic_haut"])


def verdict_h1(
    principale: pd.DataFrame, secondaire: pd.DataFrame, anneaux: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie le verdict de H1 dans chaque aire, par les règles du §5.3 (A4, A13).

    `principale` et `secondaire` viennent de `pentes_paires_par_aire` sur `d_dist_lyc_prive_min`
    et `d_n_lyc_prive_5km`, `anneaux` de `ecarts_anneaux`. Sens de H1 : pente principale
    négative (plus proche d'un lycée privé, plus de cadres), pente secondaire et écarts des
    cellules positifs. Un anneau comparé est un anneau d'origine couvert par une cellule
    estimable à chacun des deux rayons ; ses deux estimations doivent concorder. Toute cellule
    estimable peut contredire : son intervalle sous zéro fait d'une confirmation une nuance, au
    dessus de zéro il empêche d'établir un résultat nul. Colonnes : `verdict`, `mention`
    (« paires seules » pour une confirmation sans anneau comparé), `anneaux_compares`.
    """
    anneaux_origine = list(itertools.pairwise([*config.ANNEAUX_KM, float("inf")]))
    lignes = {}
    for aire in principale.index:
        pente = principale.loc[aire]
        cellules = anneaux[(anneaux["aire"] == aire) & anneaux["estimable"]]
        contredit = bool((cellules["ic_haut"] < 0).any())
        dans_le_sens = bool((cellules["ic_bas"] > 0).any())
        compares = 0
        concordants = True
        for bas, haut in anneaux_origine:
            couvrantes = cellules[(cellules["bas_km"] <= bas) & (cellules["haut_km"] >= haut)]
            par_rayon = [couvrantes[couvrantes["rayon_km"] == r] for r in config.RAYONS_SUPPORT_KM]
            if all(len(c) == 1 for c in par_rayon):
                compares += 1
                concordants &= _concordent(par_rayon[0].iloc[0], par_rayon[1].iloc[0])

        if pente["ic_haut"] < 0:
            confirmee = secondaire.loc[aire, "pente"] > 0 and concordants and not contredit
            verdict = "confirmée" if confirmee else "nuancée"
        elif pente["ic_bas"] > 0:
            verdict = "infirmée"
        elif compares > 0 and concordants and not dans_le_sens:
            # Résultat nul établi
            verdict = "infirmée"
        else:
            verdict = "non concluante"
        mention = "paires seules" if verdict == "confirmée" and compares == 0 else ""
        lignes[aire] = {"verdict": verdict, "mention": mention, "anneaux_compares": compares}
    return pd.DataFrame.from_dict(lignes, orient="index").rename_axis("aire")
