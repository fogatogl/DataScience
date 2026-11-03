"""Figures statiques du rapport (matplotlib) : une fonction par figure, avec une charte commune.

Les cartes interactives sont dans `cartes.py`, la mise en forme des tableaux dans `tableaux.py`.
"""

import itertools
from collections.abc import Collection

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, ScalarFormatter

from cadres_lycees import analyse, config


def fig1(
    profil: pd.DataFrame, lycees: gpd.GeoDataFrame, titre: str, aires_retenues: Collection[str]
) -> Figure:
    """Fig. 1 : pour chaque aire, la prévalence du privé sous contrat et la composition sociale.

    À gauche, la part du privé en nombre de lycées et en candidats au bac ; à droite, l'IPS de
    chaque lycée par secteur, avec la moyenne simple du secteur et l'écart privé moins public :
    les deux dimensions du critère (b) du choix des aires (PLAN §2.2, §5.1). `profil` vient de
    `analyse.profil_aires`, `lycees` de `nettoyage.lycees_geo` ; `titre` est le message de la
    figure, écrit par le groupe (PLAN §6). Les aires sont triées par écart d'IPS, le plus fort
    en haut ; celles de `aires_retenues` sont mises en avant, nom en gras sur une bande grise.
    """
    inconnues = sorted(set(aires_retenues) - set(profil.index))
    assert not inconnues, f"Aires retenues absentes du profil : {inconnues}."
    profil = profil.sort_values("ecart_ips")
    texte = config.COULEUR_TEXTE
    fig, (ax_part, ax_ips) = plt.subplots(
        1, 2, figsize=(14, 6.2), sharey=True, gridspec_kw={"width_ratios": [1, 1.5]}
    )
    _panneau_prevalence(ax_part, profil)
    _panneau_ips(ax_ips, profil, lycees)
    for ax in (ax_part, ax_ips):
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=texte)
        ax.grid(axis="x", color=config.COULEUR_GRILLE, linewidth=0.8)
        ax.set_axisbelow(True)
    # Les aires occupent les positions 0, 1, 2... dans l'ordre du profil trié, sur les deux
    # panneaux. Une demi-hauteur un peu sous 0,5 laisse un liseré blanc entre deux aires retenues
    # voisines. La bande passe sous tout le reste (zorder 0) : tracée après les points, elle les
    # cacherait
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

    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    n_lycees = profil["n_lycees"].sum()
    n_sans_ips = n_lycees - profil[["n_ips_public", "n_ips_prive"]].sum().sum()
    fig.text(
        0.01,
        0.01,
        "Lycées généraux, technologiques et polyvalents, publics et privés sous contrat, des "
        f"communes de l'aire (annuaire du {config.DATE_ANNUAIRE}). Part en lycées : tous les "
        f"lycées ; part en candidats : présents au bac général et technologique, moyenne "
        f"2012-2022,\npour les {profil['n_avec_candidats'].sum()} lycées sur {n_lycees} qui ont "
        "une IVAL (ce n'est pas une part d'élèves au sens de la DEPP). IPS : voie générale et "
        f"technologique, rentrée {config.RENTREE_IPS}, moyenne simple des lycées, "
        f"{n_sans_ips} lycées sans IPS. En gras sur fond gris : les aires retenues.\n"
        "Sources : annuaire de l'éducation, DEPP (IPS, IVAL), Insee (aires d'attraction des "
        "villes 2020), IGN.",
        fontsize=8,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    # Fermée, la figure n'est affichée qu'une fois par un notebook, avec sa valeur de retour
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig


def _panneau_prevalence(ax: plt.Axes, profil: pd.DataFrame) -> None:
    """Fig. 1, gauche : part du privé en lycées et en candidats au bac, une ligne par aire."""
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
    ax.set_yticklabels(
        [
            f"{aire}\n{ligne.n_lycees} lycées, {ligne.n_avec_candidats} avec IVAL"
            for aire, ligne in zip(profil.index, profil.itertuples(), strict=True)
        ],
        color=config.COULEUR_TEXTE,
        fontsize=9,
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False)


def _panneau_ips(ax: plt.Axes, profil: pd.DataFrame, lycees: gpd.GeoDataFrame) -> None:
    """Fig. 1, droite : IPS de chaque lycée par secteur, moyenne du secteur et écart, par aire."""
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
            rang[aire] + 0.1,
            f"{ligne.ecart_ips:+.0f}",
            ha="right",
            fontsize=10,
            color=config.COULEUR_TEXTE,
            fontweight="bold",
        )
        ax.text(
            bord,
            rang[aire] - 0.1,
            f"{ligne.n_ips_prive} / {ligne.n_ips_public}",
            ha="right",
            va="top",
            fontsize=7,
            color=config.COULEUR_TEXTE,
        )
    ax.text(
        bord,
        len(profil) - 0.45,
        "écart privé − public\nlycées privés / publics",
        ha="right",
        va="bottom",
        fontsize=8,
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
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        frameon=False,
    )


def _axes_a_la_francaise(fig: Figure) -> None:
    """Écrit les graduations numériques avec une virgule décimale et un vrai signe moins.

    Seuls les axes à graduations calculées (`ScalarFormatter`) changent : les axes à libellés
    (aires, variantes) gardent leurs noms.
    """
    francais = FuncFormatter(lambda valeur, _: f"{valeur:g}".replace(".", ",").replace("-", "−"))
    for ax in fig.axes:
        for axe in (ax.xaxis, ax.yaxis):
            if isinstance(axe.get_major_formatter(), ScalarFormatter):
                axe.set_major_formatter(francais)


def aires_ordonnees(aires: Collection[str]) -> list[str]:
    """Renvoie les aires présentes dans l'ordre de `config.COULEURS_AIRES`.

    Échoue si une aire n'a pas de couleur : sinon elle disparaîtrait de la figure sans signal.
    """
    presentes = set(aires)
    inconnues = sorted(presentes - set(config.COULEURS_AIRES))
    assert not inconnues, f"Aires sans couleur dans config.COULEURS_AIRES : {inconnues}."
    return [aire for aire in config.COULEURS_AIRES if aire in presentes]


def _libelle_cellule(bas_km: float, haut_km: float, rayon_km: int) -> str:
    """Nomme une cellule d'anneaux par ses bornes et son rayon : « 20-30 km, rayon 5 km »."""
    bornes = (
        f"{bas_km:.0f} km et plus" if haut_km == float("inf") else f"{bas_km:.0f}-{haut_km:.0f} km"
    )
    return f"{bornes}, rayon {rayon_km} km"


def fig4(
    principale: pd.DataFrame, secondaire: pd.DataFrame, anneaux: pd.DataFrame, titre: str
) -> Figure:
    """Fig. 4 : estimations de H1 par aire, en points avec leurs intervalles à 95 % (§5.2).

    Trois panneaux à axes propres, les aires sur la même ligne de l'un à l'autre (H2, §5.4) :
    pente principale et pente secondaire des paires (`analyse.pentes_paires_par_aire`), écarts
    des cellules estimables à 5 et à 10 km (`analyse.ecarts_anneaux`), chacune nommée par ses
    bornes. Les cellules non estimables sont nommées en note. `titre` est le message de la
    figure, écrit par le groupe (PLAN §6).
    """
    aires = aires_ordonnees(principale.index)
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
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(colors=texte)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=config.COULEUR_GRILLE, linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_yticks([rang[aire] for aire in aires])
    axes[0].set_yticklabels(aires, color=texte)
    axes[0].set_ylim(-0.6, len(aires) - 0.4)
    # Place à droite pour les noms des cellules
    gauche, droite = axes[2].get_xlim()
    axes[2].set_xlim(gauche, droite + 0.6 * (droite - gauche))

    non_estimables = anneaux[~anneaux["estimable"]]
    noms = [
        f"{ligne.aire} ({_libelle_cellule(ligne.bas_km, ligne.haut_km, ligne.rayon_km)})"
        for ligne in non_estimables.itertuples()
    ]
    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(
        0.01,
        0.01,
        "Sens de H1 : pente principale négative, pente secondaire et écarts positifs. Pentes des "
        "paires de communes contiguës sans constante, à écarts de distance au centre et de "
        "log-densité donnés ;\nécarts des cellules : régression pondérée par les actifs, à "
        "distance au centre et log-densité données (rond : rayon de 5 km, carré : 10 km). "
        f"Intervalles à 95 % par bootstrap ({config.NB_TIRAGES_BOOTSTRAP} tirages).\n"
        f"Cellules non estimables : {', '.join(noms)}.\nSources : Insee, recensement 2022, "
        f"« Évolution et structure de la population » ; annuaire de l'éducation "
        f"({config.DATE_ANNUAIRE}) ; IGN.",
        fontsize=9,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.16, 1, 0.95))
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig


def fig5(paires: pd.DataFrame, pentes: pd.DataFrame, titre: str) -> Figure:
    """Fig. 5 : écart de part de cadres et écart de distance au lycée privé dans les paires.

    Un panneau par aire : le nuage par classes de `analyse.nuage_paires` et la droite de pente
    principale de H1, sans constante, avec son intervalle à 95 % (§5.3). `paires` vient de
    `pipeline.construire_base`, `pentes` de `analyse.pentes_paires_par_aire(paires,
    "d_dist_lyc_prive_min")` ; `titre` est le message de la figure, écrit par le groupe (PLAN §6).
    """
    acces = "d_dist_lyc_prive_min"
    aires = aires_ordonnees(paires["aire"])
    assert set(pentes.index) == set(aires), "Les pentes et les paires n'ont pas les mêmes aires."
    texte = config.COULEUR_TEXTE

    fig, axes = plt.subplots(1, len(aires), figsize=(14, 5.4), sharey=True, squeeze=False)
    for ax, aire in zip(axes[0], aires, strict=True):
        couleur = config.COULEURS_AIRES[aire]
        nuage = analyse.nuage_paires(paires[paires["aire"] == aire], acces)
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
            f"{ligne[cle] * 100:+.2f}".replace(".", ",") for cle in ("pente", "ic_bas", "ic_haut")
        )
        # Les statistiques vont au-dessus du panneau : dedans, elles pourraient cacher des points
        ax.set_title(aire, loc="left", fontsize=11, color=couleur, fontweight="bold", pad=34)
        ax.text(
            0,
            1.02,
            f"pente : {pente} point par km, intervalle à 95 % : [{bas} ; {haut}]\n"
            f"{int(ligne['n_paires'])} paires, {int(ligne['n_communes'])} communes",
            transform=ax.transAxes,
            va="bottom",
            fontsize=8.5,
            color=texte,
        )
        ax.set_xlabel(
            "Écart de distance au lycée privé le plus proche,\nà position égale (km)", color=texte
        )
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=texte)
        ax.grid(color=config.COULEUR_GRILLE, linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0][0].set_ylabel(
        "Écart de part de cadres en 2022,\nà position égale (points)", color=texte
    )

    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(
        0.01,
        0.01,
        "Paires de communes contiguës d'une même aire, chacune comptée dans les deux sens. Les "
        "deux écarts sont pris à écarts de distance au centre et de log-densité donnés (résidus "
        "des régressions sur ces\ncontrôles, sans constante) ; chaque point est la moyenne d'une "
        f"des {config.NB_CLASSES_FIG5} classes d'effectifs égaux de l'écart de distance. Droite : "
        "pente principale de H1 ; intervalle par bootstrap des communes "
        f"({config.NB_TIRAGES_BOOTSTRAP} tirages).\nSources : Insee, recensement 2022, "
        f"« Évolution et structure de la population » ; annuaire de l'éducation "
        f"({config.DATE_ANNUAIRE}) ; IGN.",
        fontsize=8,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.1, 1, 0.94))
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig


def fig6(terciles: pd.DataFrame, titre: str) -> Figure:
    """Fig. 6 : évolution de la part de cadres par tiers d'IVAL de chaque aire (H3, §5.5).

    Un point par aire et par catégorie (`config.CATEGORIES_FIG6`), avec son intervalle à 95 %
    par bootstrap des grappes ; la catégorie « sans IVAL » est à part. `terciles` vient de
    `analyse.terciles_h3`, dont les tirages écartés sont nommés en note ; `titre` est le message
    de la figure, écrit par le groupe (PLAN §6). Elle décrit : le verdict de H3 se lit sur β_q
    et β_n.
    """
    aires = aires_ordonnees(terciles.index.get_level_values("aire"))
    texte = config.COULEUR_TEXTE
    decalages = {aire: 0.22 * (k - (len(aires) - 1) / 2) for k, aire in enumerate(aires)}
    # La catégorie « sans IVAL » est séparée des tiers par un intervalle plus large
    positions = {categorie: k for k, categorie in enumerate(config.CATEGORIES_FIG6[:3])}
    positions[config.CATEGORIES_FIG6[3]] = 3.6

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
    ax.set_ylabel("Évolution de la part de cadres, 2011-2022 (points)", color=texte)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=texte)
    ax.grid(axis="y", color=config.COULEUR_GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    ecartes = terciles[terciles["tirages_ecartes"] > 0]
    noms_ecartes = ", ".join(
        f"{aire} {categorie} {int(ligne['tirages_ecartes'])}"
        for (aire, categorie), ligne in ecartes.iterrows()
    )
    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(
        0.01,
        0.01,
        "Communes ayant au moins un lycée retenu à 5 km ; « sans IVAL » : aucun de ces lycées n'a "
        "d'IVAL. Moyennes simples ; sous chaque point, le nombre de communes.\nIntervalles à 95 % "
        "par bootstrap des grappes « lycée avec IVAL le plus proche », tirées dans chaque aire "
        f"({config.NB_TIRAGES_BOOTSTRAP} tirages) ;\ntirages sans commune de la catégorie, écartés "
        f"pour elle : {noms_ecartes or 'aucun'}.\nIVAL : valeur ajoutée du taux d'accès de la "
        "seconde au bac, moyenne des sessions 2012 à 2022, lycées d'au moins 5 sessions.\n"
        "Sources : Insee, recensements 2011 et 2022, « Évolution et structure de la population » ; "
        f"DEPP, IVAL ; annuaire de l'éducation ({config.DATE_ANNUAIRE}) ; IGN.",
        fontsize=8,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.17, 1, 0.95))
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig


def fig_robustesse(robustesse: pd.DataFrame, titre: str) -> Figure:
    """Pente principale de H1 dans chaque variante de robustesse, par aire (§5.6).

    Une ligne par variante en points par km (les pentes secondaires, en points par lycée, restent
    dans le tableau), un point par aire avec son intervalle à 95 % ; la spécification principale
    en haut, sur fond gris, sert de repère. `robustesse` vient de `analyse.robustesse_h1` ;
    `titre` est le message de la figure (PLAN §6).
    """
    en_km = robustesse[~robustesse.index.get_level_values("variante").str.contains("secondaire")]
    variantes = list(en_km.index.unique("variante"))
    aires = aires_ordonnees(en_km.index.get_level_values("aire"))
    texte = config.COULEUR_TEXTE
    decalages = {aire: 0.22 * (k - (len(aires) - 1) / 2) for k, aire in enumerate(aires)}

    fig, ax = plt.subplots(figsize=(10, 1.2 + 0.62 * len(variantes)))
    ax.axhspan(-0.45, 0.45, color=config.COULEUR_FOND_RETENUES, zorder=0)
    ax.axvline(0, color=config.COULEUR_LIAISON, linewidth=1, zorder=0)
    for rang, variante in enumerate(variantes):
        for aire in aires:
            if (variante, aire) not in en_km.index:
                continue
            ligne = en_km.loc[(variante, aire)]
            y = rang + decalages[aire]
            couleur = config.COULEURS_AIRES[aire]
            if pd.notna(ligne["ic_bas"]):
                ax.hlines(y, ligne["ic_bas"] * 100, ligne["ic_haut"] * 100, color=couleur, lw=2)
            ax.scatter(
                ligne["pente"] * 100,
                y,
                s=36,
                color=couleur,
                edgecolor="white",
                zorder=3,
                label=aire if rang == 0 else None,
            )
    ax.set_yticks(range(len(variantes)))
    ax.set_yticklabels(variantes, color=texte)
    ax.invert_yaxis()
    ax.set_xlabel(
        "Pente principale : points de part de cadres par km de distance au lycée privé", color=texte
    )
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(colors=texte)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=config.COULEUR_GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(
        0.01,
        0.01,
        "Sens de H1 : pente négative. Même estimation et même bootstrap que la spécification "
        f"principale ({config.NB_TIRAGES_BOOTSTRAP} tirages par commune).\nUne variante sans objet "
        "dans une aire n'a pas de point : prix au m² à Lyon et Nantes (Alsace-Moselle hors DVF),\n"
        "frontière à Strasbourg. Sources : Insee, recensement 2022 ; annuaire de l'éducation ; "
        "DVF (Etalab) ; IGN.",
        fontsize=8,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.12, 1, 0.95))
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig


def fig7(pentes: pd.DataFrame, titre: str) -> Figure:
    """Fig. 7 : association de la part de cadres avec l'accès à chaque infrastructure (H4).

    Une ligne par mesure d'accès, de la plus forte à la plus faible association (moyenne des
    pentes des aires), un point par aire avec son intervalle à 95 %. `pentes` vient de
    `analyse.pentes_h4` ; `titre` est le message de la figure, écrit par le groupe (PLAN §6).
    """
    aires = aires_ordonnees(pentes.index.get_level_values("aire"))
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
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(colors=texte)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=config.COULEUR_GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    # Légende dans l'ordre des aires de la charte, en dehors des points
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(
        0.01,
        0.01,
        "Pente des paires de communes contiguës, sans constante, à écarts de distance au centre "
        "et de log-densité donnés.\nMesures d'accès centrées réduites dans chaque aire et "
        "orientées pour qu'une valeur positive dise « plus d'accès, plus de cadres » (distances "
        "retournées).\nIntervalles à 95 % par bootstrap des communes "
        f"({config.NB_TIRAGES_BOOTSTRAP} tirages, les mêmes pour toutes les mesures).\n"
        "Sources : Insee, recensement 2022 et BPE 2025 ; annuaire de l'éducation "
        f"({config.DATE_ANNUAIRE}) ; SNCF Gares & Connexions ; ministère des Sports (Data ES) ;\n"
        "copies du 03/11/2026 pour la BPE, les gares et Data ES ; DREES, APL 2024 ; IGN.",
        fontsize=8,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.13, 1, 0.95))
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig


def carte_iris(
    contours: gpd.GeoDataFrame, parts: pd.DataFrame, code_centre: str, titre: str
) -> Figure:
    """Carte statique de la part de cadres par IRIS d'une aire, en 2011 puis en 2022 (A18).

    `contours` vient de `collecte.contours_iris`, `parts` de `nettoyage.part_cadres_iris`. En haut,
    l'aire entière ; en bas, un zoom sur un carré de `config.ZOOM_IRIS_KM` km de demi-côté autour
    du centroïde de la commune-centre `code_centre` (Lyon : 69123, ses arrondissements réunis),
    où ses IRIS deviennent lisibles. Les quatre panneaux ont les mêmes classes ; les IRIS non
    comparables (code ou territoire changé depuis 2011) sont hachurés en gris. C'est une
    exploration (§5.8) : ni lycées ni test. `titre` est le message de la carte, écrit par le
    groupe (PLAN §6).
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
    fig, axes = plt.subplots(2, 2, figsize=(13, 13))
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
        ax_zoom.set_title(
            f"{annee}, autour de la commune-centre ({2 * config.ZOOM_IRIS_KM} km de côté)",
            loc="left",
            fontsize=11,
        )

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
    fig.legend(handles=poignees, loc="center right", frameon=False, fontsize=9)
    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(
        0.01,
        0.01,
        "Part des cadres et professions intellectuelles supérieures parmi les actifs de 15 à 64 "
        "ans (occupés et chômeurs ayant déjà travaillé), et non de 25 à 54 ans comme dans le reste "
        "du rapport : les bases IRIS ne croisent pas\ncette tranche avec la catégorie "
        "socioprofessionnelle. Non comparable : code IRIS absent en 2011, aucun actif à une "
        "date, ou commune non découpée qui en a absorbé une autre depuis 2013. Exploitation "
        "complémentaire : la part\nd'un IRIS de moins de 200 actifs est peu précise "
        "(échantillon). Sources : Insee, recensements 2011 et 2022, bases infracommunales "
        "« Activité des résidents » ; contours IRIS de l'IGN (cartiflette, "
        f"COG {config.ANNEE_COG}).",
        fontsize=8,
        color=config.COULEUR_TEXTE,
    )
    fig.tight_layout(rect=(0, 0.05, 0.85, 0.97))
    # Fermée, la figure n'est affichée qu'une fois par un notebook, avec sa valeur de retour
    _axes_a_la_francaise(fig)
    plt.close(fig)
    return fig
