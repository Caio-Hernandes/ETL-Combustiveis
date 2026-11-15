import pytest

import subprocess
import sys
from pathlib import Path

import psycopg

from src.storage.postgres_repository import PostgresRepository


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def obter_resumo(repository):
    with psycopg.connect(**repository.connection_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*),
                    SUM(preco_venda)
                FROM gold.fato_preco
            """)

            return cursor.fetchone()


def test_reprocessamento_nao_duplica_dados():
    repository = PostgresRepository()

    antes = obter_resumo(repository)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.warehouse.warehouse_loader",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    depois = obter_resumo(repository)

    assert antes == depois, (
        f"Dados alterados após reprocessamento. "
        f"Antes: {antes}, Depois: {depois}"
    )


pytestmark = pytest.mark.integration
