"""Robustesse de H1 et de H3, et indice de Moran de la part de cadres."""

import esda
import geopandas as gpd
import libpysal
import numpy as np
import pandas as pd

from cadres_lycees import accessibilite, analyse, config, geo, h1, h3, nettoyage


def robustesse_h3(
    base: gpd.GeoDataFrame, lycees: gpd.GeoDataFrame, sessions_ival: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie β_q, β_n et β_q − β_n de H3, toutes aires ensemble, dans ses robustesses.

    Spécification principale, puis l'IVAL moyenne sur 2012-2025 au lieu de 2012-2022, puis la
    valeur ajoutée du taux de réussite au lieu du taux d'accès de la seconde au bac. Seule l'IVAL
    des lycées change ; `ival_moy_5km`, la population, les grappes et l'estimation suivent les
    mêmes règles (`h3.population_h3`, `h3.estimation_h3`). Index (`variante`, `coefficient`) ;
    colonnes de `h3.estimation_h3`.
    """
    rayon = config.RAYON_PRINCIPAL_KM
    premiere, nb_min = config.PREMIERE_SESSION_IVAL, config.NB_SESSIONS_MIN_IVAL
    variantes = {
        "Spécification principale": (config.DERNIERE_SESSION_IVAL, config.INDICATEUR_IVAL),
        f"IVAL de {premiere} à {config.DERNIERE_SESSION_IVAL_ROBUSTESSE}": (
            config.DERNIERE_SESSION_IVAL_ROBUSTESSE,
            config.INDICATEUR_IVAL,
        ),
        "Valeur ajoutée du taux de réussite": (
            config.DERNIERE_SESSION_IVAL,
            config.INDICATEUR_IVAL_ROBUSTESSE,
        ),
    }
    resultats = {}
    for nom, (derniere, indicateur) in variantes.items():
        ival = nettoyage.ival_par_lycee(sessions_ival, premiere, derniere, nb_min, indicateur)
        lycees_variante = lycees.drop(columns=["ival", "poids_ival"]).join(
            ival, on="uai", how="left"
        )
        acces = accessibilite.indicateurs(
            base, lycees_variante, "lyc", rayons=(rayon,), attribut="ival", poids="poids_ival"
        )
        base_variante = base.drop(columns=f"ival_moy_{rayon}km").merge(
            acces[[f"ival_moy_{rayon}km"]],
            left_on="code_commune",
            right_index=True,
            how="left",
            validate="one_to_one",
        )
        estimation = h3.estimation_h3(h3.population_h3(base_variante, lycees_variante))
        resultats[nom] = estimation.loc["ensemble"]
    return pd.concat(resultats, names=["variante", "coefficient"])


def _ecart_paires(paires: pd.DataFrame, base: pd.DataFrame, variable: str) -> pd.Series:
    """Renvoie l'écart i − j de `variable` dans les paires, comme `geo.paires_contigues`."""
    valeurs = base.set_index("code_commune")[variable]
    return paires["code_commune_i"].map(valeurs) - paires["code_commune_j"].map(valeurs)


def _communes_centres(base: pd.DataFrame) -> pd.Series:
    """Renvoie les codes des communes-centres : la plus proche du centre de chaque aire.

    À Lyon, la commune-centre est Lyon entière : tous les arrondissements de même `code_parent`.
    """
    plus_proches = base.loc[base.groupby("aire")["dist_centre_km"].idxmin(), "code_parent"]
    return base.loc[base["code_parent"].isin(plus_proches), "code_commune"]


def _paires_sans(paires: pd.DataFrame, communes: pd.Series) -> pd.DataFrame:
    """Renvoie les paires qui ne touchent aucune des `communes` (codes communes).

    Retirer une commune retire toutes ses paires.
    """
    touchees = paires["code_commune_i"].isin(communes) | paires["code_commune_j"].isin(communes)
    return paires[~touchees]


def robustesse_h1(
    base: gpd.GeoDataFrame,
    paires: pd.DataFrame,
    lycees: gpd.GeoDataFrame,
    prives_elargis: gpd.GeoDataFrame,
    chefs_lieux: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Renvoie les pentes de H1 dans chaque variante de robustesse, aire par aire.

    Dans l'ordre du plan, après la spécification principale : pente secondaire à 3 et 10 km (le
    rayon de 5 km est la secondaire) ; avec le logarithme du prix au m² en contrôle, sur les
    paires dont les deux communes ont un prix, hors de `config.AIRES_HORS_DVF` ; part de cadres
    parmi les 15 ans ou plus en 2022 ; distance au lycée privé le plus proche parmi
    `prives_elargis` (`pipeline.lycees_prives_robustesse`, professionnels et hors contrat
    inclus) ; sans la commune-centre ; sans les communes de moins de
    `config.ACTIFS_MIN_ROBUSTESSE` actifs en 2022 ; sans les communes à moins de
    `config.DIST_FRONTIERE_KM` km du contour national, dans les aires frontalières seulement ;
    sans contrôle de densité. Même estimation et même bootstrap que `h1.pentes_paires_par_aire`.
    Index (`variante`, `aire`) ; colonnes de `h1.pentes_paires_par_aire`, en fraction par km ou par
    lycée.
    """
    principale = "d_dist_lyc_prive_min"
    variantes = {"Spécification principale": h1.pentes_paires_par_aire(paires, principale)}

    for rayon in [r for r in config.RAYONS_KM if r != config.RAYON_PRINCIPAL_KM]:
        colonne = f"d_n_lyc_prive_{rayon}km"
        ecart = _ecart_paires(paires, base, f"n_lyc_prive_{rayon}km")
        variantes[f"Pente secondaire à {rayon} km"] = h1.pentes_paires_par_aire(
            paires.assign(**{colonne: ecart}), colonne
        )

    # Prix au m² : paires dont les deux communes ont un prix, hors des aires sans DVF
    ecart_prix = _ecart_paires(paires, base, "log_prix_m2")
    avec_prix = paires.assign(d_log_prix_m2=ecart_prix)
    avec_prix = avec_prix[ecart_prix.notna() & ~paires["aire"].isin(config.AIRES_HORS_DVF)]
    variantes["Avec contrôle du prix au m²"] = h1.pentes_paires_par_aire(
        avec_prix, principale, controles=(*config.CONTROLES_PAIRES, "d_log_prix_m2")
    )

    # La part de cadres des 15 ans ou plus prend la place de la variable à expliquer
    ecart_15p = _ecart_paires(paires, base, "part_cadres_15p_2022")
    variantes["Cadres parmi les 15 ans ou plus"] = h1.pentes_paires_par_aire(
        paires.assign(d_part_cadres_2022=ecart_15p), principale
    )

    # Seule la distance au lycée privé change : contrôles et part de cadres restent les mêmes
    acces_elargi = accessibilite.indicateurs(base, prives_elargis, "lyc_prive", rayons=())
    ecart_elargi = _ecart_paires(paires, acces_elargi.reset_index(), "dist_lyc_prive_min")
    variantes["Lycées professionnels et privé hors contrat inclus"] = h1.pentes_paires_par_aire(
        paires.assign(d_dist_lyc_prive_min=ecart_elargi), principale
    )

    # Chef-lieu : la distance au lycée privé est mesurée depuis la mairie
    # (`collecte.chefs_lieux`) au lieu du centroïde ; contrôles et part de cadres restent les mêmes
    mairies = base[["code_commune"]].merge(chefs_lieux, on="code_commune", validate="one_to_one")
    assert len(mairies) == len(base), "Commune sans chef-lieu dans ADMIN EXPRESS."
    depuis_mairie = base.assign(centroide=gpd.GeoSeries(mairies["geometry"].values, crs=base.crs))
    prives = lycees[lycees["secteur"] == "prive"]
    acces_mairie = accessibilite.indicateurs(depuis_mairie, prives, "lyc_prive", rayons=())
    ecart_mairie = _ecart_paires(paires, acces_mairie.reset_index(), "dist_lyc_prive_min")
    variantes["Distances depuis le chef-lieu (mairie)"] = h1.pentes_paires_par_aire(
        paires.assign(d_dist_lyc_prive_min=ecart_mairie), principale
    )

    variantes["Sans la commune-centre"] = h1.pentes_paires_par_aire(
        _paires_sans(paires, _communes_centres(base)), principale
    )

    petites = base.loc[base["actifs_2022"] < config.ACTIFS_MIN_ROBUSTESSE, "code_commune"]
    variantes[f"Sans les communes de moins de {config.ACTIFS_MIN_ROBUSTESSE} actifs"] = (
        h1.pentes_paires_par_aire(_paires_sans(paires, petites), principale)
    )

    distance_frontiere = base["code_commune"].map(geo.distance_contour_national_km(base))
    pres_frontiere = base.loc[
        base["aire"].isin(config.AIRES_FRONTALIERES)
        & (distance_frontiere < config.DIST_FRONTIERE_KM),
        "code_commune",
    ]
    frontiere = h1.pentes_paires_par_aire(_paires_sans(paires, pres_frontiere), principale)
    # Ailleurs qu'aux aires frontalières, la variante redonnerait la spécification principale
    nom = f"Sans les communes à moins de {config.DIST_FRONTIERE_KM} km de la frontière"
    variantes[nom] = frontiere[frontiere.index.isin(config.AIRES_FRONTALIERES)]

    sans_densite = tuple(c for c in config.CONTROLES_PAIRES if c != "d_log_densite")
    variantes["Sans contrôle de densité"] = h1.pentes_paires_par_aire(
        paires, principale, controles=sans_densite
    )
    return pd.concat(variantes, names=["variante", "aire"])


def moran_part_cadres(base: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie l'indice I de Moran de la part de cadres dans chaque aire.

    Contiguïté Queen, la même que celle des paires.
    Deux variables : `part_cadres_2022`, puis l'écart restant après la comparaison par
    anneaux, c'est-à-dire la part moins la moyenne simple de son anneau, sans fusion. La
    p-valeur vient de `config.NB_PERMUTATIONS_MORAN` permutations, avec la graine du bootstrap.
    Index (`aire`, `variable`) ; colonnes `I`, `p_valeur`, `n_communes`.
    """
    lignes = []
    communes = base.copy()
    anneau = analyse.anneau(communes["dist_centre_km"])
    moyenne_anneau = communes.groupby(["aire", anneau], observed=True)[
        "part_cadres_2022"
    ].transform("mean")
    communes["ecart_anneau"] = communes["part_cadres_2022"] - moyenne_anneau
    for aire, communes_aire in communes.groupby("aire"):
        voisinage = libpysal.weights.Queen.from_dataframe(
            communes_aire.reset_index(drop=True), use_index=False, silence_warnings=True
        )
        assert not voisinage.islands, f"Communes sans voisine dans {aire} : {voisinage.islands}."
        for variable in ("part_cadres_2022", "ecart_anneau"):
            # esda tire ses permutations avec le générateur global de numpy
            np.random.seed(config.GRAINE_BOOTSTRAP)
            moran = esda.Moran(
                communes_aire[variable].to_numpy(),
                voisinage,
                permutations=config.NB_PERMUTATIONS_MORAN,
            )
            lignes.append(
                {
                    "aire": aire,
                    "variable": variable,
                    "I": moran.I,
                    "p_valeur": moran.p_sim,
                    "n_communes": len(communes_aire),
                }
            )
    return pd.DataFrame(lignes).set_index(["aire", "variable"])
