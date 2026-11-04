"""Lecture et écriture des données, sur S3 ou en local, et copies contrôlées des sources."""

import functools
import hashlib
import io
import os
import warnings

import pandas as pd
import requests
import s3fs
from fsspec import AbstractFileSystem
from fsspec.implementations.local import LocalFileSystem

from cadres_lycees import config


@functools.cache
def _avertir_stockage_local(manquantes: tuple[str, ...]) -> None:
    """Prévient que les données vont dans le dossier local, une seule fois par session.

    Le registre de `warnings` ne suffit pas : pandas et geopandas le remettent à zéro, et le
    même message reviendrait à chaque lecture ou écriture. Seul l'avertissement est mémorisé :
    le choix entre S3 et local est refait à chaque appel, une variable définie plus tard compte.
    """
    warnings.warn(
        f"Variables d'environnement manquantes : {', '.join(manquantes)}. Les données sont "
        f"lues et écrites dans le dossier local {config.DOSSIER_LOCAL} (voir README).",
        # Quatre niveaux au-dessus : cette fonction, `_systeme_fichiers`, la fonction publique de
        # ce module, puis le code qui l'appelle, que l'avertissement désigne
        stacklevel=4,
    )


def _systeme_fichiers(chemin: str) -> tuple[AbstractFileSystem, str]:
    """Renvoie le système de fichiers à utiliser et le chemin complet de `chemin` dedans.

    `chemin` est relatif à la racine du stockage du projet, par exemple "raw/annuaire.parquet".
    Les valeurs des identifiants ne sont jamais lues ici : s3fs les prend dans l'environnement.
    S3 n'est utilisé que si les identifiants AWS et le nom du bucket sont tous définis ; sinon
    le code continue en local avec un avertissement, pour qu'un compte sans BUCKET_S3 ne plante
    pas.
    """
    variables_s3 = (*config.VARIABLES_AWS, config.VARIABLE_BUCKET_S3)
    manquantes = [variable for variable in variables_s3 if variable not in os.environ]
    if not manquantes:
        bucket = os.environ[config.VARIABLE_BUCKET_S3]
        return s3fs.S3FileSystem(), f"{bucket}/{config.PREFIXE_S3}/{chemin}"
    _avertir_stockage_local(tuple(manquantes))
    return LocalFileSystem(auto_mkdir=True), f"{config.DOSSIER_LOCAL}/{chemin}"


def ecrire_octets(octets: bytes, chemin: str) -> None:
    """Écrit `octets` tels quels à `chemin` (copie brute d'une source)."""
    systeme, complet = _systeme_fichiers(chemin)
    systeme.pipe_file(complet, octets)


def lire_octets(chemin: str) -> bytes:
    """Lit le fichier `chemin` tel quel (copie brute d'une source)."""
    systeme, complet = _systeme_fichiers(chemin)
    return systeme.cat_file(complet)


def ecrire_parquet(df: pd.DataFrame, chemin: str) -> None:
    """Écrit `df` en Parquet à `chemin`. Un GeoDataFrame est écrit en GeoParquet."""
    # Sérialiser en mémoire d'abord : si to_parquet échoue, aucun fichier partiel ne reste
    tampon = io.BytesIO()
    df.to_parquet(tampon)
    ecrire_octets(tampon.getvalue(), chemin)


def existe(chemin: str) -> bool:
    """Indique si le fichier `chemin` existe, pour ne pas retélécharger une source."""
    systeme, complet = _systeme_fichiers(chemin)
    return systeme.exists(complet)


def _telecharger(urls: list[str], sha256: str) -> bytes:
    """Renvoie le contenu de la première des `urls` qui fournit le fichier attendu (même sha256).

    Une URL injoignable, ou qui fournit un autre contenu, laisse la place à la suivante, avec un
    avertissement : une copie principale en panne ne doit pas passer inaperçue. Une connexion coupée
    en cours de route est retentée `config.NB_ESSAIS_TELECHARGEMENT` fois : les serveurs de l'Insee
    coupent parfois un gros fichier, et un compte neuf télécharge tout. Si aucune URL ne convient,
    tous les refus sont dans le message d'erreur. Une URL mal écrite fait échouer.
    """
    refus = []
    for url in urls:
        for _ in range(config.NB_ESSAIS_TELECHARGEMENT):
            try:
                reponse = requests.get(url, timeout=config.DELAI_TELECHARGEMENT_S)
            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.exceptions.ChunkedEncodingError,
            ) as erreur:
                refus.append(f"{url} : {erreur}")
                warnings.warn(refus[-1], stacklevel=2)
                continue
            recu = hashlib.sha256(reponse.content).hexdigest()
            if reponse.ok and recu == sha256:
                return reponse.content
            refus.append(f"{url} : HTTP {reponse.status_code}, sha256 {recu}")
            warnings.warn(refus[-1], stacklevel=2)
            # Un refus net (404, 403) ne change pas d'un essai à l'autre : on passe à l'URL
            # suivante ; un contenu tronqué, lui, peut être complet au prochain essai
            if not reponse.ok:
                break
    raise RuntimeError(f"Aucune source ne fournit le fichier de sha256 {sha256} : {refus}")


def copie_controlee(urls: list[str], chemin: str, sha256: str) -> bytes:
    """Renvoie le contenu du fichier brut `chemin`, après contrôle de son sha256.

    S'il n'est pas encore stocké, il est téléchargé à la première des `urls` qui le fournit à
    l'identique, puis enregistré. Le sha256 est contrôlé aussi à la relecture : le projet ne lit
    jamais d'autres données que celles qu'il a fixées, même si une copie locale a été
    abîmée ou remplacée.
    """
    if not existe(chemin):
        contenu = _telecharger(urls, sha256)
        ecrire_octets(contenu, chemin)
        return contenu
    contenu = lire_octets(chemin)
    recu = hashlib.sha256(contenu).hexdigest()
    assert recu == sha256, (
        f"{chemin} a le sha256 {recu}, {sha256} attendu : supprimer cette copie pour qu'elle "
        "soit retéléchargée."
    )
    return contenu
