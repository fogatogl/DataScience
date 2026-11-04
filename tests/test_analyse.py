"""Tests des calculs d'analyse du PLAN §7, sur des données jouets calculables à la main.

Fusion des anneaux (`h1.cellules_anneaux`, §5.2, A6), poids du bootstrap par commune
(`h1.poids_bootstrap`, §5.3), invariance de la pente des paires au sens i − j
(`h1.pente_paires`, §5.3) et verdict de H1 (`h1.verdict_h1`, §5.3, A4, A13).
Module `h3` : verdict de H3 (`h3.verdict_h3`, §5.5), avec le seuil de fiabilité de l'IVAL (§3.2).

Fusion des anneaux : attendus calculés à la main avec les règles fixées par A6 : anneaux de départ
`config.ANNEAUX_KM` (0, 5, 10, 20, 30 km), au moins `config.EFFECTIF_MIN_GROUPE` (15) communes
exposées et 15 non exposées par cellule, écart des distances moyennes au centre d'au plus
`config.ECART_DIST_MAX_KM` (2 km).
"""

import math

import pandas as pd
import pytest

from cadres_lycees import config, h1, h3

# Le rayon de 10 km et non 5 : une fonction qui lirait toujours la colonne à 5 km échouerait.
RAYON = 10
EXPOSITION = f"expose_lyc_prive_{RAYON}km"
COLONNES = [
    "aire",
    "bas_km",
    "haut_km",
    "n_exposees",
    "n_non_exposees",
    "dist_moy_exposees",
    "dist_moy_non_exposees",
    "estimable",
]


def groupe(aire: str, distance: float, exposees: int = 0, non_exposees: int = 0) -> pd.DataFrame:
    """Communes jouets d'une aire, toutes à `distance` km du centre."""
    return pd.DataFrame(
        {
            "aire": aire,
            "dist_centre_km": distance,
            EXPOSITION: [1] * exposees + [0] * non_exposees,
        }
    )


def test_fusion_des_anneaux_puis_equilibre() -> None:
    """Fusions dans l'ordre du plan, équilibre vérifié après fusion, aire non estimable.

    Aire A, anneaux de départ (exposées, non exposées ; total) :
    [0, 5) (15, 15 ; 30), [5, 10) (1, 0 ; 1), [10, 20) (25, 5 ; 30), [20, 30) (0, 5 ; 5),
    [30, inf) (15, 15 ; 30). En échec au départ : [5, 10), [10, 20) et [20, 30).
    1. [5, 10), la plus proche du centre : voisines à 30 et 30, égalité, donc la plus proche
       du centre, [0, 5). Résultat [0, 10) (16, 15 ; 31).
    2. [10, 20) : voisines [0, 10) (31) et [20, 30) (5), donc [20, 30). Résultat [10, 30)
       (25, 10 ; 35), encore en échec.
    3. [10, 30) : voisines [0, 10) (31) et [30, inf) (30), donc [30, inf). Résultat [10, inf)
       (40, 25 ; 65).
    Toujours fusionner vers le centre, toujours vers l'extérieur, départager l'égalité vers
    l'extérieur ou ne pas refusionner [10, 30) donnerait d'autres cellules.
    """
    seuil = config.EFFECTIF_MIN_GROUPE
    borne_5_km = config.ANNEAUX_KM[1]
    communes = pd.concat(
        [
            groupe("A", 1.0, exposees=seuil),
            # 1,25 km est la moyenne des 16 exposées de [0, 10) : écart de 2 km pile.
            groupe("A", 1.25 + config.ECART_DIST_MAX_KM, non_exposees=seuil),
            # Borne haute exclue : à 5 km pile, la commune est dans [5, 10). Comptée dans
            # [0, 5), elle romprait l'égalité 30 = 30 de l'étape 1.
            groupe("A", borne_5_km, exposees=1),
            groupe("A", 15.0, exposees=25, non_exposees=5),
            groupe("A", 25.0, non_exposees=5),
            groupe("A", 35.0, exposees=seuil, non_exposees=seuil),
            groupe("B", 2.0, exposees=10, non_exposees=5),
            groupe("B", 40.0, exposees=10, non_exposees=5),
        ],
        ignore_index=True,
    )

    cellules = h1.cellules_anneaux(communes, RAYON)

    obtenu = cellules[COLONNES].sort_values(["aire", "bas_km"]).reset_index(drop=True)
    attendu = pd.DataFrame(
        [
            # (15 × 1 + 5) / 16 = 1,25 contre 3,25 : écart de 2 km, au plus 2, estimable.
            ("A", 0, 10, 16, 15, 1.25, 3.25, True),
            # 40 et 25 communes, mais (25 × 15 + 15 × 35) / 40 = 22,5 contre
            # (5 × 15 + 5 × 25 + 15 × 35) / 25 = 29 : écart de 6,5 km, non estimable,
            # sans nouvelle fusion avec [0, 10).
            ("A", 10, math.inf, 40, 25, 22.5, 29.0, False),
            # Toute l'aire ne compte que 10 non exposées : une seule ligne, non estimable,
            # même si l'écart est nul ((10 × 2 + 10 × 40) / 20 = (5 × 2 + 5 × 40) / 10 = 21).
            ("B", 0, math.inf, 20, 10, 21.0, 21.0, False),
        ],
        columns=COLONNES,
    )
    pd.testing.assert_frame_equal(obtenu, attendu, check_dtype=False)


def test_poids_bootstrap_produit_des_tirages() -> None:
    """Le poids d'une paire est le produit des tirages de ses deux communes (§5.3).

    Tirage : 44001 deux fois, 44002 zéro, 44003 une fois, 44004 trois fois. Une somme donnerait
    2, 3, 5 et 4 : seul le produit annule une paire dont une commune n'est pas tirée.
    """
    # Paires d'une aire extraites de la table complète : l'index ne part pas de 0.
    paires = pd.DataFrame(
        {
            "code_commune_i": ["44001", "44001", "44001", "44003"],
            "code_commune_j": ["44002", "44003", "44004", "44004"],
        },
        index=[3, 7, 8, 12],
    )
    # Pas dans l'ordre des paires : le tirage se lit par code, pas par position.
    tirage = pd.Series({"44004": 3, "44002": 0, "44001": 2, "44003": 1})

    poids = h1.poids_bootstrap(paires, tirage)

    attendu = pd.Series(
        [
            0,  # 2 × 0 : 44002 n'est pas tirée, la paire sort de ce tirage
            2,  # 2 × 1
            6,  # 2 × 3
            3,  # 1 × 3
        ],
        index=paires.index,
    )
    pd.testing.assert_series_equal(poids, attendu, check_dtype=False, check_names=False)

    # Une commune oubliée du tirage ne doit pas compter pour 0 sans erreur.
    with pytest.raises(AssertionError):
        h1.poids_bootstrap(paires, tirage.drop("44002"))


def test_pente_paires_invariante_au_sens_i_j() -> None:
    """Pente connue, inchangée quand on inverse le sens de paires, avec ou sans poids (§5.3, A6).

    Inverser une paire multiplie toute sa ligne par −1 (écart de part de cadres et régresseurs) :
    sans constante, X'X et X'y ne changent pas, puisque (−1)² = 1. Avec une constante, la colonne
    de 1 ne change pas de signe : ici la pente vaudrait 0,5, puis 1 après l'inversion.
    """
    acces = "d_dist_lyc_prive_min"
    # d_part = 2 × d_dist_prive + 0,5 × d_dist_centre + 1 × d_log_densite + résidu
    #   index  d_dist_prive  d_dist_centre  d_log_densite  résidu  d_part
    #     0          1              2              0          −1     2 + 1 + 0 − 1 = 2
    #     1          2              0              1          −2     4 + 0 + 1 − 2 = 3
    #     2         −1              1              1           1     −2 + 0,5 + 1 + 1 = 0,5
    #     3          1              0              0           6     2 + 6 = 8
    #     4          0              1              0           1     0,5 + 1 = 1,5
    #     5          0              0              1           1     1 + 1 = 2
    # Le résidu est orthogonal aux trois régresseurs (−1 − 4 − 1 + 6 = 0, −2 + 1 + 1 = 0,
    # −2 + 1 + 1 = 0) : les moindres carrés sans constante retrouvent exactement 2. Sans résidu,
    # une régression avec constante donnerait 2 aussi. Sans le contrôle de densité : 2,12.
    paires = pd.DataFrame(
        {
            "code_commune_i": ["44001", "44001", "44002", "44002", "44003", "44004"],
            "code_commune_j": ["44002", "44003", "44003", "44004", "44005", "44005"],
            "d_part_cadres_2022": [2.0, 3.0, 0.5, 8.0, 1.5, 2.0],
            acces: [1.0, 2.0, -1.0, 1.0, 0.0, 0.0],
            "d_dist_centre_km": [2.0, 0.0, 1.0, 0.0, 1.0, 0.0],
            "d_log_densite": [0.0, 1.0, 1.0, 0.0, 0.0, 1.0],
        }
    )
    # Paires 1 et 3 prises dans l'autre sens (j − i), puis lignes mélangées.
    inversees = [1, 3]
    colonnes_d = ["d_part_cadres_2022", acces, "d_dist_centre_km", "d_log_densite"]
    retournees = paires.copy()
    retournees.loc[inversees, ["code_commune_i", "code_commune_j"]] = paires.loc[
        inversees, ["code_commune_j", "code_commune_i"]
    ].to_numpy()
    retournees.loc[inversees, colonnes_d] = -paires.loc[inversees, colonnes_d]
    retournees = retournees.loc[[3, 0, 5, 1, 4, 2]]

    assert h1.pente_paires(paires, acces) == pytest.approx(2)
    assert h1.pente_paires(retournees, acces) == pytest.approx(2)

    # Poids comme des produits de tirages : un poids k compte la paire k fois (§5.3), 0 la retire.
    # Pente des paires dupliquées : 5,77. Des poids ignorés donneraient 2, des poids élevés au
    # carré 6,85, des poids lus par position et non par index dans `retournees` 2,67.
    poids = pd.Series([2, 0, 1, 3, 1, 2], index=paires.index)
    dupliquees = paires.loc[paires.index.repeat(poids.to_numpy())].reset_index(drop=True)
    attendu = h1.pente_paires(dupliquees, acces)
    assert h1.pente_paires(paires, acces, poids) == pytest.approx(attendu)
    assert h1.pente_paires(retournees, acces, poids) == pytest.approx(attendu)


def cellule(
    aire: str, rayon: int, bas: float, haut: float, ic: tuple[float, float] | None = None
) -> dict:
    """Cellule jouet d'anneaux : estimable si `ic` est donné, d'écart au milieu de `ic`."""
    ecart, ic_bas, ic_haut = math.nan, math.nan, math.nan
    if ic is not None:
        ic_bas, ic_haut = ic
        ecart = (ic_bas + ic_haut) / 2
    return {
        "rayon_km": rayon,
        "aire": aire,
        "bas_km": float(bas),
        "haut_km": float(haut),
        "estimable": ic is not None,
        "ecart": ecart,
        "ic_bas": ic_bas,
        "ic_haut": ic_haut,
    }


def test_verdict_h1_anneaux_compares_et_contradictions() -> None:
    """Verdict de H1 sur sept aires jouets, une règle du §5.3 (A4, A13) chacune.

    Anneaux d'origine : [0, 5), [5, 10), [10, 20), [20, 30), [30, inf). Sens de H1 : pente
    principale négative, pente secondaire et écarts des cellules positifs.
    A  confirmée sans anneau comparé (seul le 10 km est estimable) : « paires seules ».
    B  intervalle qui contient zéro, 2 anneaux comparés concordants, aucune cellule hors de
       zéro : « infirmée », résultat nul établi.
    C  confirmée, mais une cellule à un seul rayon, sous zéro : « nuancée ».
    D  intervalle qui contient zéro sans anneau comparé : « non concluante ».
    E  comme B, mais une cellule au-dessus de zéro : nul non établi, « non concluante ».
    F  pente positive dont l'intervalle exclut zéro : « infirmée », sans mention.
    G  confirmée, mais anneaux comparés de même signe aux intervalles disjoints : « nuancée ».
    """
    r5, r10 = config.RAYONS_SUPPORT_KM
    inf = math.inf
    aires = ["A", "B", "C", "D", "E", "F", "G"]
    principale = pd.DataFrame(
        {
            "pente": [-0.02, -0.005, -0.02, -0.01, -0.005, 0.02, -0.02],
            "ic_bas": [-0.03, -0.02, -0.03, -0.03, -0.02, 0.01, -0.03],
            "ic_haut": [-0.01, 0.01, -0.01, 0.01, 0.01, 0.03, -0.01],
            "n_paires": [40, 50, 40, 40, 50, 40, 40],
        },
        index=pd.Index(aires, name="aire"),
    )
    # Le sens seul compte pour la pente secondaire : l'intervalle de A contient zéro et ne
    # doit pas empêcher la confirmation. Seule F a une pente secondaire négative. A et F sont
    # échangées : une lecture par position donnerait à A la pente de F, et « nuancée ».
    secondaire = pd.DataFrame(
        {
            "pente": [-0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
            "ic_bas": [-0.015, 0.005, 0.005, 0.005, 0.005, -0.01, 0.005],
            "ic_haut": [-0.005, 0.015, 0.015, 0.015, 0.015, 0.03, 0.015],
        },
        index=pd.Index(["F", "B", "C", "D", "E", "A", "G"], name="aire"),
    )
    anneaux = pd.DataFrame(
        [
            # A : aucune cellule estimable à 5 km, donc 0 anneau comparé.
            cellule("A", r5, 0, inf),
            cellule("A", r10, 0, inf, (-0.01, 0.03)),
            # B : [20, inf) à 5 km couvre [20, 30) et [30, inf), chacun couvert à 10 km par
            # sa propre cellule : 2 anneaux comparés. [0, 20) n'est estimable qu'à 10 km et
            # n'en ajoute pas. [20, 30) : 5 km [−0,02 ; 0,04], 10 km [−0,01 ; 0,05] ;
            # [30, inf) : 5 km [−0,02 ; 0,04], 10 km [−0,005 ; 0,035] : signes positifs,
            # intervalles qui se recoupent, tous contiennent zéro.
            cellule("B", r5, 0, 20),
            cellule("B", r5, 20, inf, (-0.02, 0.04)),
            cellule("B", r10, 0, 20, (-0.015, 0.025)),
            cellule("B", r10, 20, 30, (-0.01, 0.05)),
            cellule("B", r10, 30, inf, (-0.005, 0.035)),
            # C : [10, inf) à 10 km entièrement sous zéro, hors de tout anneau comparé. Si
            # seules les cellules d'un anneau comparé contredisaient, C resterait confirmée.
            cellule("C", r5, 0, inf),
            cellule("C", r10, 0, 10, (-0.01, 0.03)),
            cellule("C", r10, 10, inf, (-0.05, -0.01)),
            # D : même cellule que A, mais intervalle principal [−0,03 ; 0,01].
            cellule("D", r5, 0, inf),
            cellule("D", r10, 0, inf, (-0.01, 0.03)),
            # E : [0, inf) aux deux rayons, 5 anneaux comparés, concordants (signes positifs,
            # recouvrement [0,01 ; 0,03]), mais [0,01 ; 0,03] à 10 km est au-dessus de zéro.
            cellule("E", r5, 0, inf, (-0.01, 0.03)),
            cellule("E", r10, 0, inf, (0.01, 0.03)),
            # F : aucune cellule estimable.
            cellule("F", r5, 0, inf),
            cellule("F", r10, 0, inf),
            # G : [10, inf) à 5 km et [20, inf) à 10 km : 2 anneaux comparés, [20, 30) et
            # [30, inf) ; [10, 20) n'est couvert qu'à 5 km. [0,02 ; 0,04] et [−0,005 ; 0,015]
            # ont le même signe mais ne se recoupent pas ; aucun n'est sous zéro.
            cellule("G", r5, 0, 10),
            cellule("G", r5, 10, inf, (0.02, 0.04)),
            cellule("G", r10, 0, 20),
            cellule("G", r10, 20, inf, (-0.005, 0.015)),
        ]
    )

    verdicts = h1.verdict_h1(principale, secondaire, anneaux)

    obtenu = verdicts[["verdict", "mention", "anneaux_compares"]].sort_index()
    attendu = pd.DataFrame(
        [
            ("confirmée", "paires seules", 0),
            ("infirmée", "résultat nul établi", 2),
            ("nuancée", "", 0),
            ("non concluante", "", 0),
            ("non concluante", "", 5),
            ("infirmée", "", 0),
            ("nuancée", "", 2),
        ],
        columns=["verdict", "mention", "anneaux_compares"],
        index=pd.Index(aires, name="aire"),
    )
    pd.testing.assert_frame_equal(obtenu, attendu, check_dtype=False, check_names=False)


# β_n entièrement au-dessus de zéro dans tous les cas : une fonction qui lirait β_n à la place
# de β_q − β_n donnerait « confirmée » au lieu de « nuancée », et manquerait « infirmée »
# par l'écart.
IC_BETA_N = (0.1, 0.3)


def lignes_h3(portee: str, ic_q: tuple, ic_ecart: tuple, ecartes: int = 0) -> list[dict]:
    """Lignes jouets de `h3.estimation_h3` pour une portée, estimation au milieu de l'intervalle.

    Intervalle non rapporté (NaN) : l'estimation reste, positive, comme si elle confirmait.
    """
    lignes = []
    for coefficient, (ic_bas, ic_haut) in [
        ("β_q", ic_q),
        ("β_n", IC_BETA_N),
        ("β_q − β_n", ic_ecart),
    ]:
        estimation = 0.2 if math.isnan(ic_bas) else (ic_bas + ic_haut) / 2
        lignes.append(
            {
                "portee": portee,
                "coefficient": coefficient,
                "estimation": estimation,
                "ic_bas": ic_bas,
                "ic_haut": ic_haut,
                "n_communes": 268 if portee == "ensemble" else 75,
                "n_grappes": 81 if portee == "ensemble" else 16,
                "tirages_ecartes": ecartes,
            }
        )
    return lignes


AU_DESSUS = (0.1, 0.5)
SOUS_ZERO = (-0.4, -0.05)
AVEC_ZERO = (-0.1, 0.3)
NON_RAPPORTE = (math.nan, math.nan)


@pytest.mark.parametrize(
    ("fiabilite", "ic_q", "ic_ecart", "ecartes", "attendu"),
    [
        # 0,49 < 0,5 : la mesure ne tranche pas, même avec des intervalles qui confirmeraient.
        (
            config.SEUIL_FIABILITE_IVAL - 0.01,
            AU_DESSUS,
            AU_DESSUS,
            0,
            "non testable avec cette mesure",
        ),
        # « au moins 0,5 » : 0,5 pile est testable.
        (config.SEUIL_FIABILITE_IVAL, AU_DESSUS, AU_DESSUS, 0, "confirmée"),
        (0.8, AU_DESSUS, AU_DESSUS, 0, "confirmée"),
        (0.8, SOUS_ZERO, AU_DESSUS, 0, "infirmée"),
        (0.8, AVEC_ZERO, SOUS_ZERO, 0, "infirmée"),
        # β_q − β_n sous zéro ne « contient » pas zéro : « infirmée », pas « nuancée ».
        (0.8, AU_DESSUS, SOUS_ZERO, 0, "infirmée"),
        (0.8, AU_DESSUS, AVEC_ZERO, 0, "nuancée"),
        (0.8, AVEC_ZERO, AVEC_ZERO, 0, "non concluante"),
        # β_q − β_n au-dessus ne suffit pas : β_q doit l'être aussi.
        (0.8, AVEC_ZERO, AU_DESSUS, 0, "non concluante"),
        # 51 tirages écartés sur 1 000 : intervalles non rapportés, estimations positives.
        (0.8, NON_RAPPORTE, NON_RAPPORTE, config.MAX_TIRAGES_ECARTES + 1, "non concluante"),
    ],
)
def test_verdict_h3_seuil_et_regles(
    fiabilite: float, ic_q: tuple, ic_ecart: tuple, ecartes: int, attendu: str
) -> None:
    """Verdict de H3 sur la seule portée « ensemble » (§5.5) : « non testable avec cette mesure »
    sous le seuil de fiabilité de l'IVAL (§3.2), puis la première règle vérifiée parmi
    « infirmée », « confirmée », « nuancée », « non concluante ».

    L'aire, descriptive, a β_q et β_q − β_n sous zéro : la lire, ou combiner toutes les portées,
    donnerait « infirmée » là où l'ensemble ne l'est pas.
    """
    estimation = pd.DataFrame(
        lignes_h3("ensemble", ic_q, ic_ecart, ecartes)
        + lignes_h3("Strasbourg", SOUS_ZERO, SOUS_ZERO)
    ).set_index(["portee", "coefficient"])

    verdicts = h3.verdict_h3(estimation, fiabilite)

    assert list(verdicts.index) == ["ensemble"]
    assert verdicts.loc["ensemble", "verdict"] == attendu
    assert verdicts.loc["ensemble", "fiabilite"] == pytest.approx(fiabilite)
