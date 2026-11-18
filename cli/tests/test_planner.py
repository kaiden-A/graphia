from __future__ import annotations

from pathlib import Path

from graphia_cli.operations import Catalog
from graphia_cli.planner import STATE_ERROR, STATE_READY, STATE_SKIP, build_plan


def _build(
    paths: list[Path],
    catalog: Catalog,
    *,
    target: str | None = "pdf",
    operation: str | None = None,
    out: Path | None = None,
    recursive: bool = True,
    include_hidden: bool = False,
    overwrite: bool = False,
    max_upload_bytes: int = 25 * 1024 * 1024,
):
    return build_plan(
        paths,
        target=target,
        operation=operation,
        out=out,
        recursive=recursive,
        include_hidden=include_hidden,
        overwrite=overwrite,
        max_upload_bytes=max_upload_bytes,
        catalog=catalog,
    )


def _write(path: Path, data: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_single_file_writes_beside_source(tmp_path: Path, catalog: Catalog):
    source = _write(tmp_path / "deck.pptx")
    plan = _build([source], catalog)

    assert len(plan.items) == 1
    item = plan.items[0]
    assert item.state == STATE_READY
    assert item.operation == "pptx_to_pdf"
    assert item.destination == tmp_path / "deck.pdf"


def test_single_file_with_out(tmp_path: Path, catalog: Catalog):
    source = _write(tmp_path / "deck.pptx")
    out = tmp_path / "out"
    plan = _build([source], catalog, out=out)

    assert plan.items[0].destination == out / "deck.pdf"


def test_folder_mirrors_relative_paths(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "a.pptx")
    _write(root / "q1" / "b.pptx")
    out = tmp_path / "out"

    plan = _build([root], catalog, out=out)
    destinations = {item.destination for item in plan.items}

    assert destinations == {out / "a.pdf", out / "q1" / "b.pdf"}
    assert all(item.state == STATE_READY for item in plan.items)


def test_folder_default_output_root(tmp_path: Path, catalog: Catalog, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "decks"
    _write(root / "a.pptx")

    plan = _build([root], catalog)

    assert plan.output_root == (tmp_path / "graphia-output").resolve()
    assert plan.items[0].destination == (tmp_path / "graphia-output" / "a.pdf").resolve()


def test_non_recursive_scans_only_the_top(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "a.pptx")
    _write(root / "sub" / "b.pptx")

    plan = _build([root], catalog, out=tmp_path / "out", recursive=False)

    assert [item.source.name for item in plan.items] == ["a.pptx"]


def test_hidden_and_ignored_directories(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "a.pptx")
    _write(root / ".secret.pptx")
    _write(root / "node_modules" / "dep.pptx")

    default = _build([root], catalog, out=tmp_path / "out")
    assert [item.source.name for item in default.items] == ["a.pptx"]

    hidden = _build([root], catalog, out=tmp_path / "out", include_hidden=True)
    assert {item.source.name for item in hidden.items} == {"a.pptx", ".secret.pptx"}


def test_output_directory_is_not_scanned(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "a.pptx")
    out = root / "converted"
    _write(out / "old.pptx")

    plan = _build([root], catalog, out=out)

    assert [item.source.name for item in plan.items] == ["a.pptx"]


def test_existing_output_is_skipped_unless_overwrite(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "a.pptx")
    _write(root / "a.pdf")
    out = tmp_path / "out"
    _write(out / "a.pdf")

    plan = _build([root], catalog, out=out)
    by_name = {item.source.name: item for item in plan.items}
    assert by_name["a.pptx"].state == STATE_SKIP
    assert "already exists" in (by_name["a.pptx"].reason or "")

    overwrite = _build([root], catalog, out=out, overwrite=True)
    by_name = {item.source.name: item for item in overwrite.items}
    assert by_name["a.pptx"].state == STATE_READY


def test_collision_marks_both_as_errors(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "a.pptx")
    _write(root / "a.docx")

    plan = _build([root], catalog, out=tmp_path / "out")

    assert len(plan.items) == 2
    assert all(item.state == STATE_ERROR for item in plan.items)
    assert all("Another source file" in (item.reason or "") for item in plan.items)


def test_empty_and_oversize_files_are_skipped(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "decks"
    _write(root / "empty.pptx", b"")
    _write(root / "big.pptx", b"0123456789")

    plan = _build([root], catalog, out=tmp_path / "out", max_upload_bytes=5)

    states = {item.source.name: item for item in plan.items}
    assert states["empty.pptx"].state == STATE_SKIP
    assert "empty" in (states["empty.pptx"].reason or "").lower()
    assert states["big.pptx"].state == STATE_SKIP
    assert "limit" in (states["big.pptx"].reason or "").lower()


def test_unsupported_and_already_target_files(tmp_path: Path, catalog: Catalog):
    root = tmp_path / "docs"
    _write(root / "old.ppt")
    _write(root / "already.pdf")

    plan = _build([root], catalog, out=tmp_path / "out")
    reasons = {item.source.name: item.reason for item in plan.items}

    assert "No pdf conversion" in (reasons["old.ppt"] or "")
    assert "Already PDF" in (reasons["already.pdf"] or "")


def test_multiple_roots_keep_root_names(tmp_path: Path, catalog: Catalog):
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first / "a.pptx")
    _write(second / "b.pptx")
    out = tmp_path / "out"

    plan = _build([first, second], catalog, out=out)
    destinations = {item.destination for item in plan.items}

    assert destinations == {out / "first" / "a.pdf", out / "second" / "b.pdf"}


def test_explicit_operation_rejects_wrong_extension(tmp_path: Path, catalog: Catalog):
    source = _write(tmp_path / "notes.txt")
    plan = _build([source], catalog, target=None, operation="pptx_to_pdf")

    assert plan.items[0].state == STATE_SKIP
    assert "PPTX to PDF accepts" in (plan.items[0].reason or "")
