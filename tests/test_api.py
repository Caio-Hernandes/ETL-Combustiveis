import warnings

from src.api.main import app


def test_monthly_route_and_operation_ids_are_unique():
    routes = [route for route in app.routes if getattr(route, "path", None) == "/precos/mensais"]
    assert len(routes) == 1
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        schema = app.openapi()
    ids = [operation["operationId"] for path in schema["paths"].values() for operation in path.values()]
    assert len(ids) == len(set(ids))
