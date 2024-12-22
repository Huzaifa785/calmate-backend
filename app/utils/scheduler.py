from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from appwrite.services.databases import Databases
from appwrite.query import Query
from app.utils.appwrite_client import get_client
from app.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_daily_calories():
    try:
        client = get_client()
        database = Databases(client)
        
        # Get all users - paginate through results
        offset = 0
        limit = 100  # Process in batches
        
        while True:
            users = database.list_documents(
                database_id=settings.DATABASE_ID,
                collection_id='6758085b003d85763089',
                queries=[
                    Query.limit(limit),
                    Query.offset(offset)
                ]
            )
            
            if not users['documents']:
                break
                
            for user in users['documents']:
                try:
                    database.update_document(
                        database_id=settings.DATABASE_ID,
                        collection_id='6758085b003d85763089',
                        document_id=user['$id'],
                        data={'calories_consumed_today': 0}
                    )
                    logger.info(f"Reset calories for user: {user['$id']}")
                except Exception as e:
                    logger.error(f"Failed to reset calories for user {user['$id']}: {str(e)}")
            
            offset += limit
            
        logger.info("Completed daily calorie reset for all users")
    except Exception as e:
        logger.error(f"Error in reset_daily_calories: {str(e)}")
        raise

def init_scheduler():
    scheduler = AsyncIOScheduler()
    
    # Schedule reset_daily_calories to run at midnight every day
    scheduler.add_job(
        reset_daily_calories,
        CronTrigger(hour=0, minute=0),  # Run at midnight
        id='reset_daily_calories',
        name='Reset daily calorie counts',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    return scheduler