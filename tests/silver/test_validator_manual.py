from pathlib import Path

from src.transform.fuel_transformer import FuelTransformer
from src.transform.data_validator import DataValidator
from src.storage.parquet_repository import ParquetRepository
import pandas as pd

arquivo = next(Path("data/bronze").glob("*.csv"))

transformer = FuelTransformer(arquivo)
validator = DataValidator()

df = transformer.transform(transformer.extract())

validos, rejeitados = validator.validate(df)

print("\nRESULTADO DA VALIDACAO")
print(f"Total: {len(df)}")
print(f"Validos: {len(validos)}")
print(f"Rejeitados: {len(rejeitados)}")

print("\nMOTIVOS DE REJEICAO:")
print(rejeitados["motivo_rejeicao"].value_counts())

assert len(validos) + len(rejeitados) == len(df)

repository = ParquetRepository("data/silver")

arquivos = repository.save(validos)

print("\nARQUIVOS PARQUET GERADOS:")

for arquivo in arquivos:
    print(arquivo)

total_parquet = 0

for arquivo in arquivos:
    df_parquet = pd.read_parquet(arquivo)

    print(f"{arquivo}: {len(df_parquet)} registros")

    total_parquet += len(df_parquet)

print(f"\nTotal original valido: {len(validos)}")
print(f"Total salvo em Parquet: {total_parquet}")

assert total_parquet == len(validos), (
    "A quantidade de registros não corresponde!"
)

print("\nIntegridade dos registros confirmada!")