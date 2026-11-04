"""Charte graphique commune aux figures : ordre des aires, style des axes, titre et note."""

import re
import textwrap
from collections.abc import Collection

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, ScalarFormatter

from cadres_lycees import config


def aires_ordonnees(aires: Collection[str]) -> list[str]:
    """Renvoie les aires présentes dans l'ordre de `config.COULEURS_AIRES`.

    Échoue si une aire n'a pas de couleur : sinon elle disparaîtrait de la figure sans signal.
    """
    presentes = set(aires)
    inconnues = sorted(presentes - set(config.COULEURS_AIRES))
    assert not inconnues, f"Aires sans couleur dans config.COULEURS_AIRES : {inconnues}."
    return [aire for aire in config.COULEURS_AIRES if aire in presentes]


def styler_axes(ax: plt.Axes, grille: str, axe_y: bool = True) -> None:
    """Applique le style commun : sans cadre haut et droit, grille claire sous les données.

    `grille` vaut "x", "y" ou "both" ; sans `axe_y`, la ligne et les tirets de l'axe des y
    disparaissent aussi (axe de libellés).
    """
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=config.COULEUR_TEXTE)
    if not axe_y:
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    ax.grid(axis=grille, color=config.COULEUR_GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)


def habiller(fig: Figure, titre: str, note: str, haut: float = 0.95) -> None:
    """Pose le titre-message et la note de la figure, ajuste la mise en page, puis la ferme.

    La note est recoupée à la largeur de la figure en `config.TAILLE_NOTE_FIGURES` points, pour
    rester lisible une fois la figure réduite à la colonne du rapport ; la marge du bas suit sa
    longueur. Les graduations passent à la française. Fermée, la figure n'est affichée qu'une
    fois par un notebook, avec sa valeur de retour.
    """
    taille = config.TAILLE_NOTE_FIGURES
    # Environ 0,62 cadratin par caractère (police par défaut de matplotlib) : caractères par ligne
    largeur = int(fig.get_figwidth() * 72 / (taille * 0.62))
    # Seuls les espaces ordinaires coupent : « 95 % » garde son espace insécable
    lignes = textwrap.wrap(re.sub(r"[ \n]+", " ", note), largeur)
    fig.suptitle(titre, fontsize=13, x=0.01, ha="left")
    fig.text(0.01, 0.01, "\n".join(lignes), fontsize=taille, color=config.COULEUR_TEXTE)
    hauteur_note = (len(lignes) * taille * 1.35 / 72 + 0.25) / fig.get_figheight()
    fig.tight_layout(rect=(0, hauteur_note, 1, haut))
    _axes_a_la_francaise(fig)
    plt.close(fig)


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
