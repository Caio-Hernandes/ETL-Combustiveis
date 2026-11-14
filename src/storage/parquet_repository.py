
from pathlib import Path

import pandas as pd


class ParquetRepository:
    def __init__(self, silver_dir: str | Path):
        self.silver_dir = Path(silver_dir)

    def save(self, df: pd.DataFrame) -> list[Path]:
        if df["data_coleta"].isna().any():
            raise ValueError("Existem datas inválidas.")

        arquivos = []

        grupos = df.groupby([
            df["data_coleta"].dt.year,
            df["data_coleta"].dt.month,
        ])

        for (ano, mes), dados in grupos:
            pasta = (
                self.silver_dir
                / f"ano={ano}"
                / f"mes={mes:02d}"
            )

            pasta.mkdir(parents=True, exist_ok=True)

            destino = pasta / "combustiveis.parquet"

            dados.to_parquet(
                destino,
                engine="pyarrow",
                index=False,
            )

            arquivos.append(destino)

        return arquivos
