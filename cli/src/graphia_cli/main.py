from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import typer

from graphia_cli import __version__, api, auth
from graphia_cli.client import GraphiaClient
from graphia_cli.config import Runtime, resolve_runtime, save_server
from graphia_cli.errors import ApiError, AuthError, GraphiaError
from graphia_cli.operations import Catalog
from graphia_cli.output import Reporter, display_path
from graphia_cli.planner import STATE_ERROR, STATE_SKIP, Plan, build_plan
from graphia_cli.runner import BatchOutcome, run_plan

app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help="Convert documents in batches from the terminal, powered by Graphia.",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"graphia {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the CLI version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Graphia CLI."""


def _fail(message: str) -> None:
    typer.secho(message, err=True, fg=typer.colors.RED)
    raise typer.Exit(2)


def _runtime(server: str | None) -> Runtime:
    return resolve_runtime(server)


def _stored_token(runtime: Runtime) -> auth.StoredToken:
    stored = auth.load_token(runtime)
    if stored is None:
        raise AuthError(
            f"Not signed in to {runtime.server}. Run `graphia login` first."
        )
    return stored


def _server_config(client: GraphiaClient) -> api.ConfigInfo:
    try:
        config = api.get_config(client)
    except ApiError as exc:
        if exc.status == 404:
            raise AuthError("This server does not support the Graphia CLI yet.") from exc
        raise
    if config.auth_mode != "browser-approval":
        raise AuthError("This server does not support the Graphia CLI yet.")
    return config


@app.command()
def login(
    server: str | None = typer.Option(
        None, "--server", "-s", help="Graphia server URL (API or site)."
    ),
    name: str | None = typer.Option(None, "--name", help="Device name shown in the browser."),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Print the approval URL instead of opening a browser.",
    ),
    allow_local_approval: bool = typer.Option(
        False,
        "--allow-local-approval",
        help="Allow the localhost approval page a remote API may report.",
    ),
) -> None:
    """Sign in by approving this terminal in a browser."""
    runtime = _runtime(server)
    try:
        stored, user = auth.login(
            runtime,
            name=name,
            no_browser=no_browser,
            allow_local_approval=allow_local_approval,
        )
        if user.is_guest:
            raise AuthError("The CLI requires a member account.")
    except GraphiaError as exc:
        _fail(str(exc))
        return

    try:
        save_server(runtime.config_path, runtime.server)
    except OSError:
        typer.secho(
            f"Signed in, but could not save {runtime.config_path}. "
            "Pass --server next time.",
            err=True,
            fg=typer.colors.YELLOW,
        )

    typer.echo(f"Signed in as {user.email}.")
    typer.echo(f"Server: {runtime.server}")
    typer.echo(f"Token:  {stored.source}")


@app.command()
def logout(
    server: str | None = typer.Option(
        None, "--server", "-s", help="Graphia server URL (API or site)."
    ),
) -> None:
    """Revoke the stored CLI session."""
    runtime = _runtime(server)
    try:
        removed = auth.logout(runtime)
    except GraphiaError as exc:
        _fail(str(exc))
        return
    if removed:
        typer.echo(f"Signed out of {runtime.server}.")
    else:
        typer.echo(f"No stored session for {runtime.server}.")


@app.command()
def whoami(
    server: str | None = typer.Option(
        None, "--server", "-s", help="Graphia server URL (API or site)."
    ),
) -> None:
    """Show the signed-in account."""
    runtime = _runtime(server)
    try:
        stored = _stored_token(runtime)
        with GraphiaClient(runtime.server, token=stored.token) as client:
            user = api.get_me(client)
    except GraphiaError as exc:
        _fail(str(exc))
        return

    if user.is_guest:
        _fail("This session belongs to a guest. The CLI requires a member account.")
        return

    typer.echo(user.email)
    if user.name:
        typer.echo(user.name)
    typer.echo(f"Server: {runtime.server}")
    typer.echo(f"Token:  {stored.source}")


@app.command()
def doctor(
    server: str | None = typer.Option(
        None, "--server", "-s", help="Graphia server URL (API or site)."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show HTTP requests."),
) -> None:
    """Check the server, session, and supported operations."""
    runtime = _runtime(server)
    stored = auth.load_token(runtime)
    ok = True

    typer.echo(f"Graphia CLI {__version__}")
    typer.echo(f"Server: {runtime.server} ({runtime.server_source})")
    typer.echo(f"Config: {runtime.config_path}")
    typer.echo(f"Token:  {stored.source if stored else 'not signed in'}")

    try:
        with GraphiaClient(
            runtime.server,
            token=stored.token if stored else None,
            verbose=verbose,
        ) as client:
            config = _server_config(client)
            typer.echo(f"API:    {config.app_name} {config.version}")
            typer.echo(f"Web:    {config.web_url}")
            if auth.is_localhost(config.web_url) and not auth.is_localhost(runtime.server):
                typer.secho(
                    "        Approval page points at localhost; "
                    "set PUBLIC_BASE_URL on the API.",
                    err=True,
                    fg=typer.colors.YELLOW,
                )
            typer.echo(
                f"Limits: {config.max_upload_mb} MB, "
                f"{config.max_active_jobs} active jobs, "
                f"{config.uploads_per_hour} uploads/hour"
            )
            operations = api.get_operations(client)
            typer.echo(f"Ops:    {len(operations)}")

            if stored is None:
                typer.echo("Auth:   not signed in (run `graphia login`)")
            else:
                try:
                    user = api.get_me(client)
                except GraphiaError as exc:
                    typer.secho(f"Auth:   {exc}", err=True, fg=typer.colors.RED)
                    ok = False
                else:
                    kind = "guest" if user.is_guest else "member"
                    typer.echo(f"Auth:   {user.email} ({kind})")
                    if user.is_guest:
                        ok = False
    except GraphiaError as exc:
        typer.secho(f"API:    {exc}", err=True, fg=typer.colors.RED)
        ok = False

    raise typer.Exit(0 if ok else 1)


@app.command()
def operations(
    server: str | None = typer.Option(
        None, "--server", "-s", help="Graphia server URL (API or site)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON."),
) -> None:
    """List the conversions this server supports."""
    runtime = _runtime(server)
    try:
        with GraphiaClient(runtime.server) as client:
            items = api.get_operations(client)
    except GraphiaError as exc:
        _fail(str(exc))
        return

    if json_output:
        typer.echo(json.dumps([asdict(item) for item in items], indent=2))
        return
    Reporter().operations(items)


def _plan_report(plan: Plan, runtime: Runtime, *, dry_run: bool) -> dict[str, Any]:
    files = []
    for item in plan.items:
        files.append(
            {
                "source": str(item.source),
                "operation": item.operation,
                "output": str(item.destination),
                "state": item.state,
                "reason": item.reason,
            }
        )
    return {
        "server": runtime.server,
        "output": str(plan.output_root) if plan.output_root else None,
        "dryRun": dry_run,
        "ready": len(plan.ready),
        "skipped": len(plan.skipped),
        "errors": len(plan.errors),
        "files": files,
    }


def _outcome_report(
    plan: Plan,
    runtime: Runtime,
    outcome: BatchOutcome,
    *,
    elapsed: float,
) -> dict[str, Any]:
    by_source = {str(result.item.source): result for result in outcome.results}
    files = []
    converted = failed = cancelled = 0

    for item in plan.items:
        result = by_source.get(str(item.source))
        if result is not None:
            state = result.state
            job_id = result.job_id
            output = str(result.output) if result.output else None
            error = result.error
            if state == "converted":
                converted += 1
            elif state == "failed":
                failed += 1
            elif state == "cancelled":
                cancelled += 1
        elif item.state == STATE_SKIP:
            state, job_id, output, error = "skipped", None, None, item.reason
        elif item.state == STATE_ERROR:
            state, job_id, output, error = "error", None, None, item.reason
        else:
            state, job_id, output, error = "cancelled", None, None, "Not run."
            cancelled += 1

        files.append(
            {
                "source": str(item.source),
                "operation": item.operation,
                "output": output,
                "state": state,
                "jobId": job_id,
                "error": error,
            }
        )

    return {
        "server": runtime.server,
        "output": str(plan.output_root) if plan.output_root else None,
        "converted": converted,
        "skipped": len(plan.skipped),
        "failed": failed,
        "cancelled": cancelled,
        "errors": len(plan.errors),
        "seconds": round(elapsed, 1),
        "fatal": str(outcome.fatal) if outcome.fatal else None,
        "files": files,
    }


@app.command()
def convert(
    paths: list[Path] = typer.Argument(..., help="Files or folders to convert."),
    server: str | None = typer.Option(
        None, "--server", "-s", help="Graphia server URL (API or site)."
    ),
    to: str | None = typer.Option(
        None,
        "--to",
        "-t",
        help="Target format: pdf, md, or txt.",
    ),
    operation: str | None = typer.Option(
        None,
        "--operation",
        "-o",
        help="Explicit operation id (for example compress_pdf).",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output folder. Defaults beside a single file or to ./graphia-output.",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        help="Scan folders recursively.",
    ),
    include_hidden: bool = typer.Option(
        False,
        "--include-hidden",
        help="Include dotfiles and hidden folders.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Replace existing output files.",
    ),
    jobs: int = typer.Option(
        3,
        "--jobs",
        "-j",
        min=1,
        max=8,
        help="Files to keep in flight (server limit applies).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show the plan without uploading anything.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print a JSON report."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only show errors and the summary."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show HTTP requests."),
) -> None:
    """Convert files or scan folders for a target format."""
    runtime = _runtime(server)
    reporter = Reporter(quiet=quiet, json_mode=json_output)
    started = time.monotonic()

    try:
        stored = _stored_token(runtime)
        with GraphiaClient(
            runtime.server,
            token=stored.token,
            verbose=verbose,
        ) as client:
            config = _server_config(client)
            catalog = Catalog.from_operations(api.get_operations(client))
            user = api.get_me(client)
            if user.is_guest:
                raise AuthError("The CLI requires a member account.")

            plan = build_plan(
                list(paths),
                target=to,
                operation=operation,
                out=out,
                recursive=recursive,
                include_hidden=include_hidden,
                overwrite=overwrite,
                max_upload_bytes=config.max_upload_mb * 1024 * 1024,
                catalog=catalog,
            )

            if dry_run:
                if json_output:
                    typer.echo(json.dumps(_plan_report(plan, runtime, dry_run=True), indent=2))
                else:
                    reporter.plan(plan, title="Dry run")
                raise typer.Exit(1 if plan.has_errors else 0)

            if not plan.items:
                reporter.info("No files matched.")
            for item in plan.skipped:
                reporter.item_skipped(item)
            for item in plan.errors:
                reporter.error(f"{display_path(item.source)} — {item.reason}")

            if not plan.ready:
                reporter.summary(plan, [], time.monotonic() - started)
                if json_output:
                    outcome = BatchOutcome()
                    typer.echo(
                        json.dumps(
                            _outcome_report(
                                plan,
                                runtime,
                                outcome,
                                elapsed=time.monotonic() - started,
                            ),
                            indent=2,
                        )
                    )
                raise typer.Exit(1 if plan.has_errors else 0)

            workers = min(jobs, config.max_active_jobs)
            if workers < jobs:
                reporter.info(
                    f"Using {workers} parallel job(s); the server allows "
                    f"{config.max_active_jobs}."
                )
            reporter.info(
                f"Converting {len(plan.ready)} file(s) with {workers} in flight…"
            )

            try:
                outcome = run_plan(
                    plan,
                    client,
                    jobs=workers,
                    reporter=reporter,
                )
            except KeyboardInterrupt:
                typer.secho("Stopped.", err=True, fg=typer.colors.YELLOW)
                raise typer.Exit(130) from None

            elapsed = time.monotonic() - started
            reporter.summary(plan, outcome.results, elapsed)
            if json_output:
                typer.echo(
                    json.dumps(
                        _outcome_report(plan, runtime, outcome, elapsed=elapsed),
                        indent=2,
                    )
                )

            if outcome.fatal is not None:
                raise outcome.fatal
    except GraphiaError as exc:
        _fail(str(exc))
        return

    failed = any(result.state == "failed" for result in outcome.results)
    raise typer.Exit(1 if (failed or plan.has_errors) else 0)


if __name__ == "__main__":
    app()
