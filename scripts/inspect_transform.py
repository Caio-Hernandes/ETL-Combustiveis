
from pathlib import Path

from src.transform.fuel_transformer import FuelTransformer



def main():
    arquivo = next(Path("data/bronze").glob("*.csv"))

    transformer = FuelTransformer(arquivo)

    df_original = transformer.extract()
    df_tratado = transformer.transform(df_original)

    print("\nTOTAL DE REGISTROS:")
    print(len(df_tratado))

    print("\nCOLUNAS:")
    print(df_tratado.columns.tolist())

    print("\nTIPOS:")
    print(df_tratado.dtypes)

    print("\nAMOSTRA:")
    print(df_tratado.head().to_string(index=False))

    print("\nVALORES NULOS:")
    print(df_tratado.isna().sum())
    print("\nLINHAS COMPLETAMENTE VAZIAS:")
    print(df_tratado.isna().all(axis=1).sum())

    print("\nLINHAS PARCIALMENTE NULAS:")
    parcialmente_nulas = (
        df_tratado.isna().any(axis=1)
        & ~df_tratado.isna().all(axis=1)
    )
    print(parcialmente_nulas.sum())

    print("\nDUPLICATAS EXATAS:")
    print(df_tratado.duplicated().sum())

    print("\nDUPLICATAS POR CHAVE DE NEGÓCIO:")
    chave = ["cnpj", "combustivel", "data_coleta"]
    print(df_tratado.duplicated(subset=chave).sum())

    print("\nPREÇOS INVÁLIDOS:")
    print((df_tratado["preco_venda"] <= 0).sum())

    print("\nPERÍODO DOS DADOS:")
    print(df_tratado["data_coleta"].min())
    print(df_tratado["data_coleta"].max())

    print("\nCOMBUSTÍVEIS:")
    print(df_tratado["combustivel"].value_counts())
    print("\nLINHAS TOTALMENTE VAZIAS:")
    print(df_tratado.isna().all(axis=1).sum())

    print("\nLINHAS PARCIALMENTE NULAS:")
    print(
        (
            df_tratado.isna().any(axis=1)
            & ~df_tratado.isna().all(axis=1)
        ).sum()
    )

    print("\nDUPLICATAS EXATAS:")
    print(df_tratado.duplicated().sum())

    print("\nDUPLICATAS POR CNPJ + COMBUSTÍVEL + DATA:")
    print(
        df_tratado.duplicated(
            subset=["cnpj", "combustivel", "data_coleta"]
        ).sum()
    )


if __name__ == "__main__":
    main()
