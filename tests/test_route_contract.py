import json
from pathlib import Path


CONTRACT_PATH = Path(__file__).parent / "contracts" / "route_contract.json"
EXPECTED_BLUEPRINTS = {
    "dashboard",
    "auth",
    "admin",
    "backup",
    "api",
    "categories",
    "topics",
    "contacts",
    "notes",
    "labs",
    "notifications",
    "profile",
    "security",
    "tasks",
}


def load_contract():
    with CONTRACT_PATH.open(encoding="utf-8") as contract_file:
        return json.load(contract_file)


def flatten_expected_routes(contract):
    routes = []
    for blueprint, entries in contract["blueprints"].items():
        for entry in entries:
            routes.append({"blueprint": blueprint, **entry})
    return sorted(routes, key=route_sort_key)


def current_routes(app, ignored_methods):
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        blueprint = rule.endpoint.split(".", 1)[0]
        routes.append(
            {
                "blueprint": blueprint,
                "endpoint": rule.endpoint,
                "rule": rule.rule,
                "methods": sorted(set(rule.methods) - ignored_methods),
            }
        )
    return sorted(routes, key=route_sort_key)


def route_sort_key(route):
    return route["blueprint"], route["rule"], route["endpoint"]


def test_route_map_matches_frozen_contract(app):
    contract = load_contract()
    expected = flatten_expected_routes(contract)
    ignored_methods = set(contract["ignored_methods"])
    actual = current_routes(app, ignored_methods)

    expected_route_map = [
        {key: value for key, value in route.items() if key != "auth"}
        for route in expected
    ]

    assert len(expected) == 72
    assert {route["blueprint"] for route in expected} == EXPECTED_BLUEPRINTS
    assert actual == expected_route_map


def test_route_contract_records_authentication_expectations():
    contract = load_contract()
    routes = flatten_expected_routes(contract)
    allowed_expectations = {"public", "authenticated", "admin", "pending_mfa"}

    assert all(route["auth"] in allowed_expectations for route in routes)
    assert {route["endpoint"] for route in routes if route["auth"] == "admin"}
    assert {route["endpoint"] for route in routes if route["auth"] == "authenticated"}
