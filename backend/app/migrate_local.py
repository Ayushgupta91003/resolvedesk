"""Copy local SQLite business records into ResolveDesk's isolated Docker database.

The source is retained. Refuses an occupied target or unfinished workflows because
cross-backend graph checkpoint conversion is intentionally not implicit.
"""
import argparse
import json
from pathlib import Path
from sqlalchemy import create_engine, select, func
from sqlalchemy.engine import make_url
from .models import Base, Run

def migrate(source_path, target_url):
    source_path = Path(source_path).resolve()
    if not source_path.is_file():
        raise ValueError("The source SQLite database does not exist.")
    url = make_url(target_url)
    if url.get_backend_name() != "postgresql" or url.host not in ("127.0.0.1", "localhost") or url.port != 55432 or url.database != "resolvedesk":
        raise ValueError("This helper only targets ResolveDesk's localhost:55432/resolvedesk database.")
    source = create_engine(f"sqlite:///{source_path.as_posix()}")
    target = create_engine(target_url)
    try:
        with source.connect() as conn:
            unfinished = conn.scalar(select(func.count()).select_from(Run).where(Run.status.not_in(["completed", "rejected"])))
            if unfinished:
                raise ValueError(f"Finish or reject active investigations and resolve {unfinished} unfinished/failed run(s) before migration. Source data is unchanged.")
        Base.metadata.create_all(target)
        counts = {}
        with source.connect() as src, target.begin() as dst:
            occupied = sum(dst.scalar(select(func.count()).select_from(table)) for table in Base.metadata.sorted_tables)
            if occupied:
                raise ValueError("The target already contains business records. Refusing to overwrite or merge data.")
            for table in Base.metadata.sorted_tables:
                rows = [dict(row._mapping) for row in src.execute(select(table))]
                if rows:
                    dst.execute(table.insert(), rows)
                counts[table.name] = len(rows)
        return counts
    finally:
        source.dispose()
        target.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target-url", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps({"migrated": migrate(args.source, args.target_url), "source_retained": True}, indent=2))
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
