
from pathlib import Path

import pandas as pd

from src.storage.postgres_repository import PostgresRepository


class WarehouseLoader:
    COLUMNS = [
        "regiao",
        "uf",
        "municipio",
        "revenda",
        "cnpj",
        "combustivel",
        "data_coleta",
        "preco_venda",
        "unidade_medida",
        "bandeira",
    ]

    REQUIRED_COLUMNS = [
        "uf",
        "municipio",
        "cnpj",
        "combustivel",
        "data_coleta",
        "preco_venda",
        "unidade_medida",
    ]

    def __init__(self):
        project_root = Path(__file__).resolve().parents[2]

        self.silver_dir = project_root / "data" / "silver"
        self.sql_path = project_root / "sql" / "load_gold.sql"
        self.repository = PostgresRepository()

    def load(self):
        arquivos = sorted(
            self.silver_dir.glob("ano=*/mes=*/*.parquet")
        )

        if not arquivos:
            raise FileNotFoundError(
                "Nenhum arquivo Parquet encontrado na Silver."
            )

        sql = self.sql_path.read_text(encoding="utf-8")

        for arquivo in arquivos:
            df = pd.read_parquet(arquivo)

            if df.empty:
                continue

            df = df[self.COLUMNS].copy()

            chaves = ["cnpj", "combustivel", "data_coleta"]

            if df.duplicated(subset=chaves).any():
                raise ValueError(
                    f"Registros duplicados em {arquivo}"
                )

            if df[self.REQUIRED_COLUMNS].isna().any().any():
                raise ValueError(
                    f"Campos obrigatorios nulos em {arquivo}"
                )

            if df["preco_venda"].le(0).any():
                raise ValueError(
                    f"Precos invalidos em {arquivo}"
                )

            df["data_coleta"] = (
                df["data_coleta"].dt.strftime("%Y-%m-%d")
            )

            self.repository.load_dataframe(df, sql)

            print(
                f"Carregado: {arquivo.parent.name} "
                f"({len(df)} registros)"
            )

        total = self.repository.count_facts()

        print(f"\nTotal de registros na Gold: {total}")


if __name__ == "__main__":
    WarehouseLoader().load()
