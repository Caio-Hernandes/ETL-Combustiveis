import hashlib
from unittest.mock import Mock

import pytest

from src.extract import anp_extractor
from src.extract.anp_extractor import ANPExtractor


@pytest.fixture
def csv_file(tmp_path):
    source = tmp_path / "precos.csv"
    source.write_bytes(b"Estado - Sigla;Valor de Venda\r\nSP;6,29\r\n")
    return source


def test_ingest_preserves_csv_and_sha256(tmp_path, csv_file):
    original = csv_file.read_bytes()
    extractor = ANPExtractor(tmp_path / "bronze")

    destination = extractor.ingest(csv_file)

    assert destination == tmp_path / "bronze" / csv_file.name
    assert destination.read_bytes() == original
    assert csv_file.read_bytes() == original
    assert extractor.calculate_hash(destination) == hashlib.sha256(original).hexdigest()


def test_reingest_identical_csv_does_not_copy_again(tmp_path, csv_file, monkeypatch):
    extractor = ANPExtractor(tmp_path / "bronze")
    destination = extractor.ingest(csv_file)
    copy = Mock(side_effect=AssertionError("Arquivo identico nao deve ser copiado"))
    monkeypatch.setattr(anp_extractor, "copy2", copy)

    assert extractor.ingest(csv_file) == destination
    copy.assert_not_called()
    assert list(extractor.bronze_dir.iterdir()) == [destination]


def test_same_filename_with_different_content_preserves_bronze(tmp_path, csv_file):
    extractor = ANPExtractor(tmp_path / "bronze")
    destination = extractor.ingest(csv_file)
    original = destination.read_bytes()
    csv_file.write_bytes(b"Estado - Sigla;Valor de Venda\nSP;7,00\n")

    with pytest.raises(FileExistsError):
        extractor.ingest(csv_file)

    assert destination.read_bytes() == original


def test_missing_csv_raises_without_creating_data(tmp_path):
    extractor = ANPExtractor(tmp_path / "bronze")

    with pytest.raises(FileNotFoundError):
        extractor.ingest(tmp_path / "missing.csv")

    assert not list(extractor.bronze_dir.iterdir())


def test_non_csv_is_rejected(tmp_path):
    source = tmp_path / "precos.txt"
    source.write_text("SP;6,29", encoding="utf-8")
    extractor = ANPExtractor(tmp_path / "bronze")

    with pytest.raises(ValueError, match="CSV"):
        extractor.ingest(source)

    assert not list(extractor.bronze_dir.iterdir())


def test_corrupted_copy_is_removed_and_source_is_preserved(tmp_path, csv_file, monkeypatch):
    extractor = ANPExtractor(tmp_path / "bronze")
    original = csv_file.read_bytes()

    def corrupt_copy(source, destination):
        destination.write_bytes(b"copia incompleta")

    monkeypatch.setattr(anp_extractor, "copy2", corrupt_copy)

    with pytest.raises(IOError, match="integridade"):
        extractor.ingest(csv_file)

    assert not (extractor.bronze_dir / csv_file.name).exists()
    assert csv_file.read_bytes() == original
