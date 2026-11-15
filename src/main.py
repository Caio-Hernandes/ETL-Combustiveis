
import argparse
import hashlib
import logging
from pathlib import Path

from src.extract.anp_extractor import ANPExtractor
from src.transform.fuel_transformer import FuelTransformer
from src.transform.data_validator import DataValidator
from src.storage.parquet_repository import ParquetRepository
from src.storage.postgres_repository import PostgresRepository
from src.warehouse.warehouse_loader import WarehouseLoader


logger = logging.getLogger(__name__)


def calcular_hash(caminho: Path) -> str:
    sha256 = hashlib.sha256()

    with caminho.open("rb") as arquivo:
        for bloco in iter(
            lambda: arquivo.read(1024 * 1024),
            b"",
        ):
            sha256.update(bloco)

    return sha256.hexdigest()


def processar_arquivo(
    origem: Path,
    repository: PostgresRepository,
    force: bool = False,
    *,
    extractor=None,
    validator=None,
    parquet_repository=None,
    warehouse=None,
    rejected_dir: Path = Path("data/rejected"),
) -> bool:
    logger.info("Processando arquivo: %s", origem.name)

    # 1. CONTROLE INCREMENTAL
    logger.info("Verificando historico de processamento...")

    hash_arquivo = calcular_hash(origem)

    if not force and repository.file_processed(hash_arquivo):
        logger.info(
            "Arquivo ja processado: %s. Ignorando.",
            origem.name,
        )
        return False

    # 2. BRONZE
    logger.info("Iniciando camada Bronze...")

    extractor = extractor if extractor is not None else ANPExtractor(Path("data/bronze"))
    destination = extractor.ingest(origem)

    logger.info("Arquivo armazenado em: %s", destination)

    # 3. TRANSFORMACAO
    logger.info("Iniciando transformacao dos dados...")

    transformer = FuelTransformer(destination)

    df_raw = transformer.extract()
    df_transformado = transformer.transform(df_raw)

    logger.info(
        "Registros transformados: %s",
        len(df_transformado),
    )

    # 4. VALIDACAO
    logger.info("Validando os registros...")

    validator = validator if validator is not None else DataValidator()

    validos, rejeitados = validator.validate(df_transformado)

    logger.info("Validos: %s", len(validos))
    logger.info("Rejeitados: %s", len(rejeitados))

    rejected_dir.mkdir(parents=True, exist_ok=True)
    destino_rejeitados = rejected_dir / f"{origem.stem}-{hash_arquivo}.parquet"
    rejeitados.to_parquet(destino_rejeitados, index=False)
    logger.info("Rejeitados persistidos em: %s", destino_rejeitados)

    if validos.empty:
        raise ValueError(
            f"Nenhum registro valido encontrado em {origem.name}."
        )

    # 5. SILVER
    logger.info("Persistindo camada Silver...")

    parquet_repository = parquet_repository if parquet_repository is not None else ParquetRepository("data/silver")
    arquivos = parquet_repository.save(validos)

    logger.info(
        "Particoes geradas: %s",
        len(arquivos),
    )

    # 6. GOLD
    logger.info("Iniciando carga incremental da Gold...")

    warehouse = warehouse if warehouse is not None else WarehouseLoader(repository=repository)

    warehouse.load(
        arquivos=arquivos,
        substituir_meses=True,
    )

    # 7. REGISTRO DE PROCESSAMENTO
    repository.register_file(
        nome_arquivo=origem.name,
        hash_sha256=hash_arquivo,
        registros_validos=len(validos),
    )

    logger.info(
        "Arquivo processado com sucesso: %s",
        origem.name,
    )

    return True


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Pipeline ETL de precos de combustiveis da ANP"
    )

    grupo = parser.add_mutually_exclusive_group(required=True)

    grupo.add_argument(
        "--file",
        help="Caminho de um CSV da ANP",
    )

    grupo.add_argument(
        "--dir",
        help="Pasta contendo os CSVs da ANP",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Forca o reprocessamento dos arquivos",
    )

    parser.add_argument("--bronze-dir", type=Path, default=Path("data/bronze"))
    parser.add_argument("--silver-dir", type=Path, default=Path("data/silver"))
    parser.add_argument("--rejected-dir", type=Path, default=Path("data/rejected"))

    args = parser.parse_args()

    # SELECAO DOS ARQUIVOS
    if args.file:
        origem = Path(args.file)

        if not origem.is_file():
            parser.error(f"Arquivo nao encontrado: {origem}")

        arquivos = [origem]

    else:
        pasta = Path(args.dir)

        if not pasta.is_dir():
            parser.error(f"Diretorio nao encontrado: {pasta}")

        arquivos = sorted(
            (
                arquivo
                for arquivo in pasta.iterdir()
                if arquivo.is_file()
                and arquivo.suffix.lower() == ".csv"
            ),
            key=lambda arquivo: arquivo.name.lower(),
        )

        if not arquivos:
            parser.error(
                f"Nenhum arquivo CSV encontrado em: {pasta}"
            )

    logger.info(
        "Arquivos encontrados: %s",
        len(arquivos),
    )

    repository = PostgresRepository()

    extractor = ANPExtractor(args.bronze_dir)
    validator = DataValidator()
    parquet_repository = ParquetRepository(args.silver_dir)
    warehouse = WarehouseLoader(repository=repository, silver_dir=args.silver_dir)

    processados = 0
    ignorados = 0

    # PROCESSAMENTO DOS ARQUIVOS
    for origem in arquivos:
        resultado = processar_arquivo(
            origem=origem,
            repository=repository,
            force=args.force,
            extractor=extractor,
            validator=validator,
            parquet_repository=parquet_repository,
            warehouse=warehouse,
            rejected_dir=args.rejected_dir,
        )

        if resultado:
            processados += 1
        else:
            ignorados += 1

    # RESUMO
    logger.info("====================================")
    logger.info("Pipeline ETL finalizado com sucesso!")
    logger.info("Total de arquivos: %s", len(arquivos))
    logger.info("Processados: %s", processados)
    logger.info("Ignorados: %s", ignorados)
    logger.info("====================================")


if __name__ == "__main__":
    main()
