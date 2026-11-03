"""Mise en forme des tableaux affichés dans le rapport : libellés en clair, unités, virgule.

Les calculs sont dans `analyse.py` ; ces fonctions ne font que présenter leurs résultats, et
`document_markdown` met en forme les documents du dépôt affichés tels quels (tableau de support,
dictionnaire, journal).
"""

from pathlib import Path

import pandas as pd
from pandas.io.formats.style import Styler

from cadres_lycees import config, figures


def _nombre(valeur: float, facteur: float = 1, signe: bool = True, decimales: int = 2) -> str:
    """Écrit un nombre à la française (virgule, vrai signe moins), à `decimales` décimales."""
    texte = f"{valeur * facteur:{'+' if signe else ''}.{decimales}f}"
    return texte.replace(".", ",").replace("-", "−")


def _estimation(ligne: pd.Series, valeur: str, facteur: float) -> str:
    """Écrit « estimation [bas ; haut] », et les tirages écartés du bootstrap s'il y en a."""
    ecartes = int(ligne["tirages_ecartes"])
    estimation = _nombre(ligne[valeur], facteur)
    if pd.isna(ligne["ic_bas"]):
        return f"{estimation} (intervalle non rapporté, {ecartes} tirages écartés)"
    texte = (
        f"{estimation} [{_nombre(ligne['ic_bas'], facteur)} ; {_nombre(ligne['ic_haut'], facteur)}]"
    )
    if ecartes:
        texte += f" ({ecartes} tirages écartés)"
    return texte


def tableau_robustesse(robustesse: pd.DataFrame) -> pd.DataFrame:
    """Met en forme le tableau de robustesse de H1 : une ligne par variante, une aire par colonne.

    Chaque case donne la pente en points, par km (ou par lycée pour les pentes secondaires), et
    son intervalle à 95 %, avec le nombre de tirages écartés s'il y en a. « — » : la variante ne
    concerne pas l'aire ; intervalle non rapporté au-delà de `config.MAX_TIRAGES_ECARTES`
    tirages écartés. `robustesse` vient de `analyse.robustesse_h1`.
    """
    cases = robustesse.apply(_estimation, axis=1, valeur="pente", facteur=100).unstack("aire")
    aires = figures.aires_ordonnees(cases.columns)
    variantes = robustesse.index.unique("variante")
    tableau = cases.reindex(index=variantes, columns=aires).fillna("—")
    unites = ["points par lycée" if "secondaire" in nom else "points par km" for nom in variantes]
    tableau.insert(0, "Unité", unites)
    return tableau.rename_axis(index=None, columns=None)


def tableau_h3(estimation: pd.DataFrame) -> Styler:
    """Met en forme les coefficients de H3 : une ligne par coefficient, une colonne par portée.

    `estimation` vient de `analyse.estimation_h3` (index portée, coefficient) ou de
    `analyse.robustesse_h3` (index variante, coefficient) : la colonne est le premier niveau.
    Points de part de cadres, 2011-2022, pour un écart-type ; intervalle à 95 %. Renvoie un
    `Styler` : son HTML garde les indices des β (β<sub>q</sub>), qu'un DataFrame échapperait.
    """
    cases = estimation.apply(_estimation, axis=1, valeur="estimation", facteur=1)
    premier = estimation.index.names[0]
    # « Ensemble » d'abord, puis les aires dans l'ordre de la charte
    portees = [p for p in estimation.index.unique(premier) if p not in config.COULEURS_AIRES]
    colonnes = portees + figures.aires_ordonnees(
        [p for p in estimation.index.unique(premier) if p in config.COULEURS_AIRES]
    )
    tableau = cases.unstack(premier).reindex(
        index=estimation.index.unique("coefficient"), columns=colonnes
    )
    tableau = tableau.rename(columns={"ensemble": "Ensemble"})
    beta = {"q": "β<sub>q</sub>", "n": "β<sub>n</sub>"}
    libelles = {
        "β_q": f'<span class="grec">{beta["q"]}</span> (qualité)',
        "β_n": f'<span class="grec">{beta["n"]}</span> (nombre)',
        "β_q − β_n": f'<span class="grec">{beta["q"]} − {beta["n"]}</span>',
    }
    return tableau.rename(index=libelles).rename_axis(index=None, columns=None).style


def tableau_acces(resume: pd.DataFrame) -> pd.DataFrame:
    """Met en forme `analyse.resume_acces` : libellés en clair et unités, une aire par colonne."""
    rayon = config.RAYON_PRINCIPAL_KM
    libelles = {
        "communes": "Communes",
        "part_exposees": f"Part des communes avec un lycée privé sous contrat à {rayon} km (%)",
        "dist_lyc_prive_min": "Distance au lycée privé sous contrat le plus proche (km, médiane)",
        "dist_lyc_public_min": "Distance au lycée public le plus proche (km, médiane)",
        "dist_gare_min": "Distance à la gare la plus proche (km, médiane)",
        "apl_mg": "APL aux médecins généralistes (consultations par an et par habitant, médiane)",
        f"n_sport_{rayon}km": f"Installations sportives à {rayon} km (médiane)",
        f"n_culture_{rayon}km": f"Équipements culturels à {rayon} km (médiane)",
    }
    tableau = resume.copy()
    tableau["part_exposees"] = tableau["part_exposees"] * 100
    tableau = tableau[list(libelles)].rename(columns=libelles).T
    # Comptes sans décimale ; parts, distances et APL à une décimale, leur précision réelle
    texte = tableau.apply(
        lambda ligne: ligne.map(
            lambda valeur: _nombre(
                valeur, signe=False, decimales=0 if (ligne % 1 == 0).all() else 1
            )
        ),
        axis=1,
    )
    return texte[figures.aires_ordonnees(texte.columns)].rename_axis(index=None, columns=None)


def tableau_fiabilite(fiabilite: pd.DataFrame) -> pd.DataFrame:
    """Met en forme `analyse.fiabilite_ival` : libellés en clair ; seule « ensemble » tranche H3."""
    libelles = {
        "r": "Corrélation des deux moitiés (r)",
        "r_spearman_brown": "Fiabilité (Spearman-Brown)",
        "n_communes_h3": "Communes de la population de H3",
        "n_communes": "Communes renseignées dans les deux moitiés",
        "n_lycees": "Lycées distincts à 5 km",
    }
    ordre = ["ensemble", *figures.aires_ordonnees(fiabilite.index.drop("ensemble"))]
    tableau = fiabilite.loc[ordre, list(libelles)].rename(columns=libelles)
    texte = tableau.map(lambda valeur: f"{valeur:.3f}".replace(".", ",").removesuffix(",000"))
    return texte.rename(index={"ensemble": "Ensemble (tranche H3)"}).rename_axis(index=None)


def tableau_moran(moran: pd.DataFrame) -> pd.DataFrame:
    """Met en forme `analyse.moran_part_cadres` : une ligne par aire, I et p-valeur par variable."""
    variables = {
        "part_cadres_2022": "part de cadres",
        "ecart_anneau": "écart à la moyenne de l'anneau",
    }
    tableau = moran[["I", "p_valeur"]].unstack("variable")
    tableau = tableau[
        [(mesure, variable) for variable in variables for mesure in ("I", "p_valeur")]
    ]
    tableau.columns = [
        f"{'I de Moran' if mesure == 'I' else 'p-valeur'}, {variables[variable]}"
        for mesure, variable in tableau.columns
    ]
    # La plus petite p-valeur possible par permutations est 1 / (permutations + 1)
    plancher = 1 / (config.NB_PERMUTATIONS_MORAN + 1)

    def case(nom: str, valeur: float) -> str:
        if nom.startswith("p-valeur") and valeur <= plancher:
            return f"< {plancher:.3f}".replace(".", ",")
        return f"{valeur:.3f}".replace(".", ",")

    texte = tableau.apply(lambda colonne: colonne.map(lambda v: case(colonne.name, v)))
    return texte.loc[figures.aires_ordonnees(texte.index)].rename_axis(index=None)


def tableau_gradient(parts: pd.DataFrame) -> pd.DataFrame:
    """Met en forme `analyse.parts_par_anneau` : une ligne par anneau, une aire par colonne.

    Chaque case donne la part de cadres de l'anneau, en %, et le nombre de communes.
    """
    cases = parts.apply(
        lambda ligne: (
            f"{_nombre(ligne['part_cadres_2022'], 100, signe=False, decimales=1)} % "
            f"({int(ligne['communes'])} communes)"
        ),
        axis=1,
    ).unstack("aire")
    return (
        cases[figures.aires_ordonnees(cases.columns)]
        .fillna("—")
        .rename_axis(index=None, columns=None)
    )


def tableau_hypotheses(verdict_h1: pd.DataFrame, verdict_h3: pd.DataFrame) -> pd.DataFrame:
    """Renvoie le tableau des hypothèses du §6 : verdicts de H1 et H3, H2 et H4 descriptives.

    `verdict_h1` et `verdict_h3` viennent de `analyse.verdict_h1` et `analyse.verdict_h3`. Les
    verdicts suivent les règles écrites avant les résultats (§5.3, §5.5) ; H2 et H4 n'en ont
    pas (§5.4, §5.7, A20).
    """
    lignes = [
        {
            "Hypothèse": "H1",
            "Portée": aire,
            "Verdict": ligne["verdict"],
            "Mention": ligne["mention"],
        }
        for aire, ligne in verdict_h1.loc[figures.aires_ordonnees(verdict_h1.index)].iterrows()
    ]
    lignes.append(
        {
            "Hypothèse": "H2",
            "Portée": "3 aires",
            "Verdict": "descriptive",
            "Mention": "une seule aire de l'Ouest : comparaison sans test",
        }
    )
    fiabilite = _nombre(verdict_h3.loc["ensemble", "fiabilite"], signe=False)
    lignes.append(
        {
            "Hypothèse": "H3",
            "Portée": "3 aires ensemble",
            "Verdict": verdict_h3.loc["ensemble", "verdict"],
            "Mention": f"fiabilité de l'IVAL {fiabilite}",
        }
    )
    lignes.append(
        {
            "Hypothèse": "H4",
            "Portée": "3 aires",
            "Verdict": "descriptive",
            "Mention": "aucune règle de verdict fixée avant l'estimation",
        }
    )
    return pd.DataFrame(lignes).set_index(["Hypothèse", "Portée"])


def document_markdown(chemin: Path, apres: str | None = None) -> str:
    """Renvoie un document Markdown du dépôt, pour l'afficher dans le rapport.

    Le texte part de la ligne qui suit `apres`, ou de la deuxième ligne (après le titre du
    document) si `apres` est absent. Les titres sont descendus de deux niveaux (`##` devient
    `####`) pour rester sous la section du rapport qui affiche le document ; une ligne qui
    commence par `#` dans un bloc de code est un commentaire et reste telle quelle.
    """
    texte = chemin.read_text(encoding="utf-8")
    if apres is None:
        corps = texte.split("\n", maxsplit=1)[1]
    else:
        assert apres in texte, f"« {apres} » absent de {chemin}."
        corps = texte.split(apres, maxsplit=1)[1]
    lignes = []
    dans_un_bloc_de_code = False
    for ligne in corps.splitlines():
        if ligne.startswith("```"):
            dans_un_bloc_de_code = not dans_un_bloc_de_code
        if ligne.startswith("#") and not dans_un_bloc_de_code:
            ligne = "##" + ligne
        lignes.append(ligne)
    return "\n".join(lignes)
