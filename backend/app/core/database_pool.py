import asyncpg
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        """Initialize database connection pool"""
        if self.pool:
            return
        try:
            # Create asyncpg connection pool against the Postgres in DATABASE_URL
            logger.info(f"Connecting database pool to {settings.database_url.rsplit('@', 1)[-1]}")
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=1,
                max_size=20,  # Max connections to maintain
            )

            # Run a test query so we know the connection actually works
            async with self.pool.acquire() as conn:
                db_name, reservation_count = await conn.fetchrow(
                    "SELECT current_database(), (SELECT COUNT(*) FROM reservations)"
                )
                logger.info(f"✅ Connected to Postgres database '{db_name}' ({reservation_count} reservations)")

            logger.info("✅ Database connection pool initialized")

        except Exception as e:
            logger.error(f"❌ Database pool initialization failed: {e}")
            self.pool = None

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()

# Global database pool instance
db_pool = DatabasePool()
