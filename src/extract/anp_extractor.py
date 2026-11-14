
from pathlib import Path
from shutil import copy2
import hashlib
import logging

logger = logging.getLogger(__name__)


class ANPExtractor:
    def __init__(self, bronze_dir: str | Path):
        self.bronze_dir = Path(bronze_dir)
        self.bronze_dir.mkdir(parents=True, exist_ok=True)

    def calculate_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def ingest(self, source_path: str | Path) -> Path:
        source = Path(source_path)

        if not source.is_file():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {source}"
            )

        if source.suffix.lower() != ".csv":
            raise ValueError("O arquivo precisa ser um CSV.")

        destination = self.bronze_dir / source.name

        source_hash = self.calculate_hash(source)

        if destination.exists():
            destination_hash = self.calculate_hash(destination)

            if destination_hash == source_hash:
                logger.info(
                    "Arquivo já existe na Bronze: %s",
                    destination
                )
                return destination

            raise FileExistsError(
                "Já existe um arquivo com esse nome e "
                "conteúdo diferente na Bronze."
            )

        copy2(source, destination)

        destination_hash = self.calculate_hash(destination)

        if source_hash != destination_hash:
            destination.unlink(missing_ok=True)
            raise IOError(
                "Falha na verificação de integridade."
            )

        logger.info("Arquivo ingerido: %s", destination)
        logger.info("SHA-256: %s", destination_hash)

        return destination
