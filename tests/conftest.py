import pytest


def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Use --run-integration com banco e Silver de teste"))
