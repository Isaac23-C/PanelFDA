from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re
import time

import mysql.connector
import spacy
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor


DB_CONFIG = {
    "user": "root",
    "password": "root",
    "host": "127.0.0.1",
    "port": 8889,
    "database": "covid_19pruebas",
}

NLP_MODEL = "es_core_news_sm"
BATCH_SIZE = 500
STAGING_TABLE = "registro_a_mortalidad_tmp"

NEGATION_PATTERN = re.compile(
    r"\b("
    r"no|sin|niega|negado|negada|descarta|descartado|descartada|"
    r"podr[ií]a|puede|probable|posible|riesgo|eventual|sospecha"
    r")\b",
    re.IGNORECASE,
)

EXCLUSION_PHRASES = (
    "riesgo de fallecer",
    "podria fallecer",
    "podría fallecer",
    "puede fallecer",
    "inclusive fallecer",
    "probabilidad de fallecer",
    "en caso de fallecimiento",
)

POSITIVE_PATTERNS = (
    re.compile(r"\bfallec(?:e|io|ió|iendo|imiento)\b", re.IGNORECASE),
    re.compile(r"\bdefunci(?:on|ón)\b", re.IGNORECASE),
    re.compile(r"\bnota de defunci(?:on|ón)\b", re.IGNORECASE),
    re.compile(r"\bhora de defunci(?:on|ón)\b", re.IGNORECASE),
    re.compile(r"\begres[ao].{0,25}\bdefunci(?:on|ón)\b", re.IGNORECASE),
    re.compile(r"\bmu(?:rio|rió|ere|erto|erta)\b", re.IGNORECASE),
    re.compile(r"\bobit[oó]\b", re.IGNORECASE),
)

DEATH_LEMMAS = {"fallecer", "morir"}
DEATH_NOUNS = {"defuncion", "defunción", "obito", "óbito", "muerte", "fallecimiento"}


@dataclass
class PatientText:
    nuevos: str
    text: str


def get_connection() -> MySQLConnection:
    return mysql.connector.connect(**DB_CONFIG)


def ensure_schema(cursor: MySQLCursor) -> None:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = %s
            AND table_name = 'registro_a'
            AND column_name = 'mortalidad'
        """,
        (DB_CONFIG["database"],),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            ALTER TABLE registro_a
            ADD COLUMN mortalidad TINYINT(1) NOT NULL DEFAULT 0
            """
        )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.statistics
        WHERE table_schema = %s
            AND table_name = 'registro_a'
            AND index_name = 'idx_registro_a_nuevos'
        """,
        (DB_CONFIG["database"],),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            CREATE INDEX idx_registro_a_nuevos
            ON registro_a (nuevos(191))
            """
        )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
            nuevos VARCHAR(255) NOT NULL PRIMARY KEY,
            mortalidad TINYINT(1) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(f"TRUNCATE TABLE {STAGING_TABLE}")


def fetch_patient_texts(cursor: MySQLCursor) -> list[PatientText]:
    cursor.execute("SET SESSION group_concat_max_len = 1024 * 1024")
    cursor.execute(
        """
        SELECT
            TRIM(nuevos) AS nuevos,
            GROUP_CONCAT(DISTINCT NULLIF(TRIM(resclin), '') SEPARATOR '\n\n') AS texto
        FROM registro_a
        WHERE nuevos IS NOT NULL
            AND TRIM(nuevos) <> ''
            AND resclin IS NOT NULL
            AND TRIM(resclin) <> ''
        GROUP BY TRIM(nuevos)
        """
    )
    rows = cursor.fetchall()
    return [PatientText(nuevos=row[0], text=row[1] or "") for row in rows]


def sentence_has_positive_pattern(sentence_text: str) -> bool:
    if not sentence_text:
        return False

    lowered = sentence_text.lower()
    if any(phrase in lowered for phrase in EXCLUSION_PHRASES):
        return False

    return any(pattern.search(sentence_text) for pattern in POSITIVE_PATTERNS)


def sentence_has_negation(token_index: int, sentence_tokens: list[str]) -> bool:
    start = max(0, token_index - 4)
    context = " ".join(sentence_tokens[start : token_index + 1])
    return bool(NEGATION_PATTERN.search(context))


def detect_mortality(doc) -> int:
    for sentence in doc.sents:
        sentence_text = sentence.text.strip()
        if not sentence_text:
            continue

        lowered = sentence_text.lower()
        if any(phrase in lowered for phrase in EXCLUSION_PHRASES):
            continue

        tokens = [token.text.lower() for token in sentence]

        for index, token in enumerate(sentence):
            token_text = token.text.lower()
            lemma = token.lemma_.lower()

            if lemma in DEATH_LEMMAS or token_text in DEATH_NOUNS:
                if sentence_has_negation(index, tokens):
                    continue
                return 1

        if sentence_has_positive_pattern(sentence_text):
            return 1

    return 0


def score_patients(nlp, patients: Iterable[PatientText]) -> list[tuple[str, int]]:
    results: list[tuple[str, int]] = []

    for doc, patient in zip(
        nlp.pipe((patient.text for patient in patients), batch_size=BATCH_SIZE),
        patients,
        strict=True,
    ):
        results.append((patient.nuevos, detect_mortality(doc)))

    return results


def write_scores(cursor: MySQLCursor, scores: list[tuple[str, int]]) -> None:
    cursor.executemany(
        f"""
        INSERT INTO {STAGING_TABLE} (nuevos, mortalidad)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE mortalidad = VALUES(mortalidad)
        """,
        scores,
    )

    cursor.execute(
        f"""
        UPDATE registro_a r
        JOIN {STAGING_TABLE} m ON m.nuevos = r.nuevos
        SET r.mortalidad = m.mortalidad
        """
    )


def print_summary(cursor: MySQLCursor) -> None:
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT TRIM(nuevos)) AS pacientes,
            COUNT(DISTINCT CASE WHEN mortalidad = 1 THEN TRIM(nuevos) END) AS pacientes_mortalidad,
            SUM(mortalidad = 1) AS filas_mortalidad
        FROM registro_a
        WHERE nuevos IS NOT NULL
            AND TRIM(nuevos) <> ''
        """
    )
    pacientes, pacientes_mortalidad, filas_mortalidad = cursor.fetchone()
    print(f"Pacientes procesados: {pacientes}")
    print(f"Pacientes con mortalidad detectada: {pacientes_mortalidad}")
    print(f"Filas con mortalidad=1: {filas_mortalidad}")


def main() -> None:
    started_at = time.time()
    print(f"Cargando modelo spaCy: {NLP_MODEL}")
    nlp = spacy.load(NLP_MODEL, disable=["ner", "textcat"])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("Preparando esquema en MySQL...")
        ensure_schema(cursor)
        conn.commit()

        print("Extrayendo resúmenes clínicos agrupados por paciente...")
        patients = fetch_patient_texts(cursor)
        print(f"Pacientes con texto clínico: {len(patients)}")

        print("Detectando mortalidad con spaCy...")
        scores = score_patients(nlp, patients)

        print("Actualizando tabla registro_a...")
        write_scores(cursor, scores)
        conn.commit()

        print_summary(cursor)
        elapsed = time.time() - started_at
        print(f"Proceso completado en {elapsed:.2f} segundos")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
