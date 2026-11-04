"""H1 : comparaison par anneaux, pentes des paires contiguës et verdict ; pentes de H4.

H4 reprend l'estimateur des paires de H1, appliqué aux autres infrastructures.
"""

import itertools

import numpy as np
import pandas as pd

from cadres_lycees import config


def _distances_groupes(
    communes_aire: pd.DataFrame, colonne_exposition: str, bas: float, haut: float
) -> tuple[pd.Series, pd.Series]:
    """Renvoie les distances au centre des communes exposées, puis non exposées, de [bas, haut)."""
    dans_la_cellule = communes_aire["dist_centre_km"].between(bas, haut, inclusive="left")
    cellule = communes_aire[dans_la_cellule]
    exposee = cellule[colonne_exposition] == 1
    return cellule.loc[exposee, "dist_centre_km"], cellule.loc[~exposee, "dist_centre_km"]


def cellules_anneaux(communes: pd.DataFrame, rayon: int) -> pd.DataFrame:
    """Renvoie, aire par aire, les cellules d'anneaux de distance au centre après fusion.

    Une cellule remplit la condition si les communes
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


def pente_paires(
    paires: pd.DataFrame,
    acces: str,
    poids: pd.Series | None = None,
    controles: tuple[str, ...] = config.CONTROLES_PAIRES,
) -> float | None:
    """Renvoie la pente de `d_part_cadres_2022` sur l'écart d'accès `acces` dans les paires.

    Moindres carrés sans constante, avec les écarts de `controles` en contrôle (ceux de
    `config.CONTROLES_PAIRES` par défaut ; la robustesse « sans contrôle de densité » retire
    `d_log_densite`). Le sens i − j suit l'ordre des codes : changer le signe de toutes les colonnes
    d'une paire ne change pas cette pente, alors qu'une constante en dépendrait. `poids`, aligné sur
    `paires`, pondère les paires (bootstrap) ; sans poids, chaque paire compte une fois. Renvoie
    None si les régresseurs sont colinéaires : un tirage du bootstrap peut ne garder aucune paire où
    l'accès diffère.
    """
    colonnes = [acces, *controles]
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
    # lstsq rend une solution même si des régresseurs sont colinéaires : elle n'aurait pas de sens
    if rang < len(colonnes):
        return None
    return float(coefficients[0])


def poids_bootstrap(paires: pd.DataFrame, tirage: pd.Series) -> pd.Series:
    """Renvoie le poids de chaque paire dans un tirage du bootstrap par commune.

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


def pentes_paires_par_aire(
    paires: pd.DataFrame, acces: str, controles: tuple[str, ...] = config.CONTROLES_PAIRES
) -> pd.DataFrame:
    """Renvoie, aire par aire, la pente des paires et son intervalle à 95 %.

    `paires` vient de `pipeline.construire_base` ; `controles` est passé à `pente_paires`.
    Intervalle : percentiles 2,5 et 97,5 des pentes de `config.NB_TIRAGES_BOOTSTRAP` tirages
    avec remise des communes de l'aire (voir `poids_bootstrap`). La graine
    `config.GRAINE_BOOTSTRAP` est remise à chaque appel : le résultat est reproductible, et deux
    appels sur les mêmes paires (principale et secondaire, lycées et autres équipements pour H4)
    voient les mêmes tirages. Les tirages d'une aire dépendent des aires traitées avant elle.
    Un tirage de régresseurs colinéaires est écarté et compté, comme pour H3 ; au-delà de
    `config.MAX_TIRAGES_ECARTES`, l'intervalle n'est pas rapporté. Colonnes : `pente`, `ic_bas`,
    `ic_haut`, `n_paires`, `n_communes`, `tirages_ecartes` ; index : l'aire.
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
            poids = poids_bootstrap(paires_aire, tirage)
            pentes.append(pente_paires(paires_aire, acces, poids, controles))
        pente = pente_paires(paires_aire, acces, controles=controles)
        assert pente is not None, f"Régresseurs colinéaires dans les paires de {aire}."
        valides = [pente_tiree for pente_tiree in pentes if pente_tiree is not None]
        ecartes = len(pentes) - len(valides)
        rapporte = ecartes <= config.MAX_TIRAGES_ECARTES
        lignes[aire] = {
            "pente": pente,
            "ic_bas": np.percentile(valides, 2.5) if rapporte else np.nan,
            "ic_haut": np.percentile(valides, 97.5) if rapporte else np.nan,
            "n_paires": len(paires_aire),
            "n_communes": len(communes),
            "tirages_ecartes": ecartes,
        }
    return pd.DataFrame.from_dict(lignes, orient="index").rename_axis("aire")


def nuage_paires(paires: pd.DataFrame, acces: str) -> pd.DataFrame:
    """Renvoie le nuage par classes des paires d'une aire, à contrôles donnés (`fig_paires`).

    On retire à `d_part_cadres_2022` et à l'écart d'accès `acces` leur partie expliquée par les
    écarts de `config.CONTROLES_PAIRES` (régressions sans constante, comme `pente_paires`). Par
    le théorème de Frisch-Waugh-Lovell, la pente des résidus de l'un sur les résidus de l'autre
    est exactement celle de `pente_paires` : les points et la droite de la figure disent la même
    chose. Les paires sont symétrisées (chaque paire dans les deux sens), ce qui centre le
    nuage sur zéro sans changer la pente, puis réparties en `config.NB_CLASSES_NUAGE_PAIRES` classes
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
    classe = pd.qcut(symetrisees["acces_residuel"], config.NB_CLASSES_NUAGE_PAIRES, labels=False)
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
    """Renvoie, pour chaque mesure d'accès de H4 et chaque aire, la pente des paires.

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


def ecart_cellule(cellule: pd.DataFrame, colonne_exposition: str, poids: pd.Series) -> float:
    """Renvoie l'écart de part de cadres entre communes exposées et non exposées d'une cellule.

    Coefficient de `colonne_exposition` (0/1) dans la régression de `part_cadres_2022` sur
    l'exposition, `dist_centre_km` et `log_densite` avec constante, pondérée par `poids`.
    Dans une cellule, la constante est sans danger : il n'y a pas de sens i − j.
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


def _ic_ecart_cellule(
    communes: pd.DataFrame, colonne_exposition: str, generateur: np.random.Generator
) -> tuple[float, float]:
    """Renvoie l'intervalle à 95 % de `ecart_cellule` par bootstrap dans chaque groupe.

    `config.NB_TIRAGES_BOOTSTRAP` tirages avec remise des communes exposées parmi les exposées,
    et des non exposées parmi les non exposées : les deux effectifs restent ceux de la cellule.
    Une commune tirée k fois compte k fois ses actifs.
    """
    exposee = communes[colonne_exposition] == 1
    groupes = (communes[exposee], communes[~exposee])
    ecarts = []
    for _ in range(config.NB_TIRAGES_BOOTSTRAP):
        tirees = np.concatenate(
            [generateur.choice(groupe.index, size=len(groupe), replace=True) for groupe in groupes]
        )
        tirage = pd.Series(tirees).value_counts().reindex(communes.index, fill_value=0)
        poids = communes["actifs_2022"] * tirage
        ecarts.append(ecart_cellule(communes, colonne_exposition, poids))
    return float(np.percentile(ecarts, 2.5)), float(np.percentile(ecarts, 97.5))


def ecarts_anneaux(base: pd.DataFrame) -> pd.DataFrame:
    """Renvoie l'écart avec/sans lycée privé de chaque cellule d'anneaux, à 5 et 10 km.

    Cellules de `cellules_anneaux`, les mêmes que celles du tableau de support. Dans chaque
    cellule estimable : `ecart`, l'écart à contrôles donnés pondéré par `actifs_2022`
    (`ecart_cellule`), son intervalle à 95 % (`_ic_ecart_cellule`) et `ecart_brut`, l'écart des
    parts moyennes pondérées. Les écarts sont en fraction ; une cellule non estimable a des
    valeurs manquantes.
    """
    generateur = np.random.default_rng(config.GRAINE_BOOTSTRAP)
    lignes = []
    for rayon in config.RAYONS_SUPPORT_KM:
        colonne_exposition = f"expose_lyc_prive_{rayon}km"
        for cellule in cellules_anneaux(base, rayon).itertuples(index=False):
            ligne = {"rayon_km": rayon, **cellule._asdict()}
            if cellule.estimable:
                dans_la_cellule = (base["aire"] == cellule.aire) & base["dist_centre_km"].between(
                    cellule.bas_km, cellule.haut_km, inclusive="left"
                )
                communes = base[dans_la_cellule]
                exposee = communes[colonne_exposition] == 1
                parts_moyennes = [
                    np.average(groupe["part_cadres_2022"], weights=groupe["actifs_2022"])
                    for groupe in (communes[exposee], communes[~exposee])
                ]
                ic_bas, ic_haut = _ic_ecart_cellule(communes, colonne_exposition, generateur)
                ligne |= {
                    "ecart": ecart_cellule(communes, colonne_exposition, communes["actifs_2022"]),
                    "ic_bas": ic_bas,
                    "ic_haut": ic_haut,
                    "ecart_brut": parts_moyennes[0] - parts_moyennes[1],
                }
            lignes.append(ligne)
    return pd.DataFrame(lignes)


def _concordent(a: pd.Series, b: pd.Series) -> bool:
    """Dit si deux estimations concordent : même signe et intervalles qui se recoupent."""
    meme_signe = np.sign(a["ecart"]) == np.sign(b["ecart"])
    return bool(meme_signe and a["ic_bas"] <= b["ic_haut"] and b["ic_bas"] <= a["ic_haut"])


def verdict_h1(
    principale: pd.DataFrame, secondaire: pd.DataFrame, anneaux: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie le verdict de H1 dans chaque aire, par les règles du plan.

    `principale` et `secondaire` viennent de `pentes_paires_par_aire` sur `d_dist_lyc_prive_min`
    et `d_n_lyc_prive_5km`, `anneaux` de `ecarts_anneaux`. Sens de H1 : pente principale
    négative (plus proche d'un lycée privé, plus de cadres), pente secondaire et écarts des
    cellules positifs. Un anneau comparé est un anneau d'origine couvert par une cellule
    estimable à chacun des deux rayons ; ses deux estimations doivent concorder. Toute cellule
    estimable peut contredire : son intervalle sous zéro fait d'une confirmation une nuance, au
    dessus de zéro il empêche d'établir un résultat nul. Colonnes : `verdict`, `mention`
    (« paires seules » pour une confirmation sans anneau comparé, « résultat nul établi » pour
    une infirmation dont l'intervalle contient zéro), `anneaux_compares`.
    """
    anneaux_origine = list(itertools.pairwise([*config.ANNEAUX_KM, float("inf")]))
    lignes = {}
    for aire in principale.index:
        pente = principale.loc[aire]
        # Un intervalle non rapporté fausserait toutes les comparaisons qui suivent
        assert pente[["ic_bas", "ic_haut"]].notna().all(), f"Intervalle manquant à {aire}."
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

        mention = ""
        if pente["ic_haut"] < 0:
            confirmee = secondaire.loc[aire, "pente"] > 0 and concordants and not contredit
            verdict = "confirmée" if confirmee else "nuancée"
            if confirmee and compares == 0:
                mention = "paires seules"
        elif pente["ic_bas"] > 0:
            verdict = "infirmée"
        elif compares > 0 and concordants and not dans_le_sens:
            verdict, mention = "infirmée", "résultat nul établi"
        else:
            verdict = "non concluante"
        lignes[aire] = {"verdict": verdict, "mention": mention, "anneaux_compares": compares}
    return pd.DataFrame.from_dict(lignes, orient="index").rename_axis("aire")
