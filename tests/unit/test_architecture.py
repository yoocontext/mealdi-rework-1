import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path("src")


def _imports(*, path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    return imports


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    [
        ("application", {"bootstrap", "delivery", "infra"}),
        ("delivery", {"bootstrap", "infra"}),
        ("infra", {"bootstrap", "delivery"}),
    ],
)
def test_layers_only_import_allowed_dependencies(
    *,
    layer: str,
    forbidden: set[str],
) -> None:
    violations = [
        f"{path}: {', '.join(sorted(imported))}"
        for path in (SOURCE_ROOT / layer).rglob("*.py")
        if (imported := _imports(path=path) & forbidden)
    ]

    assert violations == []


def test_only_use_cases_commit_application_transactions() -> None:
    violations: list[str] = []

    for path in SOURCE_ROOT.rglob("*.py"):
        if path.is_relative_to(SOURCE_ROOT / "application" / "use_cases"):
            continue
        if path == SOURCE_ROOT / "infra" / "common" / "transaction.py":
            continue

        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "commit"
            ):
                violations.append(f"{path}:{node.lineno}")

    assert violations == []


def test_data_mappers_cannot_access_raw_database_sessions() -> None:
    violations: list[str] = []

    for path in (SOURCE_ROOT / "infra" / "dm").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "sqlalchemy.ext.asyncio":
                continue
            if any(alias.name == "AsyncSession" for alias in node.names):
                violations.append(f"{path}:{node.lineno}")

    assert violations == []
