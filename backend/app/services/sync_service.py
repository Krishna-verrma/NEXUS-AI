import asyncio
import logging
from datetime import datetime
from app.database.repository import Repository
from app.integrations.calendar.unified_calendar import UnifiedCalendarEngine
from app.services.oauth.google_oauth import GoogleOAuthService
from app.services.oauth.microsoft_oauth import MicrosoftOAuthService

logger = logging.getLogger("nexus.sync_service")

class SyncService:
    _background_task: asyncio.Task = None
    _is_running: bool = False

    @classmethod
    async def run_initial_startup_sync(cls):
        """
        Executed when Nexus AI starts:
        1. Check connected accounts.
        2. Refresh OAuth tokens if necessary.
        3. Synchronize today's calendar.
        4. Synchronize upcoming calendar events.
        5. Synchronize relevant email changes.
        6. Detect meeting changes.
        7. Update dashboard cache.
        """
        logger.info("Running Nexus startup synchronization...")
        try:
            # 1 & 2. Check accounts and refresh tokens
            g_token = await GoogleOAuthService.get_valid_access_token()
            ms_token = await MicrosoftOAuthService.get_valid_access_token()
            
            logger.info(f"Account check: Google={'Valid' if g_token else 'Not active'}, Microsoft={'Valid' if ms_token else 'Not active'}")

            # 3, 4, 5, 6, 7. Synchronize calendars and detect changes
            res = await UnifiedCalendarEngine.sync_all_calendars()
            logger.info(f"Startup sync completed: {res.get('total_synced', 0)} events synced across accounts.")
        except Exception as e:
            logger.warning(f"Startup sync encountered an error: {e}")

    @classmethod
    async def start_background_sync(cls, interval_seconds: int = 300):
        """Periodic background incremental synchronization loop."""
        cls._is_running = True
        logger.info(f"Starting background calendar sync loop (every {interval_seconds}s)...")
        while cls._is_running:
            try:
                await asyncio.sleep(interval_seconds)
                if not cls._is_running:
                    break
                logger.debug("Executing scheduled incremental calendar sync...")
                await UnifiedCalendarEngine.sync_all_calendars()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background sync loop error: {e}")

    @classmethod
    def stop_background_sync(cls):
        cls._is_running = False
        if cls._background_task and not cls._background_task.done():
            cls._background_task.cancel()
