import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    BUSINESS_KEY = ["cnpj", "combustivel", "data_coleta"]

    REQUIRED_COLUMNS = [
        "uf",
        "municipio",
        "cnpj",
        "combustivel",
        "data_coleta",
        "preco_venda",
        "unidade_medida",
    ]

    def validate(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:

        missing_columns = (
            set(self.REQUIRED_COLUMNS) - set(df.columns)
        )

        if missing_columns:
            raise ValueError(
                f"Colunas ausentes: {sorted(missing_columns)}"
            )

        empty_mask = df.isna().all(axis=1)

        missing_required = (
            df[self.REQUIRED_COLUMNS].isna().any(axis=1)
        )

        invalid_price = (
            df["preco_venda"].le(0).fillna(False)
        )

        invalid_mask = missing_required | invalid_price
        duplicates = pd.Series(False, index=df.index)
        duplicates.loc[~invalid_mask] = df.loc[~invalid_mask].duplicated(
            subset=self.BUSINESS_KEY, keep="first"
        )
        invalid_mask = invalid_mask | duplicates

        valid_df = df.loc[~invalid_mask].copy()
        rejected_df = df.loc[invalid_mask].copy()

        rejected_df["motivo_rejeicao"] = "Campo obrigatorio ausente"

        rejected_df.loc[
            empty_mask.loc[rejected_df.index],
            "motivo_rejeicao"
        ] = "Linha completamente vazia"

        rejected_df.loc[
            invalid_price.loc[rejected_df.index],
            "motivo_rejeicao"
        ] = "Preco nao positivo"

        rejected_df.loc[duplicates.loc[rejected_df.index], "motivo_rejeicao"] = "duplicata"

        logger.info("Linhas recebidas: %s", len(df))
        logger.info("Linhas vazias: %s", int(empty_mask.sum()))
        logger.info("Registros validos: %s", len(valid_df))
        logger.info("Registros rejeitados: %s", len(rejected_df))

        return valid_df, rejected_df