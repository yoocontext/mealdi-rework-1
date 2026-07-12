import ast
from pathlib import Path

import pytest

source_root = Path("src")


def _project_imports(*, path: Path) -> set[str]:
    imports: set[str] = set()
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    return imports


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    [
        ("application", {"app", "bootstrap", "delivery", "infra"}),
        ("delivery", {"app", "bootstrap", "infra"}),
        ("infra", {"app", "bootstrap", "delivery"}),
    ],
)
def test_layer_import_boundaries(*, layer: str, forbidden: set[str]) -> None:
    violations: list[str] = []
    for path in (source_root / layer).rglob("*.py"):
        imported = _project_imports(path=path) & forbidden
        if imported:
            violations.append(f"{path}: {', '.join(sorted(imported))}")

    assert violations == []


def test_no_seedwork_or_modules_directories() -> None:
    forbidden = {
        path.name
        for path in source_root.rglob("*")
        if path.is_dir() and path.name in {"modules", "seedwork"}
    }

    assert forbidden == set()


def test_data_mappers_never_commit() -> None:
    commits: list[str] = []
    for path in (source_root / "infra" / "dm").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "commit":
                    commits.append(f"{path}:{node.lineno}")

    assert commits == []


def test_data_mappers_do_not_depend_on_async_session() -> None:
    violations = [
        str(path)
        for path in (source_root / "infra" / "dm").rglob("*.py")
        if "AsyncSession" in path.read_text()
    ]

    assert violations == []


def test_use_cases_do_not_mix_exception_translation_into_scenarios() -> None:
    violations: list[str] = []
    for path in (source_root / "application" / "use_cases").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                violations.append(f"{path}:{node.lineno}")

    assert violations == []


def test_transaction_manager_owns_required_session_operations() -> None:
    path = source_root / "infra" / "common" / "transaction.py"
    tree = ast.parse(path.read_text())
    manager = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TransactionManager"
    )
    methods = {
        node.name
        for node in manager.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }

    assert {"add", "add_all", "flush", "refresh", "commit"} <= methods


def test_every_use_case_has_a_class_docstring() -> None:
    missing: list[str] = []
    for path in (source_root / "application" / "use_cases").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.endswith("Uc"):
                if ast.get_docstring(node) is None:
                    missing.append(f"{path}:{node.name}")

    assert missing == []


def test_all_dataclasses_are_keyword_only() -> None:
    missing: list[str] = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Name):
                    continue
                if decorator.func.id != "dataclass":
                    continue

                keyword_only = next(
                    (
                        keyword.value
                        for keyword in decorator.keywords
                        if keyword.arg == "kw_only"
                    ),
                    None,
                )
                if not isinstance(keyword_only, ast.Constant):
                    missing.append(f"{path}:{node.name}")
                elif keyword_only.value is not True:
                    missing.append(f"{path}:{node.name}")

    assert missing == []


def test_project_owned_parameters_are_keyword_only() -> None:
    framework_callbacks = {
        ("src/bootstrap/main.py", "lifespan"),
        (
            "src/delivery/api/v1/http/exceptions.py",
            "handle_application_error",
        ),
    }
    violations: list[str] = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if (str(path), node.name) in framework_callbacks:
                continue

            positional = [
                argument.arg
                for argument in node.args.posonlyargs + node.args.args
                if argument.arg not in {"self", "cls"}
            ]
            if positional:
                violations.append(
                    f"{path}:{node.lineno}:{node.name}({', '.join(positional)})",
                )

    assert violations == []
