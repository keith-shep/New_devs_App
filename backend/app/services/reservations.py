from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RevenueUnavailableError(Exception):
    """Raised when revenue cannot be calculated (e.g. the database is unreachable)."""

async def calculate_monthly_revenue(property_id: str, month: int, year: int, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month.
    """

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)
        
    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date}")

    # SQL Simulation (This would be executed against the actual DB)
    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    # In production this query executes against a database session.
    # result = await db.fetch_val(query, property_id, tenant_id, start_date, end_date)
    # return result or Decimal('0')
    
    return Decimal('0') # Placeholder for now until DB connection is finalized

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        # Import database pool
        from app.core.database_pool import db_pool

        # Initialize shared pool if needed
        await db_pool.initialize()

        if db_pool.pool:
            async with db_pool.pool.acquire() as conn:
                query = """
                    SELECT
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations
                    WHERE property_id = $1 AND tenant_id = $2
                    GROUP BY property_id
                """

                row = await conn.fetchrow(query, property_id, tenant_id)

                if row:
                    total_revenue = Decimal(str(row["total_revenue"]))
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue),
                        "currency": "USD",
                        "count": row["reservation_count"]
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        # Never fall back to fake figures for financial data - surface the failure instead
        logger.error(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        raise RevenueUnavailableError("Revenue data temporarily unavailable") from e
