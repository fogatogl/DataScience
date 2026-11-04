"""Statistiques descriptives des aires et des communes, et support du choix des aires."""

import itertools

import geopandas as gpd
import pandas as pd

from cadres_lycees import config


def profil_aires(lycees: gpd.GeoDataFrame) -> pd.DataFrame:
    """Renvoie une ligne par aire : lycées, part de privé sous contrat et IPS moyen par secteur.

    `part_prive` compte les lycées ; `part_prive_candidats` pondère chaque lycée par ses candidats
    au bac (`poids_ival`, moyenne des présents au bac général et technologique 2012-2022), sur
    les `n_avec_candidats` lycées qui ont une IVAL : plus proche d'une part d'élèves, sans en être
    une au sens de la DEPP. L'IPS moyen est une moyenne simple des lycées qui ont un IPS, car la
    source ne donne pas d'effectifs. `ecart_ips` est l'IPS moyen du privé moins celui du public,
    en points d'IPS ; `n_ips_public` et `n_ips_prive` sont les nombres de lycées sur lesquels
    reposent ces moyennes. Seuls les lycées situés dans les communes de l'aire comptent ; une
    aire sans lycée privé, sans IPS dans un secteur ou sans IVAL dans un secteur fait échouer.
    """
    lycees = lycees[lycees["aire"].notna()]
    prives = lycees[lycees["secteur"] == "prive"]
    profil = pd.DataFrame(
        {
            "n_lycees": lycees.groupby("aire").size(),
            "n_prive": prives.groupby("aire").size(),
        }
    )
    profil["part_prive"] = profil["n_prive"] / profil["n_lycees"]

    avec_candidats = lycees[lycees["poids_ival"].notna()]
    par_secteur = avec_candidats.groupby(["aire", "secteur"])["poids_ival"].sum()
    candidats_par_secteur = par_secteur.unstack("secteur")
    profil["part_prive_candidats"] = candidats_par_secteur["prive"] / (
        candidats_par_secteur["prive"] + candidats_par_secteur["public"]
    )
    profil["n_avec_candidats"] = avec_candidats.groupby("aire").size()

    ips = lycees.groupby(["aire", "secteur"])["ips"].agg(["mean", "count"]).unstack("secteur")
    profil["ips_public"] = ips[("mean", "public")]
    profil["ips_prive"] = ips[("mean", "prive")]
    profil["ecart_ips"] = profil["ips_prive"] - profil["ips_public"]
    profil["n_ips_public"] = ips[("count", "public")]
    profil["n_ips_prive"] = ips[("count", "prive")]

    colonnes = ["n_prive", "part_prive_candidats", "ips_public", "ips_prive"]
    manquants = profil[colonnes].isna().any(axis=1)
    assert not manquants.any(), (
        f"Pas de lycée privé, d'IVAL ou d'IPS dans un secteur : {profil.index[manquants].tolist()}."
    )
    return profil


def tableau_support(
    base: gpd.GeoDataFrame, paires: pd.DataFrame, cellules: pd.DataFrame
) -> pd.DataFrame:
    """Renvoie le support de l'exposition, une ligne par aire et par rayon.

    `base` et `paires` viennent de `pipeline.ecrire_tableau_support` : base sans la part de
    cadres, paires sur `config.VARIABLES_PAIRES_SANS_CADRES` ; `cellules` vient de
    `cellules_anneaux`, avec une colonne `rayon_km`, pour chaque rayon de
    `config.RAYONS_SUPPORT_KM`. Colonnes : `communes`, `exposees` et `part_exposees` (au moins un
    lycée privé sous contrat dans le rayon), `cellules_estimables`, `paires_statut_different`
    (l'exposition 0/1 diffère entre les deux voisines) et `correlation_non_centree` entre
    `d_dist_lyc_prive_min` et `d_dist_centre_km` dans les paires : sans centrage, elle ne
    dépend pas du sens i − j, qui suit l'ordre des codes.
    """
    x, y = paires["d_dist_lyc_prive_min"], paires["d_dist_centre_km"]
    produits = pd.DataFrame({"xy": x * y, "xx": x**2, "yy": y**2, "aire": paires["aire"]})
    sommes = produits.groupby("aire").sum()
    correlation = sommes["xy"] / (sommes["xx"] * sommes["yy"]) ** 0.5

    lignes = []
    for rayon in config.RAYONS_SUPPORT_KM:
        colonne_exposition = f"expose_lyc_prive_{rayon}km"
        par_aire = base.groupby("aire")[colonne_exposition]
        cellules_rayon = cellules[cellules["rayon_km"] == rayon]
        estimables = cellules_rayon.groupby("aire")["estimable"].sum()
        statut_different = paires[f"d_{colonne_exposition}"] != 0
        support = pd.DataFrame(
            {
                "communes": par_aire.size(),
                "exposees": par_aire.sum(),
                "part_exposees": par_aire.mean(),
                "cellules_estimables": estimables,
                "paires_statut_different": statut_different.groupby(paires["aire"]).sum(),
                "correlation_non_centree": correlation,
            }
        )
        support.insert(0, "rayon_km", rayon)
        lignes.append(support)
    resultat = pd.concat(lignes).rename_axis("aire").reset_index()
    # Une aire sans cellule à un rayon ou sans paire aurait des valeurs manquantes
    manquantes = resultat.columns[resultat.isna().any()].tolist()
    assert not manquantes, f"Valeurs manquantes dans le tableau de support : {manquantes}."
    return resultat


def lire_tableau_support() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Relit les trois tableaux de `config.CHEMIN_TABLEAU_SUPPORT` : critères, support, cellules.

    Le fichier a été commité avant le choix des aires : le rapport affiche et contrôle ces
    valeurs-là plutôt que de les recalculer. Une colonne entièrement numérique est convertie.
    """
    texte = config.CHEMIN_TABLEAU_SUPPORT.read_text(encoding="utf-8")
    tableaux = []
    for bloc in texte.split("\n## ")[1:]:
        lignes = [ligne for ligne in bloc.splitlines() if ligne.startswith("|")]
        # La deuxième ligne d'un tableau Markdown ne fait que l'aligner
        entete, _, *corps = [
            [cellule.strip() for cellule in ligne.strip("|").split("|")] for ligne in lignes
        ]
        tableau = pd.DataFrame(corps, columns=entete)
        for colonne in tableau.columns:
            nombres = pd.to_numeric(tableau[colonne], errors="coerce")
            if nombres.notna().all():
                tableau[colonne] = nombres
        tableaux.append(tableau)
    assert len(tableaux) == 3, f"{len(tableaux)} tableaux lus dans {config.CHEMIN_TABLEAU_SUPPORT}."
    return tableaux[0], tableaux[1], tableaux[2]


def effectifs_base(base: pd.DataFrame, lycees: pd.DataFrame, paires: pd.DataFrame) -> pd.DataFrame:
    """Renvoie, aire par aire, les effectifs aux étapes clés de la construction de la base.

    Communes (arrondissements à Lyon) et petites communes, sous `config.ACTIFS_MIN_ROBUSTESSE`
    actifs en 2022 ; lycées retenus situés dans l'aire, par secteur, et ceux qui ont une IVAL ;
    paires de communes contiguës ; communes qui ont un prix au m² (au moins
    `config.MIN_VENTES_DVF` ventes). Ce sont des comptes, sans donnée sur les cadres hors du seuil
    d'actifs.
    """
    communes = base.groupby("aire").agg(
        communes=("code_commune", "size"),
        petites_communes=(
            "actifs_2022",
            lambda actifs: (actifs < config.ACTIFS_MIN_ROBUSTESSE).sum(),
        ),
        communes_avec_prix=("prix_m2_med", "count"),
    )
    dans_les_aires = lycees[lycees["aire"].notna()]
    lycees_par_aire = dans_les_aires.groupby("aire").agg(
        lycees_publics=("secteur", lambda secteur: (secteur == "public").sum()),
        lycees_prives=("secteur", lambda secteur: (secteur == "prive").sum()),
        lycees_avec_ival=("ival", "count"),
    )
    effectifs = communes.join(lycees_par_aire).join(paires.groupby("aire").size().rename("paires"))
    assert effectifs.notna().all().all(), "Aire sans lycée ou sans paire."
    return effectifs


def resume_acces(base: pd.DataFrame) -> pd.DataFrame:
    """Résume, aire par aire, l'accès des communes aux lycées et aux autres infrastructures.

    Tableau descriptif, sans donnée sur les cadres (sections 2.3 et 5 du rapport) : nombre de
    communes, part des communes exposées (au moins un lycée privé sous contrat au rayon principal)
    et médiane de chaque mesure d'accès. Médianes simples des communes : les distances et les
    comptes sont très asymétriques.
    """
    rayon = config.RAYON_PRINCIPAL_KM
    mesures = [
        "dist_lyc_prive_min",
        "dist_lyc_public_min",
        "dist_gare_min",
        "apl_mg",
        f"n_sport_{rayon}km",
        f"n_culture_{rayon}km",
    ]
    par_aire = base.groupby("aire")
    effectifs = par_aire.agg(
        communes=("code_commune", "size"),
        part_exposees=(f"expose_lyc_prive_{rayon}km", "mean"),
    )
    return effectifs.join(par_aire[mesures].median())


def parts_par_anneau(base: pd.DataFrame) -> pd.DataFrame:
    """Renvoie la part de cadres de chaque anneau de distance au centre, aire par aire.

    Anneaux sans fusion ; part de l'anneau = cadres sur actifs de ses communes réunies,
    soit la moyenne des parts pondérée par `actifs_2022`. Index (`aire`, `anneau`) ; colonnes
    `part_cadres_2022` (fraction) et `communes`. Décrit le gradient centre-périphérie, qui
    justifie de comparer les communes à distance égale du centre.
    """
    communes = base.assign(
        anneau=anneau(base["dist_centre_km"]),
        cadres=base["part_cadres_2022"] * base["actifs_2022"],
    )
    par_anneau = communes.groupby(["aire", "anneau"], observed=True).agg(
        cadres=("cadres", "sum"), actifs=("actifs_2022", "sum"), communes=("code_commune", "size")
    )
    par_anneau["part_cadres_2022"] = par_anneau["cadres"] / par_anneau["actifs"]
    return par_anneau[["part_cadres_2022", "communes"]]


def anneau(dist_centre_km: pd.Series) -> pd.Series:
    """Renvoie l'anneau, sans fusion, de chaque distance au centre (catégorie ordonnée).

    Libellés « 0-5 km » … « 30 km et plus », borne basse incluse.
    """
    bornes = [*config.ANNEAUX_KM, float("inf")]
    libelles = [f"{bas}-{haut} km" for bas, haut in itertools.pairwise(config.ANNEAUX_KM)]
    libelles.append(f"{config.ANNEAUX_KM[-1]} km et plus")
    return pd.cut(dist_centre_km, bornes, right=False, labels=libelles)
