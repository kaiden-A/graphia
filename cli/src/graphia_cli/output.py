from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from graphia_cli.api import Operation
from graphia_cli.planner import (
    STATE_ERROR,
    STATE_READY,
    STATE_SKIP,
    Plan,
    PlanItem,
)

if TYPE_CHECKING:
    from graphia_cli.runner import JobResult


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def human_size(size: int | None) -> str:
    if not size:
        return ""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return ""


class Reporter:
    def __init__(self, *, quiet: bool = False, json_mode: bool = False) -> None:
        self.console = Console(highlight=False, emoji=False)
        self.error_console = Console(
            highlight=False,
            emoji=False,
            stderr=True,
        )
        self.quiet = quiet
        self.json_mode = json_mode

    def info(self, message: str) -> None:
        if not self.json_mode and not self.quiet:
            self.console.print(message)

    def error(self, message: str) -> None:
        self.error_console.print(f"[red]{escape(message)}[/red]")

    def plan(self, plan: Plan, *, title: str = "Plan") -> None:
        if self.json_mode:
            return
        table = Table(title=title, box=None, show_lines=False, pad_edge=False)
        table.add_column("Source", overflow="fold")
        table.add_column("Operation")
        table.add_column("Output", overflow="fold")
        table.add_column("State")

        for item in plan.items:
            state = {
                STATE_READY: "[green]ready[/green]",
                STATE_SKIP: "[yellow]skip[/yellow]",
                STATE_ERROR: "[red]error[/red]",
            }.get(item.state, item.state)
            state_text = state
            if item.reason:
                state_text = f"{state_text} — {escape(item.reason)}"
            table.add_row(
                escape(display_path(item.source)),
                escape(item.operation_label or item.operation or "—"),
                escape(display_path(item.destination)),
                state_text,
            )
        self.console.print(table)
        self.console.print(
            f"{len(plan.ready)} ready, {len(plan.skipped)} skipped, "
            f"{len(plan.errors)} error(s)"
        )

    def operations(self, operations: list[Operation]) -> None:
        table = Table(box=None, pad_edge=False)
        table.add_column("Id", style="bold", no_wrap=True)
        table.add_column("Inputs")
        table.add_column("Output")
        table.add_column("Group")

        for operation in operations:
            inputs = ", ".join(f".{value}" for value in operation.input_extensions)
            output = f".{operation.output_extension}"
            if operation.output_suffix:
                output = f"*{operation.output_suffix}{output}"
            table.add_row(
                escape(operation.id),
                escape(inputs),
                escape(output),
                escape(operation.group),
            )
        self.console.print(table)

    def item_done(self, result: JobResult) -> None:
        if self.quiet or self.json_mode:
            return
        size = human_size(result.output_size)
        extra = f" ({size}, {result.duration:.1f}s)" if size else f" ({result.duration:.1f}s)"
        self.console.print(
            f"[green]✓[/green] {escape(display_path(result.item.source))} → "
            f"{escape(display_path(result.output or result.item.destination))}{extra}"
        )

    def item_skipped(self, item: PlanItem) -> None:
        if self.quiet or self.json_mode:
            return
        self.console.print(
            f"[yellow]⤼[/yellow] {escape(display_path(item.source))} — "
            f"{escape(item.reason or 'skipped')}"
        )

    def item_failed(self, result: JobResult) -> None:
        if self.json_mode:
            return
        self.error_console.print(
            f"[red]✗[/red] {escape(display_path(result.item.source))} — "
            f"{escape(result.error or 'conversion failed')}"
        )

    def summary(self, plan: Plan, results: list[JobResult], elapsed: float) -> None:
        if self.json_mode:
            return
        converted = sum(1 for result in results if result.state == "converted")
        failed = sum(1 for result in results if result.state == "failed")
        ran = {str(result.item.source) for result in results}
        cancelled = sum(1 for result in results if result.state == "cancelled")
        cancelled += sum(1 for item in plan.ready if str(item.source) not in ran)
        skipped = len(plan.skipped)

        minutes, seconds = divmod(int(elapsed), 60)
        duration = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
        self.console.print(
            f"\n[bold]{converted} converted[/bold], {skipped} skipped, {failed} failed"
            + (f", {cancelled} not run" if cancelled else "")
            + (f", {len(plan.errors)} plan error(s)" if plan.errors else "")
            + f" in {duration}"
        )
        if plan.output_root is not None and converted:
            self.console.print(f"Output: {display_path(plan.output_root)}")
        if cancelled:
            self.console.print(
                "The batch stopped early. Completed outputs are skipped on the next run."
            )
        if failed:
            self.console.print("Failed files:")
            for result in results:
                if result.state == "failed":
                    self.console.print(
                        f"  {escape(display_path(result.item.source))} — "
                        f"{escape(result.error or 'conversion failed')}"
                    )
