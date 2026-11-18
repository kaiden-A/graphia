from __future__ import annotations

import threading
import time
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from graphia_cli import api
from graphia_cli.client import GraphiaClient
from graphia_cli.errors import (
    ApiError,
    AuthError,
    BatchCancelled,
    GraphiaError,
    RateLimitError,
)
from graphia_cli.output import Reporter
from graphia_cli.planner import Plan, PlanItem

POLL_START_SECONDS = 1.0
POLL_MAX_SECONDS = 3.0
MAX_WAIT_SECONDS = 15 * 60


@dataclass
class JobResult:
    item: PlanItem
    state: str
    job_id: str | None = None
    output: Path | None = None
    output_size: int | None = None
    error: str | None = None
    duration: float = 0.0


@dataclass
class BatchOutcome:
    results: list[JobResult] = field(default_factory=list)
    fatal: Exception | None = None


@dataclass
class _BatchState:
    stop: threading.Event = field(default_factory=threading.Event)
    fatal: Exception | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def fail(self, error: Exception) -> None:
        with self.lock:
            if self.fatal is None:
                self.fatal = error
        self.stop.set()


def _is_fatal(error: ApiError) -> bool:
    return error.status in {401, 403}


def _convert_one(
    item: PlanItem,
    client: GraphiaClient,
    *,
    stop: threading.Event,
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> JobResult:
    started = time.monotonic()
    job, ticket = api.create_conversion(
        client,
        operation=item.operation,
        filename=item.source.name,
        file_size=item.size,
    )

    if stop.is_set():
        try:
            api.delete_conversion(client, job.id)
        except Exception:
            pass
        raise BatchCancelled()

    try:
        client.upload_file(ticket.url, ticket.headers, item.source)
    except Exception:
        # The job is still PENDING and would occupy an active slot for 30
        # minutes. Delete it best-effort before surfacing the error.
        try:
            api.delete_conversion(client, job.id)
        except Exception:
            pass
        raise

    if stop.is_set():
        raise BatchCancelled()

    current = api.complete_upload(client, job.id)
    if current.status == "FAILED":
        return JobResult(
            item=item,
            state="failed",
            job_id=job.id,
            error=current.error_message or "The conversion failed.",
            duration=time.monotonic() - started,
        )

    deadline = time.monotonic() + max_wait_seconds
    delay = POLL_START_SECONDS
    while time.monotonic() < deadline:
        if stop.is_set():
            raise BatchCancelled()
        current = api.get_conversion(client, job.id)
        if current.status == "COMPLETED":
            break
        if current.status == "FAILED":
            return JobResult(
                item=item,
                state="failed",
                job_id=job.id,
                error=current.error_message or "The conversion failed.",
                duration=time.monotonic() - started,
            )
        if stop.wait(delay):
            raise BatchCancelled()
        delay = min(delay + 0.5, POLL_MAX_SECONDS)
    else:
        return JobResult(
            item=item,
            state="failed",
            job_id=job.id,
            error="Timed out waiting for the conversion.",
            duration=time.monotonic() - started,
        )

    url = api.get_download(client, job.id)
    output = item.destination
    client.download_file(url, output)
    try:
        output_size = output.stat().st_size
    except OSError:
        output_size = None

    return JobResult(
        item=item,
        state="converted",
        job_id=job.id,
        output=output,
        output_size=output_size,
        duration=time.monotonic() - started,
    )


def _run_one(
    item: PlanItem,
    client: GraphiaClient,
    state: _BatchState,
    *,
    max_wait_seconds: int,
) -> JobResult:
    if state.stop.is_set():
        return JobResult(item=item, state="cancelled", error="Stopped before this file ran.")

    try:
        return _convert_one(
            item,
            client,
            stop=state.stop,
            max_wait_seconds=max_wait_seconds,
        )
    except BatchCancelled:
        return JobResult(item=item, state="cancelled", error="Stopped before this file finished.")
    except AuthError as exc:
        state.fail(exc)
        return JobResult(item=item, state="cancelled", error="Stopped.")
    except ApiError as exc:
        if _is_fatal(exc):
            state.fail(AuthError(str(exc)))
            return JobResult(item=item, state="cancelled", error="Stopped.")
        if exc.status == 429:
            state.fail(RateLimitError(str(exc)))
            return JobResult(item=item, state="cancelled", error="Stopped.")
        return JobResult(item=item, state="failed", error=str(exc))
    except GraphiaError as exc:
        return JobResult(item=item, state="failed", error=str(exc))
    except Exception as exc:  # noqa: BLE001 - one bad file must not kill the batch
        return JobResult(item=item, state="failed", error=f"Unexpected error: {exc}")


def run_plan(
    plan: Plan,
    client: GraphiaClient,
    *,
    jobs: int,
    reporter: Reporter,
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> BatchOutcome:
    state = _BatchState()
    outcome = BatchOutcome()
    if not plan.ready:
        return outcome

    workers = max(1, min(jobs, len(plan.ready)))
    executor = ThreadPoolExecutor(max_workers=workers)
    futures = {
        executor.submit(
            _run_one,
            item,
            client,
            state,
            max_wait_seconds=max_wait_seconds,
        ): item
        for item in plan.ready
    }

    try:
        for future in as_completed(futures):
            if future.cancelled():
                continue
            try:
                result = future.result()
            except CancelledError:
                continue
            outcome.results.append(result)
            if result.state == "converted":
                reporter.item_done(result)
            elif result.state == "failed":
                reporter.item_failed(result)

            if state.stop.is_set():
                for pending in futures:
                    pending.cancel()
    except KeyboardInterrupt:
        state.stop.set()
        for pending in futures:
            pending.cancel()
        raise
    finally:
        executor.shutdown(wait=True, cancel_futures=True)

    outcome.results.sort(key=lambda result: str(result.item.source).casefold())
    outcome.fatal = state.fatal
    return outcome
