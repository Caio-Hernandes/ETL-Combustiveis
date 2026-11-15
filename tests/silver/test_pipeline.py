from unittest.mock import Mock

import pandas as pd
import pytest

from src.main import processar_arquivo
from src.storage.parquet_repository import ParquetRepository
from src.extract.anp_extractor import ANPExtractor
from src.transform.data_validator import DataValidator
from src.transform.fuel_transformer import FuelTransformer


@pytest.mark.parametrize("all_invalid", [False, True])
def test_rejected_persist_before_gold(tmp_path, all_invalid):
    row = {column: "X" for column in FuelTransformer.COLUMN_MAPPING}
    row.update({"Data da Coleta": "01/01/2025", "Valor de Venda": "-1" if all_invalid else "6,29"})
    invalid = dict(row, **{"Valor de Venda": "-2"})
    source = tmp_path / "input.csv"
    pd.DataFrame([row, invalid]).to_csv(source, sep=";", index=False)
    repository = Mock()
    repository.file_processed.return_value = False
    warehouse = Mock()
    kwargs = dict(
        origem=source, repository=repository,
        extractor=ANPExtractor(tmp_path / "bronze"), validator=DataValidator(),
        parquet_repository=ParquetRepository(tmp_path / "silver"),
        warehouse=warehouse, rejected_dir=tmp_path / "rejected",
    )
    if all_invalid:
        with pytest.raises(ValueError, match="Nenhum registro valido"):
            processar_arquivo(**kwargs)
        warehouse.load.assert_not_called()
        repository.register_file.assert_not_called()
    else:
        assert processar_arquivo(**kwargs)
        warehouse.load.assert_called_once()
        repository.register_file.assert_called_once()
        silver = next((tmp_path / "silver").rglob("*.parquet"))
        assert len(pd.read_parquet(silver)) == 1
    rejected = pd.read_parquet(next((tmp_path / "rejected").glob("*.parquet")))
    assert len(rejected) == (2 if all_invalid else 1)
    assert rejected["motivo_rejeicao"].notna().all()
