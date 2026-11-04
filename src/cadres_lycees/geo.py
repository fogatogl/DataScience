"""Géographie des communes : référentiel des aires, distances en Lambert 93, paires contiguës."""

import geopandas as gpd
import pandas as pd

from cadres_lycees import collecte, config


def _referentiel_aire(nom: str, code_aav: str, aav: pd.DataFrame) -> gpd.GeoDataFrame:
    """Construit les lignes du référentiel pour une aire (voir `referentiel_communes`)."""
    communes_aav = aav[aav["AAV2020"] == code_aav]
    contours = collecte.contours_aire(code_aav).to_crs(config.CRS_CALCUL)

    # Les contours doivent couvrir exactement les communes de la table AAV : un arrondissement
    # compte pour sa commune parente (`INSEE_COM`), il y a donc plus d'unités que de communes
    # à Lyon seulement
    ecart = set(contours["INSEE_COM"]) ^ set(communes_aav["CODGEO"])
    assert not ecart, (
        f"Communes présentes dans les contours ou dans la table AAV seulement, aire {nom} : "
        f"{sorted(ecart)}"
    )
    assert contours["INSEE_COG"].is_unique, f"Codes d'unités en double pour l'aire {nom}."
    # L'égalité d'ensembles passe même si un arrondissement manque, et le centre de l'aire (union
    # des arrondissements de sa commune) serait alors faussé : on compte les unités par commune
    nb_unites = contours.groupby("INSEE_COM").size()
    nb_attendu = [config.NB_ARRONDISSEMENTS.get(parent, 1) for parent in nb_unites.index]
    assert nb_unites.tolist() == nb_attendu, f"Arrondissements manquants dans l'aire {nom}."

    unites = contours.rename(
        columns={"INSEE_COG": "code_commune", "INSEE_COM": "code_parent", "NOM": "nom_commune"}
    )
    unites = unites[["code_commune", "code_parent", "nom_commune", "geometry"]].copy()
    unites["aire"] = nom
    categorie = communes_aav.set_index("CODGEO")["CATEAAV2020"]
    unites["pole_couronne"] = unites["code_parent"].map(categorie).map(config.POLE_COURONNE_AAV)
    assert unites["pole_couronne"].notna().all(), f"Catégorie AAV non reconnue dans l'aire {nom}."

    # Le centre est la commune entière, y compris à Lyon : on réunit ses arrondissements
    # plutôt que de prendre le plus peuplé (Lyon 3e)
    centres = communes_aav.loc[
        communes_aav["CATEAAV2020"] == config.CATEGORIE_COMMUNE_CENTRE, "CODGEO"
    ]
    assert len(centres) == 1, f"{len(centres)} communes-centres dans l'aire {nom}, 1 attendue."
    contour_centre = unites.loc[unites["code_parent"] == centres.iloc[0], "geometry"].union_all()

    unites["centroide"] = unites.geometry.centroid
    unites["dist_centre_km"] = unites["centroide"].distance(contour_centre.centroid) / 1000
    return unites


def referentiel_communes(aires: dict[str, str]) -> gpd.GeoDataFrame:
    """Renvoie une ligne par commune des aires demandées, en Lambert 93.

    `aires` associe le nom de l'aire à son code AAV2020 (par exemple `config.AIRES_CANDIDATES`).
    Les arrondissements municipaux remplacent leur commune parente : `code_parent`
    donne la commune parente, celle des sources qui ignorent les arrondissements.

    Colonnes : `code_commune`, `code_parent`, `nom_commune`, `aire`, `pole_couronne`,
    `geometry` (contour), `centroide` (point de référence de la commune) et
    `dist_centre_km`, la distance en kilomètres entre ce centroïde et celui de la
    commune-centre de l'aire.
    """
    aav = collecte.aav_2020()
    referentiel = pd.concat(
        [_referentiel_aire(nom, code, aav) for nom, code in aires.items()], ignore_index=True
    )

    assert referentiel["code_commune"].is_unique, "Une commune est dans deux aires."
    nb_communes_aav = aav["AAV2020"].isin(aires.values()).sum()
    assert referentiel["code_parent"].nunique() == nb_communes_aav, (
        "Le nombre de communes diffère de celui de la table AAV."
    )
    geometrie_vide = referentiel.geometry.isna() | referentiel.geometry.is_empty
    assert not geometrie_vide.any(), "Des communes n'ont pas de contour."
    return referentiel


def paires_contigues(communes: gpd.GeoDataFrame, variables: list[str]) -> pd.DataFrame:
    """Renvoie une ligne par paire de communes contiguës d'une même aire, avec leurs écarts.

    Contiguïté « Queen » : deux communes sont voisines si leurs contours se touchent, par un
    bord ou par un seul point, comme pour l'indice de Moran. Une paire n'apparaît
    qu'une fois, avec `code_commune_i` < `code_commune_j`, et `d_<v>` vaut la valeur de i moins
    celle de j pour chaque variable v de `variables` (manquant si l'une des deux manque). Ce sens
    suit l'ordre des codes, il est donc arbitraire : seules une pente estimée sans constante ou
    des paires symétrisées, (i, j) et (j, i), n'en dépendent pas. Une commune sans voisine dans
    son aire fait échouer.
    """
    assert communes["code_commune"].is_unique, "Des codes communes sont en double."
    contours = communes[["code_commune", "aire", "geometry"]]
    # `intersects` garde les contours qui partagent un bord ou un point, et aussi ceux qui se
    # recouvrent très peu, ce que `touches` écarterait
    contacts = gpd.sjoin(contours, contours, predicate="intersects", lsuffix="i", rsuffix="j")
    # Chaque contact sort deux fois, (i, j) puis (j, i), et chaque commune se touche elle-même
    une_fois = contacts["code_commune_i"] < contacts["code_commune_j"]
    meme_aire = contacts["aire_i"] == contacts["aire_j"]
    paires = contacts.loc[une_fois & meme_aire, ["code_commune_i", "code_commune_j", "aire_i"]]
    paires = paires.rename(columns={"aire_i": "aire"}).reset_index(drop=True)
    assert not paires.duplicated(["code_commune_i", "code_commune_j"]).any(), "Paire en double."
    # Une commune sans voisine dans son aire disparaîtrait des paires sans aucun signal
    dans_une_paire = set(paires["code_commune_i"]) | set(paires["code_commune_j"])
    isolees = sorted(set(communes["code_commune"]) - dans_une_paire)
    assert not isolees, f"Communes sans voisine dans leur aire : {isolees}."

    # Les valeurs sont lues par code commune, jamais par position
    valeurs = communes.set_index("code_commune")[variables]
    for variable in variables:
        valeur_i = paires["code_commune_i"].map(valeurs[variable])
        valeur_j = paires["code_commune_j"].map(valeurs[variable])
        paires[f"d_{variable}"] = valeur_i - valeur_j
    return paires


def distance_contour_national_km(communes: gpd.GeoDataFrame) -> pd.Series:
    """Renvoie la distance en km du centroïde de chaque commune au contour de la métropole.

    Le contour est celui de l'union des départements métropolitains : il suit la frontière
    terrestre et le littoral. Il ne mesure donc la distance à la frontière que loin des côtes,
    ce qui est le cas de Lille et de Strasbourg, les seules aires où elle sert. Le résultat
    est indexé par `code_commune`.
    """
    departements = collecte.contours_departements().to_crs(config.CRS_CALCUL)
    # Les codes à deux caractères sont ceux de la métropole, Corse comprise ("2A", "2B")
    metropole = departements[departements["INSEE_DEP"].str.len() == 2]
    assert len(metropole) == config.NB_DEPARTEMENTS_METROPOLE, (
        f"{len(metropole)} départements de métropole, {config.NB_DEPARTEMENTS_METROPOLE} attendus."
    )
    contour = metropole.geometry.union_all().boundary
    centroides = communes.set_index("code_commune").set_geometry("centroide")["centroide"]
    # La distance à une géométrie seule ne vérifie pas la projection : on le fait ici
    assert centroides.crs == config.CRS_CALCUL, (
        f"Centroïdes en {centroides.crs}, pas en Lambert 93."
    )
    distances = (centroides.distance(contour) / 1000).rename("dist_contour_national_km")
    assert distances.notna().all(), "Distance au contour national manquante."
    return distances
