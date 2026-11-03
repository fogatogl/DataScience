"""Construction de la base communale et des paires de communes contiguës (PLAN §4, étape G)."""

import geopandas as gpd
import numpy as np
import pandas as pd

from cadres_lycees import accessibilite, analyse, collecte, config, geo, nettoyage, stockage


def lycees_avec_aire(referentiel: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Renvoie les lycées retenus (§2.4) de France métropolitaine, avec l'aire de leur commune.

    `referentiel` vient de `geo.referentiel_communes`. `aire` est manquante pour les lycées hors
    du référentiel : ils sont gardés, car ils comptent dans l'accès des communes du bord (effet de
    bord, §2.4). Sans construire la base, cela suffit à la Fig. 1, qui montre les 8 candidates
    alors que la base ne porte que sur les aires retenues.
    """
    return nettoyage.lycees_geo(
        collecte.annuaire_education(), collecte.ips_lycees(), collecte.ival_lycees(), referentiel
    )


def construire_base(
    aires: dict[str, str],
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    """Construit la base communale, les lycées et les paires de communes contiguës des aires.

    `aires` associe le nom de l'aire à son code AAV2020 (par exemple `config.AIRES_RETENUES`).
    La base a une ligne par commune du référentiel (arrondissements à Lyon) : les colonnes de
    `_base_sans_cadres`, puis `part_cadres_2011`, `part_cadres_2022`, `evol_cadres_pts`,
    `actifs_2011` et `actifs_2022` (§2.3). Les
    sources sont lues dans leurs copies contrôlées (§7). Écrit `config.CHEMIN_BASE` et
    `config.CHEMIN_PAIRES`, décrits dans `docs/dictionnaire_variables.md`, et renvoie
    (base, lycées, paires).
    """
    referentiel = geo.referentiel_communes(aires)
    lycees = lycees_avec_aire(referentiel)
    base = _base_sans_cadres(referentiel, lycees)
    cadres = nettoyage.part_cadres(collecte.evol_struct_rp2022(), referentiel)
    base = base.merge(
        cadres, left_on="code_commune", right_index=True, how="left", validate="one_to_one"
    )
    assert base[cadres.columns].notna().all().all(), "Part de cadres manquante après la jointure."

    paires = geo.paires_contigues(base, list(config.VARIABLES_PAIRES))
    stockage.ecrire_parquet(base, config.CHEMIN_BASE)
    stockage.ecrire_parquet(paires, config.CHEMIN_PAIRES)
    return base, lycees, paires


def _base_sans_cadres(referentiel: gpd.GeoDataFrame, lycees: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Renvoie la base communale sans la part de cadres.

    Une ligne par commune du référentiel : accès aux lycées privés et publics (§2.4), nombre de
    lycées et IVAL moyenne dans chaque rayon, population, densité, exposition 0/1, et pour H4
    accès aux gares, aux installations sportives et aux équipements culturels, et APL aux
    médecins généralistes. Le tableau de support n'utilise que cette partie : il ne lit aucune
    donnée sur les cadres (A3).
    """
    acces_tous_lycees = accessibilite.indicateurs(
        referentiel, lycees, "lyc", attribut="ival", poids="poids_ival"
    )
    blocs = [
        accessibilite.indicateurs(referentiel, lycees[lycees["secteur"] == "prive"], "lyc_prive"),
        accessibilite.indicateurs(referentiel, lycees[lycees["secteur"] == "public"], "lyc_public"),
        # Tous secteurs : le nombre de lycées et l'IVAL moyenne servent à H3 (§5.5) ; la distance
        # au plus proche, tous secteurs confondus, n'entre dans aucune analyse du plan
        acces_tous_lycees.drop(columns="dist_lyc_min"),
        nettoyage.population(collecte.serie_historique_rp2022(), referentiel),
        # H4 (§5.7) : la même fonction d'accès pour les gares ; l'APL est déjà un indicateur
        # d'accès, calculé par la DREES, et entre telle quelle
        accessibilite.indicateurs(referentiel, collecte.gares(), "gare"),
        accessibilite.indicateurs(referentiel, collecte.equipements_sportifs(), "sport"),
        accessibilite.indicateurs(referentiel, collecte.equipements_culturels(), "culture"),
        collecte.apl_medecins().to_frame(),
    ]
    base = referentiel
    for bloc in blocs:
        base = base.merge(
            bloc, left_on="code_commune", right_index=True, how="left", validate="one_to_one"
        )
    # Une commune absente d'un bloc y aurait des valeurs manquantes. Seule l'IVAL moyenne peut
    # manquer : une commune sans lycée avec IVAL dans le rayon
    colonnes_obligatoires = [col for col in base.columns if not col.startswith("ival_moy_")]
    incompletes = [col for col in colonnes_obligatoires if base[col].isna().any()]
    assert not incompletes, f"Valeurs manquantes dans {incompletes}."

    for rayon in config.RAYONS_KM:
        # Exposition 0/1, pour compter les paires de statut différent (§5.2, A6). En entier :
        # pandas refuse la différence de deux booléens, que calcule `geo.paires_contigues`
        expose = base[f"n_lyc_prive_{rayon}km"] > 0
        base[f"expose_lyc_prive_{rayon}km"] = expose.astype(int)
    # H4, sport et culture : la distance au plus proche distingue peu les communes (installation
    # sportive à 2 km au plus pour 93 à 99 % d'entre elles selon l'aire ; équipement culturel à
    # une distance médiane de 0,8 à 1,8 km). On prend le nombre au rayon principal, très
    # asymétrique (asymétrie de 3,3 à 4 selon l'aire), d'où le logarithme comme pour la densité
    # (A7). log(1 + n) : des communes n'en ont aucun à 5 km
    for equipement in ("sport", "culture"):
        nombre = base[f"n_{equipement}_{config.RAYON_PRINCIPAL_KM}km"]
        base[f"log_n_{equipement}_{config.RAYON_PRINCIPAL_KM}km"] = np.log1p(nombre)
    return base


def ecrire_tableau_support() -> None:
    """Écrit le tableau de support des 8 aires candidates dans `config.CHEMIN_TABLEAU_SUPPORT`.

    Valeurs des critères du choix des aires (§2.2) : aire de l'Ouest (a), poids du privé et
    écart d'IPS (b), population (c), lycées privés (d), support de l'exposition à 5 et 10 km (e)
    et faisabilité (f) : coût de Lyon (A11) et, pour Lille et Strasbourg, communes à moins de
    `config.DIST_FRONTIERE_KM` km du contour national (§5.2, A6) ; puis le détail des cellules
    après fusion. Le tableau est calculé une fois, avant le choix des aires, et commité. La base
    et les paires des 8 candidates sont construites ici sans la part de cadres, qui n'y entre
    donc pas, et ne sont pas écrites : `final/` reste celui des aires retenues.
    """
    referentiel = geo.referentiel_communes(config.AIRES_CANDIDATES)
    lycees = lycees_avec_aire(referentiel)
    base = _base_sans_cadres(referentiel, lycees)
    paires = geo.paires_contigues(base, list(config.VARIABLES_PAIRES_SANS_CADRES))
    profil = analyse.profil_aires(lycees)
    criteres = pd.DataFrame(
        {
            "ouest": profil.index.isin(config.AIRES_OUEST),
            "part_prive_lycees": profil["part_prive"].round(3),
            "part_prive_candidats": profil["part_prive_candidats"].round(3),
            "ecart_ips": profil["ecart_ips"].round(1),
            "n_ips_public": profil["n_ips_public"],
            "n_ips_prive": profil["n_ips_prive"],
            "population_2022": base.groupby("aire")["pop_2022"].sum(),
            "lycees": profil["n_lycees"],
            "lycees_prives": profil["n_prive"],
        },
        index=profil.index,
    )
    manquantes = criteres.columns[criteres.isna().any()].tolist()
    assert not manquantes, f"Valeurs manquantes dans les critères : {manquantes}."

    frontaliers = base[base["aire"].isin(config.AIRES_FRONTALIERES)]
    distance_frontiere = geo.distance_contour_national_km(frontaliers)
    pres_frontiere = distance_frontiere < config.DIST_FRONTIERE_KM
    aire_frontaliere = frontaliers.set_index("code_commune")["aire"]
    frontiere = pres_frontiere.groupby(aire_frontaliere).sum()
    # Un tiret pour les aires loin d'une frontière : une valeur manquante ferait écrire toute la
    # colonne en nombres décimaux
    criteres[f"communes_a_moins_de_{config.DIST_FRONTIERE_KM}km_frontiere"] = [
        str(frontiere[aire]) if aire in frontiere.index else "—" for aire in criteres.index
    ]

    cellules = pd.concat(
        [
            analyse.cellules_anneaux(base, rayon).assign(rayon_km=rayon)
            for rayon in config.RAYONS_SUPPORT_KM
        ]
    )
    support = analyse.tableau_support(base, paires, cellules).round(3)

    texte = "\n\n".join(
        [
            "# Tableau de support du choix des aires\n\nÉcrit par "
            "`pipeline.ecrire_tableau_support()` (PLAN §2.2, §5.2), avant le choix des aires et "
            "sans aucune donnée sur les cadres. Les règles de fusion des anneaux et la borne "
            "d'équilibre sont celles de l'amendement A6.",
            "## Critères (a) à (d) et frontière (f)",
            criteres.to_markdown(),
            "Critère (f), faisabilité : la part de cadres des arrondissements de Lyon vient du "
            "même fichier et avec la même définition que celle des autres communes ; le coût de "
            "Lyon est nul pour la variable à expliquer (amendement A11).",
            "## Support de l'exposition (critère e), à 5 et 10 km",
            support.to_markdown(index=False),
            "## Cellules après fusion des anneaux",
            cellules.round(2).to_markdown(index=False),
        ]
    )
    config.CHEMIN_TABLEAU_SUPPORT.write_text(texte + "\n", encoding="utf-8")


def fichiers_bruts() -> pd.DataFrame:
    """Renvoie les fichiers bruts que lit le projet, avec leur sha256 (PLAN §7).

    Liste de `config.FICHIERS_BRUTS` ; un chemin qui dépend de l'aire (`{aav}`) donne une ligne
    par aire. Colonnes `fichier` et `sha256`, pour l'annexe « Reproduire le projet ».
    """
    lignes = []
    for chemin, sha256 in config.FICHIERS_BRUTS:
        if isinstance(sha256, dict):
            lignes += [(chemin.format(aav=aav), valeur) for aav, valeur in sha256.items()]
        else:
            lignes.append((chemin, sha256))
    return pd.DataFrame(lignes, columns=["fichier", "sha256"])
