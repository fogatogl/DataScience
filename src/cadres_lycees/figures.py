"""Figures statiques du rapport (matplotlib) : une fonction par figure.

La charte commune est dans `charte.py`, les cartes interactives dans `cartes.py`.
"""

import itertools
import textwrap
from collections.abc import Collection

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from cadres_lycees import charte, config, h1


def fig_aires(
    profil: pd.DataFrame, lycees: gpd.GeoDataFrame, titre: str, aires_retenues: Collection[str]
) -> Figure:
    """Profil des aires : prévalence du privé sous contrat et composition sociale des lycées.

    À gauche, la part du privé en nombre de lycées et en candidats au bac ; à droite, l'IPS de
    chaque lycée par secteur, avec la moyenne simple du secteur et l'écart privé moins public :
    les deux dimensions du critère (b) du choix des aires. `profil` vient de
    `analyse.profil_aires`, `lycees` de `nettoyage.lycees_geo` ; `titre` est le message de la
    figure, écrit par le groupe. Les aires sont triées par écart d'IPS, le plus fort
    en haut ; celles de `aires_retenues` sont mises en avant, nom en gras sur une bande grise.
    """
    inconnues = sorted(set(aires_retenues) - set(profil.index))
    assert not inconnues, f"Aires retenues absentes du profil : {inconnues}."
    profil = profil.sort_values("ecart_ips")
    fig, (ax_part, ax_ips) = plt.subplots(
        1, 2, figsize=(14, 5.6), sharey=True, gridspec_kw={"width_ratios": [1, 1.5]}
    )
    _panneau_prevalence(ax_part, profil)
    _panneau_ips(ax_ips, profil, lycees)
    for ax in (ax_part, ax_ips):
        charte.styler_axes(ax, "x")
    # Une demi-hauteur sous 0,5 laisse un liseré blanc entre deux aires retenues voisines ; la
    # bande passe sous les points (zorder 0)
    demi_hauteur_bande = 0.45
    for position, aire in enumerate(profil.index):
        if aire in aires_retenues:
            for ax in (ax_part, ax_ips):
                ax.axhspan(
                    position - demi_hauteur_bande,
                    position + demi_hauteur_bande,
                    color=config.COULEUR_FOND_RETENUES,
                    zorder=0,
                )
            ax_part.get_yticklabels()[position].set_fontweight("bold")

    charte.habiller(
        fig,
        titre,
        "Lycées généraux, technologiques et polyvalents des communes de l'aire (annuaire du "
        f"{config.DATE_ANNUAIRE}). Candidats : présents au bac 2012-2022 des "
        f"{profil['n_avec_candidats'].sum()} lycées sur {profil['n_lycees'].sum()} qui ont une "
        f"IVAL. IPS : voie générale et technologique, rentrée {config.RENTREE_IPS}. Sources : "
        "annuaire de l'éducation, DEPP, Insee, IGN.",
    )
    return fig


def _panneau_prevalence(ax: plt.Axes, profil: pd.DataFrame) -> None:
    """`fig_aires`, gauche : part du privé en lycées et en candidats au bac, une ligne par aire."""
    positions = range(len(profil))
    couleur_prive = config.COULEURS_SECTEURS["prive"]
    en_lycees = profil["part_prive"] * 100
    en_candidats = profil["part_prive_candidats"] * 100
    ax.hlines(positions, en_lycees, en_candidats, color=config.COULEUR_LIAISON, zorder=1)
    ax.scatter(
        en_lycees,
        positions,
        s=55,
        color=couleur_prive,
        edgecolor="white",
        zorder=2,
        label="en nombre de lycées",
    )
    ax.scatter(
        en_candidats,
        positions,
        s=55,
        marker="D",
        facecolor="white",
        edgecolor=couleur_prive,
        linewidth=1.5,
        zorder=2,
        label="en candidats au bac",
    )
    ax.set_xlim(0, max(en_lycees.max(), en_candidats.max()) + 8)
    ax.set_xlabel("Part du privé sous contrat (%)", color=config.COULEUR_TEXTE)
    ax.set_title("Prévalence du privé", loc="left", fontsize=11)
    ax.set_yticks(positions)
    ax.set_yticklabels(profil.index, color=config.COULEUR_TEXTE, fontsize=11)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1, frameon=False)


def _panneau_ips(ax: plt.Axes, profil: pd.DataFrame, lycees: gpd.GeoDataFrame) -> None:
    """Panneau de droite de `fig_aires` : IPS de chaque lycée, moyenne et écart par secteur."""
    rang = {aire: position for position, aire in enumerate(profil.index)}
    avec_ips = lycees[lycees["aire"].notna() & lycees["ips"].notna()]
    assert set(avec_ips["aire"]) == set(profil.index), (
        "Les lycées et le profil n'ont pas les mêmes aires."
    )
    # Chaque secteur sur sa propre bande, de part et d'autre de la ligne de l'aire. Dans une
    # bande, les points sont décalés selon le rang de leur IPS, sur quelques niveaux : des lycées
    # d'IPS proches se recouvrent moins, et la figure est la même à chaque exécution. La hauteur
    # d'un point dans sa bande n'a pas de sens
    ecart_bande, nb_niveaux, pas_niveau = 0.17, 5, 0.03
    for secteur, bande in (("public", ecart_bande), ("prive", -ecart_bande)):
        du_secteur = avec_ips[avec_ips["secteur"] == secteur]
        niveau = du_secteur.groupby("aire")["ips"].rank(method="first") % nb_niveaux
        hauteur = du_secteur["aire"].map(rang) + bande + (niveau - nb_niveaux // 2) * pas_niveau
        couleur = config.COULEURS_SECTEURS[secteur]
        ax.scatter(
            du_secteur["ips"],
            hauteur,
            s=14,
            color=couleur,
            alpha=0.55,
            linewidth=0,
            label=f"Lycée, secteur {config.LIBELLES_SECTEURS[secteur]}",
        )
        # La moyenne tracée est celle du profil, d'où vient aussi l'écart écrit à droite
        ax.scatter(
            profil[f"ips_{secteur}"],
            [rang[aire] + bande for aire in profil.index],
            marker="|",
            s=260,
            linewidth=2.5,
            color=couleur,
            zorder=3,
        )

    bord = avec_ips["ips"].max() + 10
    for aire, ligne in zip(profil.index, profil.itertuples(), strict=True):
        ax.text(
            bord,
            rang[aire],
            f"{ligne.ecart_ips:+.0f}".replace("-", "−"),
            ha="right",
            va="center",
            fontsize=11,
            color=config.COULEUR_TEXTE,
            fontweight="bold",
        )
    ax.text(
        bord,
        len(profil) - 0.5,
        "écart privé − public",
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=config.COULEUR_TEXTE,
    )
    ax.set_xlim(avec_ips["ips"].min() - 3, bord + 1)
    ax.set_xlabel(
        f"IPS de chaque lycée, voie générale et technologique, rentrée {config.RENTREE_IPS}",
        color=config.COULEUR_TEXTE,
    )
    ax.set_title("Composition sociale des lycées", loc="left", fontsize=11)
    trait_moyenne = Line2D(
        [],
        [],
        color=config.COULEUR_TEXTE,
        marker="|",
        linestyle="",
        markersize=12,
        markeredgewidth=2.5,
        label="moyenne simple du secteur",
    )
    points, libelles = ax.get_legend_handles_labels()
    ax.legend(
        [*points, trait_moyenne],
        [*libelles, trait_moyenne.get_label()],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=2,
        frameon=False,
    )


def _libelle_cellule(bas_km: float, haut_km: float, rayon_km: int) -> str:
    """Nomme une cellule d'anneaux par ses bornes et son rayon : « 20-30 km, rayon 5 km »."""
    bornes = (
        f"{bas_km:.0f} km et plus" if haut_km == float("inf") else f"{bas_km:.0f}-{haut_km:.0f} km"
    )
    return f"{bornes}, rayon {rayon_km} km"


def fig_h1(
    principale: pd.DataFrame, secondaire: pd.DataFrame, anneaux: pd.DataFrame, titre: str
) -> Figure:
    """`fig_h1` : estimations de H1 par aire, en points avec leurs intervalles à 95 %.

    Trois panneaux à axes propres, les aires sur la même ligne de l'un à l'autre (H2) :
    pente principale et pente secondaire des paires (`h1.pentes_paires_par_aire`), écarts
    des cellules estimables à 5 et à 10 km (`h1.ecarts_anneaux`), chacune nommée par ses
    bornes. Les cellules non estimables sont nommées en note. `titre` est le message de la
    figure, écrit par le groupe.
    """
    aires = charte.aires_ordonnees(principale.index)
    assert set(secondaire.index) == set(aires), "Les deux pentes n'ont pas les mêmes aires."
    texte = config.COULEUR_TEXTE
    # La première aire en haut
    rang = {aire: len(aires) - 1 - k for k, aire in enumerate(aires)}
    estimables = anneaux[anneaux["estimable"]]
    marqueurs = {5: "o", 10: "s"}

    fig, axes = plt.subplots(1, 3, figsize=(12, 1.8 + 1.3 * len(aires)), sharey=True)
    panneaux = [
        (axes[0], "Pente principale", "points par km de distance au lycée privé le plus proche"),
        (axes[1], "Pente secondaire", "points par lycée privé de plus à 5 km"),
        (axes[2], "Écarts des cellules d'anneaux", "points, communes exposées moins non exposées"),
    ]
    for ax, pentes in ((axes[0], principale), (axes[1], secondaire)):
        for aire in aires:
            ligne = pentes.loc[aire]
            couleur = config.COULEURS_AIRES[aire]
            ax.hlines(rang[aire], ligne["ic_bas"] * 100, ligne["ic_haut"] * 100, color=couleur)
            ax.scatter(ligne["pente"] * 100, rang[aire], s=45, color=couleur, zorder=3)
    ax = axes[2]
    for aire in aires:
        cellules = estimables[estimables["aire"] == aire].reset_index(drop=True)
        couleur = config.COULEURS_AIRES[aire]
        for k, cellule in cellules.iterrows():
            # Les cellules d'une aire sont réparties autour de sa ligne, sans se recouvrir
            y = rang[aire] + 0.18 * ((len(cellules) - 1) / 2 - k)
            ax.hlines(y, cellule["ic_bas"] * 100, cellule["ic_haut"] * 100, color=couleur)
            ax.scatter(
                cellule["ecart"] * 100,
                y,
                s=40,
                marker=marqueurs[cellule["rayon_km"]],
                color=couleur,
                zorder=3,
            )
            ax.annotate(
                _libelle_cellule(cellule["bas_km"], cellule["haut_km"], cellule["rayon_km"]),
                (cellule["ic_haut"] * 100, y),
                xytext=(4, 0),
                textcoords="offset points",
                va="center",
                fontsize=9,
                color=texte,
            )
    for ax, nom, unite in panneaux:
        ax.axvline(0, color=config.COULEUR_LIAISON, linewidth=1, zorder=0)
        ax.set_title(nom, loc="left", fontsize=11, color=texte)
        ax.set_xlabel(unite, color=texte, fontsize=9)
        charte.styler_axes(ax, "x", axe_y=False)
    axes[0].set_yticks([rang[aire] for aire in aires])
    axes[0].set_yticklabels(aires, color=texte)
    axes[0].set_ylim(-0.6, len(aires) - 0.4)
    # Place à droite pour les noms des cellules, sans graduation ni axe au-delà des intervalles
    gauche, droite = axes[2].get_xlim()
    graduations = [x for x in axes[2].get_xticks() if gauche <= x <= droite]
    axes[2].set_xlim(gauche, droite + 0.6 * (droite - gauche))
    axes[2].set_xticks(graduations)
    axes[2].spines["bottom"].set_bounds(gauche, droite)

    non_estimables = anneaux[~anneaux["estimable"]]
    noms = [
        f"{ligne.aire} ({_libelle_cellule(ligne.bas_km, ligne.haut_km, ligne.rayon_km)})"
        for ligne in non_estimables.itertuples()
    ]
    charte.habiller(
        fig,
        titre,
        "Sens de H1 : pente principale négative, pente secondaire et écarts positifs. Pentes des "
        "paires de communes contiguës sans constante, à écarts de distance au centre et de "
        "log-densité donnés ;\nécarts des cellules : régression pondérée par les actifs, à "
        "distance au centre et log-densité données (rond : rayon de 5 km, carré : 10 km). "
        f"Intervalles à 95 % par bootstrap ({config.NB_TIRAGES_BOOTSTRAP} tirages).\n"
        f"Cellules non estimables : {', '.join(noms)}.\nSources : Insee, recensement 2022, "
        f"« Évolution et structure de la population » ; annuaire de l'éducation "
        f"({config.DATE_ANNUAIRE}) ; IGN.",
    )
    return fig


def fig_paires(paires: pd.DataFrame, pentes: pd.DataFrame, titre: str) -> Figure:
    """`fig_paires` : écart de part de cadres et écart de distance au lycée privé dans les paires.

    Un panneau par aire : le nuage par classes de `h1.nuage_paires` et la droite de pente
    principale de H1, sans constante, avec son intervalle à 95 %. `paires` vient de
    `pipeline.construire_base`, `pentes` de `h1.pentes_paires_par_aire(paires,
    "d_dist_lyc_prive_min")` ; `titre` est le message de la figure, écrit par le groupe.
    """
    acces = "d_dist_lyc_prive_min"
    aires = charte.aires_ordonnees(paires["aire"])
    assert set(pentes.index) == set(aires), "Les pentes et les paires n'ont pas les mêmes aires."
    texte = config.COULEUR_TEXTE

    fig, axes = plt.subplots(1, len(aires), figsize=(14, 5.4), sharey=True, squeeze=False)
    for ax, aire in zip(axes[0], aires, strict=True):
        couleur = config.COULEURS_AIRES[aire]
        nuage = h1.nuage_paires(paires[paires["aire"] == aire], acces)
        ligne = pentes.loc[aire]
        ax.axhline(0, color=config.COULEUR_LIAISON, linewidth=0.8, zorder=0)
        ax.axvline(0, color=config.COULEUR_LIAISON, linewidth=0.8, zorder=0)
        ax.scatter(
            nuage["acces_residuel"],
            nuage["cadres_residuel"] * 100,
            s=28,
            color=couleur,
            edgecolor="white",
            zorder=2,
        )
        bornes_x = [nuage["acces_residuel"].min(), nuage["acces_residuel"].max()]
        # Éventail des droites dont la pente parcourt l'intervalle à 95 %
        x = np.linspace(*bornes_x, 50)
        ax.fill_between(
            x,
            ligne["ic_bas"] * 100 * x,
            ligne["ic_haut"] * 100 * x,
            color=couleur,
            alpha=0.15,
            linewidth=0,
            zorder=0,
        )
        ax.plot(
            bornes_x,
            [ligne["pente"] * 100 * x for x in bornes_x],
            color=couleur,
            linewidth=1.8,
            zorder=1,
        )
        pente, bas, haut = (
            f"{ligne[cle] * 100:+.2f}".replace(".", ",").replace("-", "−")
            for cle in ("pente", "ic_bas", "ic_haut")
        )
        # La pente va au-dessus du panneau : dedans, elle pourrait cacher des points
        ax.set_title(aire, loc="left", fontsize=12, color=couleur, fontweight="bold", pad=22)
        ax.text(
            0,
            1.02,
            f"pente {pente} point par km [{bas} ; {haut}]",
            transform=ax.transAxes,
            va="bottom",
            fontsize=10,
            color=texte,
        )
        ax.set_xlabel(
            "Écart de distance au lycée privé le plus proche,\nà position égale (km)", color=texte
        )
        charte.styler_axes(ax, "both")
    axes[0][0].set_ylabel(
        "Écart de part de cadres en 2022,\nà position égale (points)", color=texte
    )

    effectifs = ", ".join(
        f"{aire} {pentes.loc[aire, 'n_paires']:.0f} ({pentes.loc[aire, 'n_communes']:.0f} communes)"
        for aire in aires
    )
    charte.habiller(
        fig,
        titre,
        f"Paires de communes contiguës d'une même aire : {effectifs}, chacune comptée dans les "
        "deux sens. Les deux écarts sont pris à écarts de distance au centre et de log-densité "
        "donnés (résidus des régressions sur ces contrôles, sans constante) ; chaque point est la "
        f"moyenne d'une des {config.NB_CLASSES_NUAGE_PAIRES} classes d'effectifs égaux de l'écart "
        "de distance. Droite : pente principale de H1 ; intervalle à 95\u00a0% par bootstrap des "
        f"communes ({config.NB_TIRAGES_BOOTSTRAP} tirages). Sources : Insee, recensement 2022 ; "
        f"annuaire de l'éducation ({config.DATE_ANNUAIRE}) ; IGN.",
    )
    return fig


def fig_h3(terciles: pd.DataFrame, titre: str) -> Figure:
    """`fig_h3` : évolution de la part de cadres par tiers d'IVAL de chaque aire (H3).

    Un point par aire et par catégorie (`config.CATEGORIES_TIERS_IVAL`), avec son intervalle à 95 %
    par bootstrap des grappes ; la catégorie « sans IVAL » est à part. `terciles` vient de
    `h3.terciles_h3`, dont les tirages écartés sont nommés en note ; `titre` est le message
    de la figure, écrit par le groupe. Elle décrit : le verdict de H3 se lit sur β_q
    et β_n.
    """
    aires = charte.aires_ordonnees(terciles.index.get_level_values("aire"))
    texte = config.COULEUR_TEXTE
    decalages = {aire: 0.22 * (k - (len(aires) - 1) / 2) for k, aire in enumerate(aires)}
    # La catégorie « sans IVAL » est séparée des tiers par un intervalle plus large
    positions = {categorie: k for k, categorie in enumerate(config.CATEGORIES_TIERS_IVAL[:3])}
    positions[config.CATEGORIES_TIERS_IVAL[3]] = 3.6

    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.axvline(3.3, color=config.COULEUR_LIAISON, linewidth=1, linestyle=":")
    for aire in aires:
        couleur = config.COULEURS_AIRES[aire]
        for k, (categorie, ligne) in enumerate(terciles.loc[aire].iterrows()):
            x = positions[categorie] + decalages[aire]
            ax.vlines(x, ligne["ic_bas"], ligne["ic_haut"], color=couleur, linewidth=2)
            ax.scatter(
                x,
                ligne["moyenne"],
                s=45,
                color=couleur,
                edgecolor="white",
                zorder=3,
                label=aire if k == 0 else None,
            )
            ax.annotate(
                f"{int(ligne['n_communes'])}",
                (x, ligne["ic_bas"]),
                xytext=(0, -10),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                color=texte,
            )
    ax.set_xticks(list(positions.values()))
    ax.set_xticklabels(list(positions), color=texte)
    ax.set_xlabel("IVAL moyenne des lycées à 5 km, en tiers calculés dans chaque aire", color=texte)
    ax.set_ylabel("Évolution 2011-2022 (points)", color=texte)
    # Place sous les intervalles pour le nombre de communes
    ax.set_ylim(terciles["ic_bas"].min() - 1, None)
    charte.styler_axes(ax, "y")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    ecartes = terciles[terciles["tirages_ecartes"] > 0]
    noms_ecartes = ", ".join(
        f"{aire} {categorie} {int(ligne['tirages_ecartes'])}"
        for (aire, categorie), ligne in ecartes.iterrows()
    )
    charte.habiller(
        fig,
        titre,
        "Communes ayant au moins un lycée retenu à 5 km ; « sans IVAL » : aucun de ces lycées n'a "
        "d'IVAL. Moyennes simples ; sous chaque point, le nombre de communes : sous 10 communes, "
        "l'intervalle est peu informatif.\nIntervalles à 95 % "
        "par bootstrap des grappes « lycée avec IVAL le plus proche », tirées dans chaque aire "
        f"({config.NB_TIRAGES_BOOTSTRAP} tirages) ;\ntirages sans commune de la catégorie, écartés "
        f"pour elle : {noms_ecartes or 'aucun'}.\nIVAL : valeur ajoutée du taux d'accès de la "
        "seconde au bac, moyenne des sessions 2012 à 2022, lycées d'au moins 5 sessions.\n"
        "Sources : Insee, recensements 2011 et 2022, « Évolution et structure de la population » ; "
        f"DEPP, IVAL ; annuaire de l'éducation ({config.DATE_ANNUAIRE}) ; IGN.",
    )
    return fig


def fig_robustesse(robustesse: pd.DataFrame, titre: str) -> Figure:
    """Pente principale de H1 dans les variantes de robustesse principales, par aire.

    Une ligne par variante de `config.VARIANTES_FIGURE_ROBUSTESSE`, un point par aire avec son
    intervalle à 95 % ; la spécification principale, en haut sur fond gris, sert de repère. Les
    autres variantes restent dans le tableau détaillé. `robustesse` vient de
    `robustesse.robustesse_h1` ; `titre` est le message de la figure.
    """
    variantes = list(config.VARIANTES_FIGURE_ROBUSTESSE)
    absentes = sorted(set(variantes) - set(robustesse.index.unique("variante")))
    assert not absentes, f"Variantes absentes de la robustesse : {absentes}."
    choisies = robustesse.loc[variantes]
    aires = charte.aires_ordonnees(choisies.index.get_level_values("aire"))
    texte = config.COULEUR_TEXTE
    decalages = {aire: 0.2 * (k - (len(aires) - 1) / 2) for k, aire in enumerate(aires)}

    fig, ax = plt.subplots(figsize=(10, 1.8 + 1.0 * len(variantes)))
    ax.axhspan(-0.45, 0.45, color=config.COULEUR_FOND_RETENUES, zorder=0)
    ax.axvline(0, color=config.COULEUR_LIAISON, linewidth=1.2, zorder=0)
    for rang, variante in enumerate(variantes):
        for aire in aires:
            if (variante, aire) not in choisies.index:
                continue
            ligne = choisies.loc[(variante, aire)]
            y = rang + decalages[aire]
            couleur = config.COULEURS_AIRES[aire]
            if pd.notna(ligne["ic_bas"]):
                ax.hlines(y, ligne["ic_bas"] * 100, ligne["ic_haut"] * 100, color=couleur, lw=3)
            ax.scatter(
                ligne["pente"] * 100,
                y,
                s=70,
                color=couleur,
                edgecolor="white",
                zorder=3,
                label=aire if rang == 0 else None,
            )
    ax.set_yticks(range(len(variantes)))
    ax.set_yticklabels([textwrap.fill(nom, 31) for nom in variantes], color=texte, fontsize=13)
    ax.invert_yaxis()
    ax.set_xlabel(
        "Points de part de cadres par km de distance au lycée privé", color=texte, fontsize=13
    )
    charte.styler_axes(ax, "x", axe_y=False)
    ax.tick_params(labelsize=12)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=13)
    charte.habiller(
        fig,
        titre,
        "Sens de H1 : pente négative. Même estimation et même bootstrap que la spécification "
        f"principale ({config.NB_TIRAGES_BOOTSTRAP} tirages par commune). Prix au m² : Lyon et "
        "Nantes seulement (Alsace-Moselle hors DVF). Toutes les variantes sont dans le tableau "
        "détaillé. Sources : Insee, recensement 2022 ; annuaire de l'éducation ; DVF ; IGN.",
    )
    return fig


def fig_h4(pentes: pd.DataFrame, titre: str) -> Figure:
    """`fig_h4` : association de la part de cadres avec l'accès à chaque infrastructure (H4).

    Une ligne par mesure d'accès, de la plus forte à la plus faible association (moyenne des
    pentes des aires), un point par aire avec son intervalle à 95 %. `pentes` vient de
    `h1.pentes_h4` ; `titre` est le message de la figure, écrit par le groupe.
    """
    aires = charte.aires_ordonnees(pentes.index.get_level_values("aire"))
    ordre = pentes["pente"].groupby(level="mesure").mean().sort_values().index
    texte = config.COULEUR_TEXTE
    # Les aires sont décalées verticalement dans chaque ligne, pour que leurs intervalles ne se
    # recouvrent pas ; la première en haut, comme dans la légende
    decalages = {aire: -0.22 * (k - (len(aires) - 1) / 2) for k, aire in enumerate(aires)}

    fig, ax = plt.subplots(figsize=(11, 1.4 + 1.3 * len(ordre)))
    ax.axvline(0, color=config.COULEUR_LIAISON, linewidth=1, zorder=0)
    for position, mesure in enumerate(ordre):
        for aire in aires:
            ligne = pentes.loc[(mesure, aire)]
            y = position + decalages[aire]
            couleur = config.COULEURS_AIRES[aire]
            ax.hlines(y, ligne["ic_bas"] * 100, ligne["ic_haut"] * 100, color=couleur, linewidth=2)
            ax.scatter(
                ligne["pente"] * 100,
                y,
                s=45,
                color=couleur,
                edgecolor="white",
                zorder=3,
                label=aire if position == 0 else None,
            )
    ax.set_yticks(range(len(ordre)))
    ax.set_yticklabels(ordre, color=texte)
    ax.set_xlabel(
        "Écart de part de cadres en 2022 entre deux communes voisines pour un écart-type d'accès "
        "en plus (points)",
        color=texte,
    )
    charte.styler_axes(ax, "x", axe_y=False)
    # Légende dans l'ordre des aires de la charte, en dehors des points
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    charte.habiller(
        fig,
        titre,
        "Pente des paires de communes contiguës, sans constante, à écarts de distance au centre "
        "et de log-densité donnés.\nMesures d'accès centrées réduites dans chaque aire et "
        "orientées pour qu'une valeur positive dise « plus d'accès, plus de cadres » (distances "
        "retournées).\nIntervalles à 95 % par bootstrap des communes "
        f"({config.NB_TIRAGES_BOOTSTRAP} tirages, les mêmes pour toutes les mesures).\n"
        "Sources : Insee, recensement 2022 et BPE 2025 ; annuaire de l'éducation "
        f"({config.DATE_ANNUAIRE}) ; SNCF Gares & Connexions ; ministère des Sports (Data ES) ;\n"
        "copies du 03/11/2026 pour la BPE, les gares et Data ES ; DREES, APL 2024 ; IGN.",
    )
    return fig


def carte_iris(
    contours: gpd.GeoDataFrame, parts: pd.DataFrame, code_centre: str, titre: str
) -> Figure:
    """Carte statique de la part de cadres par IRIS d'une aire, en 2011 puis en 2022.

    `contours` vient de `collecte.contours_iris`, `parts` de `nettoyage.part_cadres_iris`. En haut,
    l'aire entière ; en bas, un zoom sur un carré de `config.ZOOM_IRIS_KM` km de demi-côté autour
    du centroïde de la commune-centre `code_centre` (Lyon : 69123, ses arrondissements réunis),
    où ses IRIS deviennent lisibles. Les quatre panneaux ont les mêmes classes ; les IRIS non
    comparables (code ou territoire changé depuis 2011) sont hachurés en gris. C'est une
    exploration : ni lycées ni test. `titre` est le message de la carte, écrit par le
    groupe.
    """
    codes = contours["CODE_IRIS"].replace(config.IRIS_RECODES_2025_2024)
    # Dans les deux sens : un IRIS de 2022 sans contour disparaîtrait de la carte sans signal
    communes = codes.str[:5].unique()
    donnees = parts.index[parts.index.str[:5].isin(communes)]
    ecart = sorted(set(codes) ^ set(donnees))
    assert not ecart, (
        f"IRIS présents dans les contours ou dans les données de 2022 seulement : {ecart}"
    )
    carte = contours.to_crs(config.CRS_CALCUL).assign(iris=codes.to_numpy())
    carte = carte.join(parts, on="iris", validate="one_to_one")
    comparables = carte[carte["comparable"]]
    autres = carte[~carte["comparable"]]
    commune_centre = carte[carte["INSEE_COM"] == code_centre]
    assert not commune_centre.empty, f"Commune-centre {code_centre} absente des contours."
    centre = commune_centre.union_all().centroid

    bornes = [0, *config.BORNES_PART_CADRES_IRIS, 100]
    demi_cote = config.ZOOM_IRIS_KM * 1000
    ouest, sud = centre.x - demi_cote, centre.y - demi_cote
    # La légende a sa propre rangée sous les cartes : à côté, elle chevaucherait les titres
    fig, axes = plt.subplots(3, 2, figsize=(9, 10), gridspec_kw={"height_ratios": [1, 1, 0.16]})
    for colonne, annee in enumerate((2011, 2022)):
        # Borne basse incluse, comme dans la légende
        classe = pd.cut(
            comparables[f"part_cadres_1564_{annee}"] * 100, bornes, right=False, labels=False
        )
        assert classe.notna().all(), f"Part manquante ou hors des classes en {annee}."
        couleurs = [config.COULEURS_PART_CADRES_IRIS[int(rang)] for rang in classe]
        ax_aire, ax_zoom = axes[0, colonne], axes[1, colonne]
        for ax, epaisseur in ((ax_aire, 0.2), (ax_zoom, 0.6)):
            # Les hachures prennent la couleur du trait : un gris foncé les rend lisibles
            autres.plot(
                ax=ax,
                color=config.COULEUR_IRIS_NON_COMPARABLE,
                hatch="////",
                edgecolor=config.COULEUR_TEXTE,
                linewidth=epaisseur,
            )
            comparables.plot(ax=ax, color=couleurs, edgecolor="white", linewidth=epaisseur)
            ax.set_axis_off()
        ax_aire.add_patch(
            Rectangle(
                (ouest, sud),
                2 * demi_cote,
                2 * demi_cote,
                fill=False,
                edgecolor=config.COULEUR_TEXTE,
                linewidth=1,
            )
        )
        ax_zoom.set_xlim(ouest, ouest + 2 * demi_cote)
        ax_zoom.set_ylim(sud, sud + 2 * demi_cote)
        ax_aire.set_title(f"{annee}, aire entière", loc="left", fontsize=11)
        ax_zoom.set_title(f"{annee}, zoom sur le centre", loc="left", fontsize=11)

    libelles = [f"moins de {bornes[1]} %"]
    libelles += [f"{bas} à {haut} %" for bas, haut in itertools.pairwise(bornes[1:-1])]
    libelles.append(f"{bornes[-2]} % ou plus")
    poignees = [
        Patch(facecolor=couleur, edgecolor="white", label=libelle)
        for couleur, libelle in zip(config.COULEURS_PART_CADRES_IRIS, libelles, strict=True)
    ]
    poignees.append(
        Patch(
            facecolor=config.COULEUR_IRIS_NON_COMPARABLE,
            hatch="////",
            edgecolor=config.COULEUR_TEXTE,
            label="IRIS non comparable",
        )
    )
    grille = axes[0, 0].get_gridspec()
    for ax in axes[2]:
        ax.remove()
    ax_legende = fig.add_subplot(grille[2, :])
    ax_legende.set_axis_off()
    ax_legende.legend(handles=poignees, loc="center", ncol=4, frameon=False, fontsize=10)
    charte.habiller(
        fig,
        titre,
        "Part des cadres parmi les actifs de 15 à 64 ans (les bases IRIS ne croisent pas les "
        f"25-54 ans avec la catégorie socioprofessionnelle). Zoom : carré de "
        f"{2 * config.ZOOM_IRIS_KM} km de côté autour de la commune-centre. Non comparable : "
        "code absent en 2011, aucun actif ou territoire agrandi depuis. Part peu précise sous 200 "
        "actifs. Sources : Insee, recensements 2011 et 2022 ; IGN.",
        haut=0.97,
    )
    return fig
