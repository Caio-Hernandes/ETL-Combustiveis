
from pathlib import Path
import pandas as pd


def main():
    # Localiza o CSV
    arquivos = list(Path("data/bronze").glob("*.csv"))

    if not arquivos:
        raise FileNotFoundError("Nenhum CSV encontrado na Bronze.")

    arquivo = arquivos[0]

    print(f"Arquivo encontrado: {arquivo}")

    try:
        df = pd.read_csv(
            arquivo,
            sep=";",
            encoding="utf-8-sig",
            nrows=5
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            arquivo,
            sep=";",
            encoding="latin-1",
            nrows=5
        )

    print("\nCOLUNAS:")
    print(df.columns.tolist())

    print("\nTIPOS:")
    print(df.dtypes)

    print("\nAMOSTRA:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
