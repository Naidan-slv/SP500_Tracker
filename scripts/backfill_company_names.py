from pathlib import Path
import sys

from sqlalchemy import func, or_, select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.routes.stocks import _fetch_company_profile
from app.database.connection import SessionLocal
from app.database.models import Stock


def needs_backfill_filter():
    trimmed_name = func.trim(func.coalesce(Stock.company_name, ""))
    return or_(trimmed_name == "", func.upper(trimmed_name) == func.upper(Stock.ticker))


async def main() -> None:
    with SessionLocal() as db:
        tickers = db.execute(
            select(Stock.ticker).where(needs_backfill_filter()).order_by(Stock.ticker.asc())
        ).scalars().all()

    if not tickers:
        print("No company-name backfill needed.")
        return

    print(f"Resolving company names for {len(tickers)} tickers...")
    updated = 0

    with SessionLocal() as db:
        for idx, ticker in enumerate(tickers, start=1):
            company_name, logo_url = await _fetch_company_profile(ticker)
            if not company_name and not logo_url:
                continue

            stock = db.get(Stock, ticker)
            if not stock:
                continue

            changed = False
            if company_name and (not stock.company_name or stock.company_name.strip().upper() == ticker.upper()):
                stock.company_name = company_name
                changed = True
            if logo_url and not stock.logo_url:
                stock.logo_url = logo_url
                changed = True

            if changed:
                db.add(stock)
                updated += 1

            if idx % 10 == 0:
                print(f"Processed {idx}/{len(tickers)}...")

        db.commit()

    print(f"Backfill complete. Updated {updated} stock rows.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
