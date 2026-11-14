
import argparse
import logging
from pathlib import Path

from src.extract.anp_extractor import ANPExtractor


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        required=True,
        help="Caminho do CSV original da ANP"
    )

    args = parser.parse_args()

    extractor = ANPExtractor(Path("data/bronze"))
    destination = extractor.ingest(args.file)

    print(f"Arquivo armazenado em: {destination}")


if __name__ == "__main__":
    main()
