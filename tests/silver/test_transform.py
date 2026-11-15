import pandas as pd
import pytest

from src.transform.fuel_transformer import FuelTransformer
from src.transform.data_validator import DataValidator


@pytest.fixture
def raw():
    return pd.DataFrame([{
        "Regiao - Sigla": " SE ", "Estado - Sigla": " sp ",
        "Municipio": "SAO PAULO", "Revenda": "POSTO", "CNPJ da Revenda": "001",
        "Produto": "gasolina", "Data da Coleta": "01/01/2025",
        "Valor de Venda": "6,29", "Unidade de Medida": "R$ / litro", "Bandeira": "BRANCA",
    }])


def transform(raw):
    return FuelTransformer("unused.csv").transform(raw)


def test_decimal_and_normalization(raw):
    df = transform(raw)
    assert df.loc[0, "preco_venda"] == pytest.approx(6.29)
    assert df.loc[0, "data_coleta"] == pd.Timestamp("2025-01-01")
    assert df.loc[0, "uf"] == "SP"
    assert df.loc[0, "combustivel"] == "GASOLINA"
    assert df.loc[0, "cnpj"] == "001"


@pytest.mark.parametrize("column,value", [
    ("Valor de Venda", "-1,00"), ("Valor de Venda", "0"),
    ("Valor de Venda", "invalido"), ("Data da Coleta", "31/02/2025"),
    ("CNPJ da Revenda", None), ("Municipio", "   "),
])
def test_invalid_rows_are_rejected(raw, column, value):
    raw.loc[0, column] = value
    valid, rejected = DataValidator().validate(transform(raw))
    assert valid.empty
    assert len(rejected) == 1
    assert rejected["motivo_rejeicao"].notna().all()


def test_duplicates_use_business_key(raw):
    raw = pd.concat([raw, raw, raw], ignore_index=True)
    raw.loc[1, "Valor de Venda"] = "7,00"
    raw.loc[2, "Data da Coleta"] = "02/01/2025"
    valid, rejected = DataValidator().validate(transform(raw))
    assert len(valid) == 2
    assert len(rejected) == 1
    assert rejected.iloc[0]["motivo_rejeicao"] == "duplicata"
    assert valid.iloc[0]["preco_venda"] == pytest.approx(6.29)


def test_invalid_first_row_does_not_discard_valid_duplicate(raw):
    raw = pd.concat([raw, raw], ignore_index=True)
    raw.loc[0, "Valor de Venda"] = "-1"
    valid, rejected = DataValidator().validate(transform(raw))
    assert len(valid) == len(rejected) == 1
    assert valid.iloc[0]["preco_venda"] == pytest.approx(6.29)


def test_missing_columns_raise(raw):
    with pytest.raises(ValueError, match="Colunas ausentes"):
        transform(raw.drop(columns="Produto"))
