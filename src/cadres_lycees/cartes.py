"""Cartes interactives du rapport (folium) : accès aux lycées et part de cadres de 1999 à 2022.

Une fonction par carte, avec la charte de `figures.py` ; les cartes statiques (IRIS) restent des
figures matplotlib.
"""

import html
import itertools

import folium
import geopandas as gpd
import pandas as pd

from cadres_lycees import config

# Curseur des recensements de `carte_cadres_dates` : un contrôle Leaflet qui recolore la couche
# des communes avec les couleurs de chaque année, rangées dans leurs propriétés (`couleur_<année>`).
# Du JavaScript simple, sans bibliothèque : le module à curseur de folium dépend de d3 et de
# moment.js, que certaines pages bloquent
_CURSEUR_JS = """
// Au chargement : folium écrit ce script avant celui qui crée la carte
window.addEventListener("load", function () {
  var carte = __CARTE__, couche = __COUCHE__, annees = __ANNEES__;
  var controle = L.control({position: "topright"});
  controle.onAdd = function () {
    var div = L.DomUtil.create("div");
    div.style.cssText = "background:white;padding:6px 10px;font:13px sans-serif;"
      + "border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.3)";
    var dernier = annees.length - 1;
    div.innerHTML = '<b style="font-size:16px">' + annees[dernier] + "</b> "
      + '<input type="range" min="0" max="' + dernier + '" value="' + dernier
      + '" style="width:160px;vertical-align:middle" aria-label="Recensement"> '
      + '<button type="button">Lecture</button>';
    L.DomEvent.disableClickPropagation(div);
    var etiquette = div.querySelector("b");
    var curseur = div.querySelector("input");
    var bouton = div.querySelector("button");
    var minuterie = null;
    function montre(rang) {
      var annee = annees[rang];
      etiquette.textContent = annee;
      curseur.value = rang;
      couche.setStyle(function (commune) {
        return {
          fillColor: commune.properties["couleur_" + annee],
          fillOpacity: commune.properties["opacite_" + annee]
        };
      });
    }
    function arrete() {
      clearInterval(minuterie);
      minuterie = null;
      bouton.textContent = "Lecture";
    }
    curseur.addEventListener("input", function () { arrete(); montre(+curseur.value); });
    bouton.addEventListener("click", function () {
      if (minuterie) { arrete(); return; }
      var rang = 0;
      montre(rang);
      bouton.textContent = "Pause";
      minuterie = setInterval(function () {
        rang += 1;
        if (rang > dernier) { arrete(); return; }
        montre(rang);
      }, 1200);
    });
    return div;
  };
  controle.addTo(carte);
});
"""


def carte_cadres_dates(communes: gpd.GeoDataFrame, parts: pd.DataFrame, titre: str) -> folium.Map:
    """Carte à curseur de la part de cadres par commune, de 1999 à 2022, pour une aire.

    `communes` : les communes d'une aire, issues de `pipeline.construire_base` ; les
    arrondissements de Lyon sont réunis, la série n'ayant que Lyon entière. `parts` vient de
    `nettoyage.parts_cadres_dates`. Mêmes classes et mêmes couleurs que la carte IRIS ; une
    commune de moins de `config.ACTIFS_MIN_ROBUSTESSE` actifs à une date est pâle, sa part étant
    peu précise (§3.2). Le curseur, un petit contrôle Leaflet (`_CURSEUR_JS`), recolore les
    communes selon le recensement choisi ; le survol donne toutes les dates. `titre` est le
    message de la carte, écrit par le groupe (PLAN §6).
    """
    annees = list(config.GEOGRAPHIE_SERIE_CSP)
    unites = communes.dissolve("code_parent", as_index=False)[["code_parent", "geometry"]]
    noms = communes.set_index("code_commune")["nom_commune"]
    unites["nom"] = unites["code_parent"].map(noms).fillna("Lyon")
    valeurs = parts.loc[unites["code_parent"]].reset_index(drop=True)
    geometrie = unites.geometry.simplify_coverage(config.SIMPLIFICATION_CARTE_M)
    affichage = gpd.GeoDataFrame(
        {"nom": unites["nom"]}, geometry=geometrie, crs=communes.crs
    ).to_crs(config.CRS_CARTES)
    bornes = [0, *config.BORNES_PART_CADRES_IRIS, 100.01]
    for annee in annees:
        pourcentage = valeurs[f"part_cadres_{annee}"] * 100
        affichage[str(annee)] = pourcentage.map(lambda p: f"{p:.1f} %".replace(".", ","))
        # Borne basse incluse, comme dans la légende
        classe = pd.cut(pourcentage, bornes, right=False, labels=False)
        assert classe.notna().all(), f"Part de cadres hors des classes en {annee}."
        affichage[f"couleur_{annee}"] = [config.COULEURS_PART_CADRES_IRIS[int(c)] for c in classe]
        petite = valeurs[f"actifs_{annee}"] < config.ACTIFS_MIN_ROBUSTESSE
        affichage[f"opacite_{annee}"] = petite.map({True: 0.35, False: 0.85})

    carte = folium.Map(tiles=None, control_scale=True)
    for rang, (nom, fournisseur) in enumerate(config.FONDS_CARTE.items()):
        folium.TileLayer(fournisseur, name=nom, show=(rang == 0)).add_to(carte)
    ouest, sud, est, nord = affichage.total_bounds
    carte.fit_bounds([[sud, ouest], [nord, est]])
    derniere = annees[-1]
    couche = folium.GeoJson(
        affichage,
        name="Part de cadres",
        # Le dernier recensement à l'ouverture : le curseur remonte le temps
        style_function=lambda commune: {
            "fillColor": commune["properties"][f"couleur_{derniere}"],
            "fillOpacity": commune["properties"][f"opacite_{derniere}"],
            "color": "white",
            "weight": 0.4,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nom", *[str(annee) for annee in annees]],
            aliases=["Commune", *[f"Part de cadres en {annee}" for annee in annees]],
        ),
    ).add_to(carte)
    folium.LayerControl(collapsed=True, position="bottomright").add_to(carte)
    curseur = (
        _CURSEUR_JS.replace("__CARTE__", carte.get_name())
        .replace("__COUCHE__", couche.get_name())
        .replace("__ANNEES__", str(annees))
    )
    carte.get_root().script.add_child(folium.Element(curseur))

    libelles = [f"moins de {bornes[1]} %"]
    libelles += [f"{bas} à {haut} %" for bas, haut in itertools.pairwise(bornes[1:-1])]
    libelles.append(f"{bornes[-2]} % ou plus")
    classes = "".join(
        '<div><span style="display:inline-block;width:10px;height:10px;margin-right:6px;'
        f'background:{couleur}"></span>{libelle}</div>'
        for couleur, libelle in zip(config.COULEURS_PART_CADRES_IRIS, libelles, strict=True)
    )
    # Courte : la légende est posée sur la carte ; la définition complète est dans le rapport
    note = (
        f"Actifs de 25 à 54 ans ; Lyon entière. Pâle : moins de {config.ACTIFS_MIN_ROBUSTESSE} "
        "actifs. Sources : Insee, séries historiques du recensement ; IGN."
    )
    legende = (
        '<div style="position:fixed;bottom:28px;left:12px;z-index:1000;background:white;'
        f'padding:8px;font:11px sans-serif;color:{config.COULEUR_TEXTE};width:170px">'
        f"<b>Part de cadres</b>{classes}<p style='font-size:10px'>{note}</p></div>"
    )
    carte.get_root().html.add_child(folium.Element(legende))
    entete = (
        '<div style="position:fixed;top:10px;left:56px;z-index:1000;background:white;'
        f'padding:6px 10px;font:bold 14px sans-serif;color:{config.COULEUR_TEXTE};max-width:45%">'
        f"{html.escape(titre)}</div>"
    )
    carte.get_root().html.add_child(folium.Element(entete))
    return carte


def _libelles_distance() -> list[str]:
    """Libellés des classes de `config.BORNES_DISTANCE_KM`, du plus proche au plus loin."""
    bornes = config.BORNES_DISTANCE_KM
    libelles = [f"{bornes[0]} km ou moins"]
    libelles += [f"{bas} à {haut} km" for bas, haut in itertools.pairwise(bornes)]
    libelles.append(f"plus de {bornes[-1]} km")
    return libelles


def fig3(communes: gpd.GeoDataFrame, lycees: gpd.GeoDataFrame, titre: str) -> folium.Map:
    """Fig. 3 : carte interactive de la distance au lycée privé sous contrat le plus proche.

    `communes` et `lycees` sont la base et les lycées de `pipeline.construire_base`. Les communes
    sont colorées par classe de distance, les lycées sont des points colorés par secteur. Les
    contours sont simplifiés pour l'affichage seulement. `titre` est le message de la carte,
    écrit par le groupe (PLAN §6) ; la légende en décrit le contenu.
    """
    assert communes.crs == config.CRS_CALCUL and lycees.crs == config.CRS_CALCUL, (
        f"Communes en {communes.crs}, lycées en {lycees.crs} : EPSG:{config.CRS_CALCUL} attendu."
    )
    # La simplification ne garde les frontières partagées que si les contours, sans trou ni
    # chevauchement, forment une couverture valide
    assert communes.geometry.is_valid_coverage(), "Les contours ne forment pas une couverture."

    bornes = [0, *config.BORNES_DISTANCE_KM, float("inf")]
    # Bornes supérieures incluses, comme dans les indicateurs : « 5 km ou moins » équivaut à
    # au moins un lycée privé dans le rayon de 5 km
    classe = pd.cut(communes["dist_lyc_prive_min"], bornes, labels=False, include_lowest=True)
    assert classe.notna().all(), "Distance hors des classes de la Fig. 3."
    # Seules les colonnes affichées partent dans la page : la seconde géométrie (`centroide`)
    # ferait échouer l'export GeoJSON, et les autres colonnes l'alourdiraient
    affichage = gpd.GeoDataFrame(
        {
            "nom_commune": communes["nom_commune"],
            "aire": communes["aire"],
            "dist_lyc_prive_min": communes["dist_lyc_prive_min"].map(
                lambda km: f"{km:.1f} km".replace(".", ",")
            ),
            "n_lyc_prive_5km": communes["n_lyc_prive_5km"],
            "n_lyc_prive_10km": communes["n_lyc_prive_10km"],
            "couleur": [config.COULEURS_DISTANCE[rang] for rang in classe],
        },
        geometry=communes.geometry.simplify_coverage(config.SIMPLIFICATION_CARTE_M),
    ).to_crs(config.CRS_CARTES)
    limites = affichage[["aire", "geometry"]].dissolve("aire").reset_index()

    # Lycées affichés : ceux à 10 km ou moins du contour d'une commune, donc tous ceux que
    # comptent les `n_lyc_*`, et le lycée privé le plus proche de chaque commune, qui donne sa
    # couleur à la commune même quand il est plus loin
    zone = communes.geometry.union_all()
    dans_la_zone = lycees.distance(zone) <= max(config.RAYONS_KM) * 1000
    centroides = communes.set_geometry("centroide")[["centroide"]]
    prives = lycees.loc[lycees["secteur"] == "prive", ["geometry"]]
    plus_proches = gpd.sjoin_nearest(centroides, prives)["index_right"]
    affiches = lycees[dans_la_zone | lycees.index.isin(plus_proches)].to_crs(config.CRS_CARTES)

    carte = folium.Map(tiles=None, control_scale=True)
    for rang, (nom, fournisseur) in enumerate(config.FONDS_CARTE.items()):
        # Le premier fond s'affiche, les autres se choisissent dans le sélecteur de couches
        folium.TileLayer(fournisseur, name=nom, show=(rang == 0)).add_to(carte)
    ouest, sud, est, nord = affichage.total_bounds
    carte.fit_bounds([[sud, ouest], [nord, est]])
    folium.GeoJson(
        affichage,
        name="Distance au lycée privé sous contrat le plus proche",
        style_function=lambda commune: {
            "fillColor": commune["properties"]["couleur"],
            "fillOpacity": 0.8,
            "color": "white",
            "weight": 0.5,
        },
        highlight_function=lambda _: {"color": config.COULEUR_TEXTE, "weight": 2},
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "nom_commune",
                "aire",
                "dist_lyc_prive_min",
                "n_lyc_prive_5km",
                "n_lyc_prive_10km",
            ],
            aliases=[
                "Commune",
                "Aire",
                "Lycée privé sous contrat le plus proche",
                "Lycées privés sous contrat à 5 km",
                "Lycées privés sous contrat à 10 km",
            ],
        ),
    ).add_to(carte)
    folium.GeoJson(
        limites,
        name="Limites des aires",
        style_function=lambda _: {"fill": False, "color": config.COULEUR_TEXTE, "weight": 2},
    ).add_to(carte)

    # Les privés en dernier, pour qu'ils restent visibles au-dessus des publics
    for secteur in ("public", "prive"):
        du_secteur = affiches[affiches["secteur"] == secteur]
        libelle = f"secteur {config.LIBELLES_SECTEURS[secteur]}"
        groupe = folium.FeatureGroup(name=f"Lycées, {libelle} ({len(du_secteur)})")
        for lycee in du_secteur.itertuples():
            if pd.isna(lycee.ips):
                ips = "IPS non publié"
            else:
                ips = f"IPS {lycee.ips:.0f} (voie GT, {config.RENTREE_IPS})"
            folium.CircleMarker(
                location=[lycee.geometry.y, lycee.geometry.x],
                radius=5,
                color="white",
                weight=1,
                fill=True,
                fill_color=config.COULEURS_SECTEURS[secteur],
                fill_opacity=1,
                tooltip=f"<b>{html.escape(lycee.nom_lycee)}</b><br>{libelle.capitalize()}<br>{ips}",
            ).add_to(groupe)
        groupe.add_to(carte)
    folium.LayerControl(collapsed=True).add_to(carte)

    # folium n'a pas de légende par classes : elle est écrite en HTML, fixée au-dessus du fond
    pastille = (
        '<span style="display:inline-block;width:10px;height:10px;margin-right:6px;'
        f"border:1px solid {config.COULEUR_LIAISON};border-radius:{{arrondi}};"
        'background:{couleur}"></span>'
    )
    classes = "".join(
        f"<div>{pastille.format(arrondi=0, couleur=couleur)}{libelle}</div>"
        for couleur, libelle in zip(config.COULEURS_DISTANCE, _libelles_distance(), strict=True)
    )
    points = "".join(
        f"<div>{pastille.format(arrondi='50%', couleur=config.COULEURS_SECTEURS[secteur])}"
        f"Lycée, secteur {config.LIBELLES_SECTEURS[secteur]}</div>"
        for secteur in ("prive", "public")
    )
    note = (
        f"{config.RAYON_PRINCIPAL_KM} km ou moins : au moins un lycée privé sous contrat dans "
        "le rayon principal. Distance à vol d'oiseau depuis le centroïde de la commune, "
        "calculée sur les lycées de France métropolitaine (les lycées étrangers sont absents). "
        "Points : lycées généraux, technologiques et polyvalents à "
        f"{max(config.RAYONS_KM)} km ou moins d'une commune, y compris hors des aires, et "
        "lycée privé le plus proche de chaque commune."
    )
    source = (
        f"Sources : annuaire de l'éducation ({config.DATE_ANNUAIRE}), DEPP (IPS, rentrée "
        f"{config.RENTREE_IPS}), Insee (aires d'attraction des villes 2020), IGN (ADMIN EXPRESS, "
        f"COG {config.ANNEE_COG})."
    )
    legende = (
        '<div style="position:fixed;bottom:28px;left:12px;z-index:1000;background:white;'
        f'padding:8px;font:11px sans-serif;color:{config.COULEUR_TEXTE};width:250px">'
        "<b>Distance au lycée privé sous contrat le plus proche</b>"
        f"{classes}{points}"
        f"<p style='font-size:10px'>{note}</p><p style='font-size:10px'>{source}</p></div>"
    )
    carte.get_root().html.add_child(folium.Element(legende))
    # À droite des boutons de zoom, en haut à gauche de la carte
    entete = (
        '<div style="position:fixed;top:10px;left:56px;z-index:1000;background:white;'
        f'padding:6px 10px;font:bold 14px sans-serif;color:{config.COULEUR_TEXTE};max-width:60%">'
        f"{html.escape(titre)}</div>"
    )
    carte.get_root().html.add_child(folium.Element(entete))
    return carte
