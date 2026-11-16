from __future__ import annotations

import argparse
from datetime import timedelta

from sqlalchemy import or_, select

from core.database import SessionLocal
from core.logging import configure_logging
from core.models.conversion_job import ConversionJob
from core.storage import get_storage
from core.utils import utcnow


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete expired jobs and abandoned uploads.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    configure_logging()
    storage = get_storage()
    now = utcnow()
    abandoned_before = now - timedelta(hours=1)

    db = SessionLocal()
    try:
        jobs = list(
            db.execute(
                select(ConversionJob).where(
                    or_(
                        ConversionJob.expires_at < now,
                        (
                            (ConversionJob.upload_completed_at.is_(None))
                            & (ConversionJob.created_at < abandoned_before)
                        ),
                    )
                )
            ).scalars()
        )

        for job in jobs:
            print(f"{'would delete' if args.dry_run else 'deleting'} {job.id} ({job.status.value})")
            if args.dry_run:
                continue
            for key in [job.input_key, job.output_key]:
                if not key:
                    continue
                try:
                    storage.delete(key)
                except Exception as exc:
                    print(f"  storage delete failed for {key}: {exc}")
            db.delete(job)

        if not args.dry_run:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
