"""Construit la présentation de soutenance : _site/presentation.html, à côté du site Quarto.

La page est le gabarit `presentation/page.html` (HTML, CSS et JavaScript), dans lequel ce script
insère les données et les résultats du projet, recalculés depuis les copies gelées comme le
rapport. À lancer après `uv run quarto render`, qui vide `_site/` :

    uv run python presentation/construire.py
"""

import base64
import io
import json
import math

import numpy as np
import pandas as pd
import requests
from PIL import Image

from cadres_lycees import analyse, collecte, config, geo, h1, h3, nettoyage, pipeline, robustesse


def lignes(tableau: pd.DataFrame) -> list[dict]:
    """Renvoie les lignes d'un tableau en dictionnaires sérialisables (NaN devient None)."""
    # Une borne infinie (dernier anneau) devient une borne finie, que la page lit « et plus » ;
    # 15 décimales (le maximum) car la page arrondit elle-même les pentes, stockées en fraction
    texte = tableau.replace([np.inf], config.BORNE_OUVERTE_PRESENTATION).to_json(
        orient="records", force_ascii=False, double_precision=15
    )
    return json.loads(texte)


def communes_geojson(base: pd.DataFrame) -> dict:
    """Renvoie les communes en GeoJSON léger : contours simplifiés, coordonnées à 4 décimales."""
    colonnes = [
        "code_parent",
        "nom_commune",
        "aire",
        "dist_centre_km",
        "dist_lyc_prive_min",
        "n_lyc_prive_5km",
        "part_cadres_2022",
    ]
    communes = base[[*colonnes, "geometry"]].copy()
    communes["geometry"] = communes.geometry.simplify(config.SIMPLIFICATION_PRESENTATION_M)
    communes = communes.to_crs(config.CRS_CARTES)
    communes["geometry"] = communes.geometry.set_precision(1e-4)
    return json.loads(communes.to_json(drop_id=True))


def parts_dates(base: pd.DataFrame) -> dict:
    """Renvoie la part de cadres de chaque commune aux cinq recensements de 1999 à 2022."""
    series = {annee: collecte.serie_csp_2554(annee) for annee in config.GEOGRAPHIE_SERIE_CSP}
    parts = nettoyage.parts_cadres_dates(series, collecte.passage_communes(), base)
    return {code: ligne.round(5).to_dict() for code, ligne in parts.iterrows()}


def _tuile(longitude: float, latitude: float, zoom: int) -> tuple[int, int]:
    """Renvoie les indices de la tuile Web Mercator qui contient un point."""
    n = 2**zoom
    x = (longitude + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(latitude))) / math.pi) / 2 * n
    return int(x), int(y)


def _coin(x: int, y: int, zoom: int) -> tuple[float, float]:
    """Renvoie la longitude et la latitude du coin nord-ouest d'une tuile."""
    n = 2**zoom
    latitude = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return x / n * 360 - 180, latitude


def fond_ign(communes_aire: pd.DataFrame) -> dict:
    """Renvoie le fond Plan IGN d'une aire : une image en niveaux de gris et ses bornes.

    Les tuiles qui couvrent l'aire sont assemblées puis réduites : la page affiche ainsi un
    fond sans dépendre du service de tuiles. Bornes au format Leaflet [[sud, ouest], [nord, est]].
    """
    zoom = config.ZOOM_FONDS_PRESENTATION
    ouest, sud, est, nord = communes_aire.to_crs(config.CRS_CARTES).total_bounds
    x0, y0 = _tuile(ouest, nord, zoom)
    x1, y1 = _tuile(est, sud, zoom)
    image = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    with requests.Session() as session:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                url = config.URL_TUILES_IGN.format(z=zoom, x=x, y=y)
                reponse = session.get(url, timeout=config.DELAI_TELECHARGEMENT_S)
                reponse.raise_for_status()
                tuile = Image.open(io.BytesIO(reponse.content)).convert("RGB")
                image.paste(tuile, ((x - x0) * 256, (y - y0) * 256))
    largeur = config.LARGEUR_FONDS_PRESENTATION
    image = image.convert("L").resize((largeur, round(image.height * largeur / image.width)))
    tampon = io.BytesIO()
    image.save(tampon, "JPEG", quality=config.QUALITE_JPEG_FONDS_PRESENTATION, optimize=True)
    lon_o, lat_n = _coin(x0, y0, zoom)
    lon_e, lat_s = _coin(x1 + 1, y1 + 1, zoom)
    return {
        "bornes": [[lat_s, lon_o], [lat_n, lon_e]],
        "uri": "data:image/jpeg;base64," + base64.b64encode(tampon.getvalue()).decode(),
    }


def resultats(base: pd.DataFrame, lycees: pd.DataFrame, paires: pd.DataFrame) -> dict:
    """Renvoie les résultats affichés par la page, calculés par les modules du projet."""
    aires = list(config.AIRES_RETENUES)
    candidates = pipeline.lycees_avec_aire(geo.referentiel_communes(config.AIRES_CANDIDATES))
    lycees_aires = lycees[lycees["aire"].notna()].to_crs(config.CRS_CARTES)
    sessions_ival = collecte.ival_lycees()

    principale = h1.pentes_paires_par_aire(paires, "d_dist_lyc_prive_min")
    secondaire = h1.pentes_paires_par_aire(paires, "d_n_lyc_prive_5km")
    anneaux = h1.ecarts_anneaux(base)
    fiabilite = h3.fiabilite_ival(base, lycees, sessions_ival)
    estimation = h3.estimation_h3(h3.population_h3(base, lycees))
    variantes = robustesse.robustesse_h1(
        base, paires, lycees, pipeline.lycees_prives_robustesse(), collecte.chefs_lieux()
    )
    acces = analyse.resume_acces(base)[["communes", "part_exposees"]]
    return {
        "aires": aires,
        "borne_ouverte": config.BORNE_OUVERTE_PRESENTATION,
        # Mêmes classes, couleurs et seuil de précision que la carte à curseur du rapport
        "carte_cadres": {
            "annees": list(config.GEOGRAPHIE_SERIE_CSP),
            "bornes_pct": list(config.BORNES_PART_CADRES_IRIS),
            "couleurs": list(config.COULEURS_PART_CADRES_IRIS),
            "actifs_min": config.ACTIFS_MIN_ROBUSTESSE,
        },
        "lycees": [
            {
                "nom": ligne.nom_lycee,
                "secteur": ligne.secteur,
                "aire": ligne.aire,
                "ips": None if pd.isna(ligne.ips) else ligne.ips,
                "ival": None if pd.isna(ligne.ival) else round(ligne.ival, 5),
                "lat": round(ligne.geometry.y, 5),
                "lon": round(ligne.geometry.x, 5),
            }
            for ligne in lycees_aires.itertuples()
        ],
        "profil_aires": lignes(analyse.profil_aires(candidates).loc[aires].reset_index()),
        "acces": lignes(acces.reset_index()),
        "gradient": lignes(analyse.parts_par_anneau(base).reset_index()),
        "n_paires": paires["aire"].value_counts().to_dict(),
        "h1_principale": lignes(principale.reset_index()),
        "h1_secondaire": lignes(secondaire.reset_index()),
        "h1_anneaux": lignes(anneaux),
        "h1_verdict": lignes(h1.verdict_h1(principale, secondaire, anneaux).reset_index()),
        "h1_nuage": {
            aire: lignes(h1.nuage_paires(paires[paires["aire"] == aire], "d_dist_lyc_prive_min"))
            for aire in aires
        },
        "fiabilite_ival": lignes(fiabilite.reset_index()),
        "h3_estimation": lignes(estimation.reset_index()),
        "h3_verdict": lignes(
            h3.verdict_h3(estimation, fiabilite.loc["ensemble", "r_spearman_brown"]).reset_index()
        ),
        "h3_robustesse": lignes(
            robustesse.robustesse_h3(base, lycees, sessions_ival).reset_index()
        ),
        "h4": lignes(h1.pentes_h4(base, paires).reset_index()),
        "robustesse": lignes(variantes.reset_index()),
        "variantes_figure": list(config.VARIANTES_FIGURE_ROBUSTESSE),
        "moran": lignes(robustesse.moran_part_cadres(base).reset_index()),
        "n_fichiers_bruts": len(pipeline.fichiers_bruts()),
    }


def _bloc(identifiant: str, objet: object) -> str:
    """Renvoie un objet en JSON dans une balise que le JavaScript de la page lit."""
    texte = json.dumps(objet, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/json" id="{identifiant}">{texte}</script>'


def main() -> None:
    """Calcule les données, assemble la page et l'écrit dans `config.CHEMIN_PRESENTATION`."""
    base, lycees, paires = pipeline.construire_base(config.AIRES_RETENUES)
    fonds = {aire: fond_ign(base[base["aire"] == aire]) for aire in config.AIRES_RETENUES}
    donnees = "\n".join(
        [
            _bloc("d-communes", communes_geojson(base)),
            _bloc("d-parts", parts_dates(base)),
            _bloc("d-resultats", resultats(base, lycees, paires)),
            _bloc("d-fonds", fonds),
        ]
    )
    gabarit = config.CHEMIN_GABARIT_PRESENTATION.read_text(encoding="utf-8")
    assert gabarit.count("<!--DONNEES-->") == 1, "Emplacement des données absent du gabarit."
    # Le gabarit est le contenu de la page : on y ajoute l'en-tête d'un document HTML complet
    page = (
        '<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "<style>body{margin:0} img{max-width:100%} [hidden]{display:none!important}</style>\n"
        + gabarit.replace("<!--DONNEES-->", donnees)
        + "\n</html>\n"
    )
    config.CHEMIN_PRESENTATION.parent.mkdir(exist_ok=True)
    config.CHEMIN_PRESENTATION.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
