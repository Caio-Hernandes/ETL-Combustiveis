
import logging
from pathlib import Path

import pandas as pd

from src.storage.postgres_repository import PostgresRepository


logger = logging.getLogger(__name__)


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

    def __init__(self, repository=None, silver_dir=None):
        project_root = Path(__file__).resolve().parents[2]

        self.silver_dir = Path(silver_dir) if silver_dir is not None else project_root / "data" / "silver"
        self.sql_path = project_root / "sql" / "load_gold.sql"
        self.repository = repository if repository is not None else PostgresRepository()

    def load(
        self,
        arquivos: list[Path] | None = None,
        substituir_meses: bool = False,
    ):
        if arquivos is None:
            arquivos = sorted(
                self.silver_dir.glob("ano=*/mes=*/*.parquet")
            )
        else:
            arquivos = sorted(Path(a) for a in arquivos)

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

            periodo = None

            if substituir_meses:
                meses = (
                    df["data_coleta"]
                    .dt.to_period("M")
                    .unique()
                )

                if len(meses) != 1:
                    raise ValueError(
                        f"Arquivo deve conter apenas um mes: {arquivo}"
                    )

                mes = meses[0]

                inicio = mes.start_time.date()
                fim = (mes + 1).start_time.date()

                periodo = (inicio, fim)

            df["data_coleta"] = (
                df["data_coleta"].dt.strftime("%Y-%m-%d")
            )

            self.repository.load_dataframe(
                df,
                sql,
                periodo=periodo,
            )

            logger.info("Carregado: %s (%s registros)", arquivo, len(df))

        total = self.repository.count_facts()

        logger.info("Total de registros na Gold: %s", total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    WarehouseLoader().load()
