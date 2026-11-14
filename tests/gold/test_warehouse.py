
from pathlib import Path

import psycopg
import pytest
import pyarrow.parquet as pq

from src.storage.postgres_repository import PostgresRepository


@pytest.fixture(scope="module")
def connection():
    repository = PostgresRepository()

    with psycopg.connect(**repository.connection_params) as conn:
        yield conn


def test_total_gold_igual_silver(connection):
    project_root = Path(__file__).resolve().parents[2]
    silver_dir = project_root / "data" / "silver"

    arquivos = list(silver_dir.glob("ano=*/mes=*/*.parquet"))

    assert arquivos, "Nenhum Parquet encontrado na Silver"

    total_silver = sum(
        pq.ParquetFile(arquivo).metadata.num_rows
        for arquivo in arquivos
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM gold.fato_preco")
        total_gold = cursor.fetchone()[0]

    assert total_gold == total_silver, (
        f"Silver: {total_silver}, Gold: {total_gold}"
    )


def test_sem_duplicatas(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                data_coleta,
                revenda_id,
                combustivel_id,
                COUNT(*)
            FROM gold.fato_preco
            GROUP BY
                data_coleta,
                revenda_id,
                combustivel_id
            HAVING COUNT(*) > 1
            LIMIT 1
        """)

        duplicata = cursor.fetchone()

    assert duplicata is None, f"Duplicata encontrada: {duplicata}"


def test_precos_validos(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM gold.fato_preco
            WHERE preco_venda <= 0
               OR preco_venda IS NULL
        """)

        invalidos = cursor.fetchone()[0]

    assert invalidos == 0, (
        f"Encontrados {invalidos} precos invalidos"
    )


def test_integridade_referencial(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM gold.fato_preco f

            LEFT JOIN gold.dim_tempo t
                ON f.data_coleta = t.data

            LEFT JOIN gold.dim_localidade l
                ON f.localidade_id = l.id

            LEFT JOIN gold.dim_combustivel c
                ON f.combustivel_id = c.id

            LEFT JOIN gold.dim_revenda r
                ON f.revenda_id = r.id

            WHERE t.data IS NULL
               OR l.id IS NULL
               OR c.id IS NULL
               OR r.id IS NULL
        """)

        inconsistencias = cursor.fetchone()[0]

    assert inconsistencias == 0, (
        f"Encontradas {inconsistencias} referencias invalidas"
    )
