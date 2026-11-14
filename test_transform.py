
from pathlib import Path

from src.transform.fuel_transformer import FuelTransformer


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
