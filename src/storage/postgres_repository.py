
import os
from io import StringIO
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


class PostgresRepository:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env")

        self.connection_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5433")),
            "dbname": os.getenv("POSTGRES_DB", "combustiveis_dw"),
            "user": os.getenv("POSTGRES_USER", "etl_user"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }

        if not self.connection_params["password"]:
            raise ValueError("POSTGRES_PASSWORD nao configurada.")

    def load_dataframe(self, df: pd.DataFrame, sql: str):
        buffer = StringIO()
        df.to_csv(buffer, index=False, na_rep="")
        buffer.seek(0)

        with psycopg.connect(**self.connection_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TEMP TABLE stage_preco (
                        regiao TEXT,
                        uf TEXT,
                        municipio TEXT,
                        revenda TEXT,
                        cnpj TEXT,
                        combustivel TEXT,
                        data_coleta DATE,
                        preco_venda NUMERIC(12,4),
                        unidade_medida TEXT,
                        bandeira TEXT
                    ) ON COMMIT DROP
                """)

                with cursor.copy("""
                    COPY stage_preco (
                        regiao, uf, municipio, revenda,
                        cnpj, combustivel, data_coleta,
                        preco_venda, unidade_medida, bandeira
                    )
                    FROM STDIN
                    WITH (FORMAT CSV, HEADER TRUE)
                """) as copy:
                    while bloco := buffer.read(1024 * 1024):
                        copy.write(bloco)

                cursor.execute(sql)

    def count_facts(self) -> int:
        with psycopg.connect(**self.connection_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM gold.fato_preco"
                )
                return cursor.fetchone()[0]
