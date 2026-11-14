
import argparse
import subprocess
from pathlib import Path


class DatabaseInitializer:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.schema_path = self.project_root / "sql" / "schema.sql"
        self.views_path = self.project_root / "sql" / "views_gold.sql"

    def initialize(self, reset=False):
        if not self.schema_path.is_file():
            raise FileNotFoundError(
                f"Schema nao encontrado: {self.schema_path}"
            )

        if not self.views_path.is_file():
            raise FileNotFoundError(
                f"Views SQL nao encontradas: {self.views_path}"
            )

        sql = (
            self.schema_path.read_bytes()
            + b"\n"
            + self.views_path.read_bytes()
        )

        if reset:
            print("Removendo schema Gold existente...", flush=True)
            sql = b"DROP SCHEMA IF EXISTS gold CASCADE;\n" + sql

        command = [
            "docker", "compose", "exec", "-T",
            "postgres",
            "psql", "-X", "-1",
            "-v", "ON_ERROR_STOP=1",
            "-U", "etl_user",
            "-d", "combustiveis_dw",
        ]

        subprocess.run(
            command,
            input=sql,
            cwd=self.project_root,
            check=True,
        )

        print("Schema Gold inicializado com sucesso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga e recria todas as tabelas da Gold"
    )

    args = parser.parse_args()

    DatabaseInitializer().initialize(reset=args.reset)
