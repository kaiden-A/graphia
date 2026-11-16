from __future__ import annotations

import argparse
from datetime import timedelta

from sqlalchemy import or_, select, update

from app.services import processor_client
from core.database import SessionLocal
from core.logging import configure_logging
from core.models.conversion_job import ConversionJob
from core.models.enums import JobStatus
from core.utils import utcnow


def main() -> None:
    parser = argparse.ArgumentParser(description="Requeue stale processor jobs.")
    parser.add_argument("--minutes", type=int, default=15)
    parser.add_argument("--no-trigger", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    configure_logging()
    cutoff = utcnow() - timedelta(minutes=args.minutes)
    db = SessionLocal()
    try:
        stale = list(
            db.execute(
                select(ConversionJob).where(
                    or_(
                        (ConversionJob.status == JobStatus.PROCESSING)
                        & (ConversionJob.started_at < cutoff),
                        (ConversionJob.status == JobStatus.PENDING)
                        & (ConversionJob.upload_completed_at.is_not(None))
                        & (ConversionJob.created_at < cutoff),
                    )
                )
            ).scalars()
        )

        for job in stale:
            print(f"requeue {job.id} ({job.status.value})")
            if args.dry_run:
                continue
            db.execute(
                update(ConversionJob)
                .where(ConversionJob.id == job.id)
                .values(
                    status=JobStatus.PENDING,
                    started_at=None,
                    error_message=None,
                )
            )
            db.commit()
            if not args.no_trigger:
                accepted, message = processor_client.trigger(job.id)
                if not accepted:
                    print(f"  trigger failed: {message}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
