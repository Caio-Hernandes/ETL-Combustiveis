
import argparse
import logging
from pathlib import Path

from src.extract.anp_extractor import ANPExtractor
from src.transform.fuel_transformer import FuelTransformer
from src.transform.data_validator import DataValidator
from src.storage.parquet_repository import ParquetRepository
from src.warehouse.warehouse_loader import WarehouseLoader


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Pipeline ETL de precos de combustiveis da ANP"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Caminho do CSV original da ANP"
    )

    args = parser.parse_args()

    # 1. BRONZE
    logger.info("Iniciando camada Bronze...")

    extractor = ANPExtractor(Path("data/bronze"))
    destination = extractor.ingest(args.file)

    logger.info("Arquivo armazenado em: %s", destination)

    # 2. TRANSFORMACAO
    logger.info("Iniciando transformacao dos dados...")

    transformer = FuelTransformer(destination)

    df_raw = transformer.extract()
    df_transformado = transformer.transform(df_raw)

    logger.info(
        "Registros transformados: %s",
        len(df_transformado)
    )

    # 3. VALIDACAO
    logger.info("Validando os registros...")

    validator = DataValidator()

    validos, rejeitados = validator.validate(df_transformado)

    logger.info("Validos: %s", len(validos))
    logger.info("Rejeitados: %s", len(rejeitados))

    if validos.empty:
        raise ValueError(
            "Nenhum registro valido encontrado. Pipeline interrompido."
        )

    # 4. SILVER
    logger.info("Persistindo camada Silver...")

    parquet_repository = ParquetRepository("data/silver")
    arquivos = parquet_repository.save(validos)

    logger.info(
        "Arquivos Parquet gerados: %s",
        len(arquivos)
    )

    # 5. GOLD
    logger.info("Iniciando carga da Gold...")

    warehouse = WarehouseLoader()
    warehouse.load()

    logger.info("Pipeline ETL finalizado com sucesso!")


if __name__ == "__main__":
    main()
