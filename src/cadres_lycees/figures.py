"""Figures du rapport : une fonction par figure, avec les mêmes couleurs de secteur."""

import html
import itertools
from collections.abc import Collection

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

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


def fig2(base: pd.DataFrame, titre: str) -> Figure:
    """Fig. 2 : part de cadres de chaque commune selon sa distance au centre de l'aire.

    Un point par commune et, par aire, une courbe qui relie la part de cadres de chaque tranche
    de distance (`_courbe_tranches`). Les bornes des anneaux du §5.2 sont en pointillés : la
    figure montre pourquoi on compare à distance égale (PLAN §5.1). `base` vient de
    `pipeline.construire_base` ; `titre` est le message de la figure, écrit par le groupe
    (PLAN §6). Une commune sans actif en 2022 n'a pas de part et n'est pas tracée (A17).
    """
    inconnues = sorted(set(base["aire"]) - set(config.COULEURS_AIRES))
    assert not inconnues, f"Aires sans couleur dans config.COULEURS_AIRES : {inconnues}."
    sans_part = base["part_cadres_2022"].isna()
    communes = base[~sans_part]
    texte = config.COULEUR_TEXTE

    fig, ax = plt.subplots(figsize=(11, 6.2))
    for borne in config.ANNEAUX_KM[1:]:
        ax.axvline(borne, color=config.COULEUR_LIAISON, linestyle=":", linewidth=1, zorder=0)
    ax.text(
        config.ANNEAUX_KM[1],
        1.0,
        " bornes des anneaux",
        transform=ax.get_xaxis_transform(),
        va="top",
        fontsize=8,
        color=texte,
    )
    for aire, couleur in config.COULEURS_AIRES.items():
        communes_aire = communes[communes["aire"] == aire]
        if communes_aire.empty:
            continue
        ax.scatter(
            communes_aire["dist_centre_km"],
            communes_aire["part_cadres_2022"] * 100,
            s=12,
            color=couleur,
            alpha=0.3,
            linewidth=0,
            zorder=1,
        )
        courbe = _courbe_tranches(communes_aire)
        ax.plot(
            courbe["distance"],
            courbe["part"] * 100,
            color=couleur,
            linewidth=2.2,
            marker="o",
            markersize=4,
            zorder=2,
            label=f"{aire} ({len(communes_aire)} communes)",
        )

    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    ax.set_xlabel("Distance au centre de l'aire (km)", color=texte)
    ax.set_ylabel("Part de cadres parmi les actifs de 25 à 54 ans en 2022 (%)", color=texte)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=texte)
    ax.grid(axis="y", color=config.COULEUR_GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right")

    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    pas = f"{config.PAS_COURBE_FIG2_KM:g}".replace(".", ",")
    fig.text(
        0.01,
        0.01,
        "Un point par commune (arrondissement à Lyon). Courbe : part de cadres de chaque tranche "
        f"de {pas} km de distance au centre, toutes communes de la tranche réunies\n(moyenne "
        "pondérée par les actifs), placée au milieu de la tranche ; pas de point pour une "
        f"tranche de moins de {config.MIN_COMMUNES_TRANCHE_FIG2} communes. Distance à vol "
        "d'oiseau entre centroïdes.\n"
        f"Communes sans actif en 2022, non tracées : {sans_part.sum()}. Sources : Insee, "
        "recensement 2022, « Évolution et structure de la population » ; aires d'attraction des "
        "villes 2020 ; IGN.",
        fontsize=8,
        color=texte,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    plt.close(fig)
    return fig


def _courbe_tranches(communes: pd.DataFrame) -> pd.DataFrame:
    """Part de cadres par tranche de distance au centre, pondérée par les actifs (Fig. 2).

    La part d'une tranche est le total de ses cadres sur le total de ses actifs, soit la moyenne
    des parts communales pondérée par `actifs_2022` (§3.2). Renvoie une ligne par tranche d'au
    moins `config.MIN_COMMUNES_TRANCHE_FIG2` communes : `distance` (milieu de la tranche, km) et
    `part` (fraction).
    """
    pas = config.PAS_COURBE_FIG2_KM
    cadres = communes.assign(
        tranche=communes["dist_centre_km"] // pas,
        cadres=communes["part_cadres_2022"] * communes["actifs_2022"],
    )
    tranches = cadres.groupby("tranche").agg(
        n=("cadres", "size"), cadres=("cadres", "sum"), actifs=("actifs_2022", "sum")
    )
    tranches = tranches[tranches["n"] >= config.MIN_COMMUNES_TRANCHE_FIG2]
    return pd.DataFrame(
        {
            "distance": (tranches.index + 0.5) * pas,
            "part": tranches["cadres"] / tranches["actifs"],
        }
    )


def fig5(paires: pd.DataFrame, pentes: pd.DataFrame, titre: str) -> Figure:
    """Fig. 5 : écart de part de cadres et écart de distance au lycée privé dans les paires.

    Un panneau par aire : le nuage par classes de `analyse.nuage_paires` et la droite de pente
    principale de H1, sans constante, avec son intervalle à 95 % (§5.3). `paires` vient de
    `pipeline.construire_base`, `pentes` de `analyse.pentes_paires_par_aire(paires,
    "d_dist_lyc_prive_min")` ; `titre` est le message de la figure, écrit par le groupe (PLAN §6).
    """
    acces = "d_dist_lyc_prive_min"
    aires = [aire for aire in config.COULEURS_AIRES if aire in set(paires["aire"])]
    inconnues = sorted(set(paires["aire"]) - set(aires))
    assert not inconnues, f"Aires sans couleur dans config.COULEURS_AIRES : {inconnues}."
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
        ax.set_xlabel("Écart de distance au lycée privé le plus proche (km)", color=texte)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=texte)
        ax.grid(color=config.COULEUR_GRILLE, linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0][0].set_ylabel("Écart de part de cadres en 2022 (points)", color=texte)

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
    plt.close(fig)
    return fig


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
    folium.LayerControl(collapsed=False).add_to(carte)

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


def fig7(pentes: pd.DataFrame, titre: str) -> Figure:
    """Fig. 7 : association de la part de cadres avec l'accès à chaque infrastructure (H4).

    Une ligne par mesure d'accès, de la plus forte à la plus faible association (moyenne des
    pentes des aires), un point par aire avec son intervalle à 95 %. `pentes` vient de
    `analyse.pentes_h4` ; `titre` est le message de la figure, écrit par le groupe (PLAN §6).
    """
    aires = [
        aire for aire in config.COULEURS_AIRES if aire in set(pentes.index.get_level_values("aire"))
    ]
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
    plt.close(fig)
    return fig
