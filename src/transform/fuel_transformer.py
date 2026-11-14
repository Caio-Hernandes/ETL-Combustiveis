
from pathlib import Path

import pandas as pd


class FuelTransformer:
    COLUMN_MAPPING = {
        "Regiao - Sigla": "regiao",
        "Estado - Sigla": "uf",
        "Municipio": "municipio",
        "Revenda": "revenda",
        "CNPJ da Revenda": "cnpj",
        "Produto": "combustivel",
        "Data da Coleta": "data_coleta",
        "Valor de Venda": "preco_venda",
        "Unidade de Medida": "unidade_medida",
        "Bandeira": "bandeira",
    }

    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path)

    def extract(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(
                self.source_path,
                sep=";",
                encoding="utf-8-sig",
                dtype="string",
            )
        except UnicodeDecodeError:
            df = pd.read_csv(
                self.source_path,
                sep=";",
                encoding="latin-1",
                dtype="string",
            )

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        missing_columns = (
            set(self.COLUMN_MAPPING) - set(df.columns)
        )

        if missing_columns:
            raise ValueError(
                f"Colunas ausentes: {sorted(missing_columns)}"
            )

        df = df[list(self.COLUMN_MAPPING)].copy()

        df = df.rename(columns=self.COLUMN_MAPPING)

        # Padronização de texto
        text_columns = [
            "regiao",
            "uf",
            "municipio",
            "revenda",
            "cnpj",
            "combustivel",
            "unidade_medida",
            "bandeira",
        ]

        for column in text_columns:
            df[column] = df[column].str.strip()

        df["combustivel"] = df["combustivel"].str.upper()
        df["uf"] = df["uf"].str.upper()

        # Conversão de data
        df["data_coleta"] = pd.to_datetime(
            df["data_coleta"],
            format="%d/%m/%Y",
            errors="coerce",
        )

        # Conversão de preço: "6,29" -> 6.29
        df["preco_venda"] = pd.to_numeric(
            df["preco_venda"].str.replace(
                ",", ".", regex=False
            ),
            errors="coerce",
        )

        return df
