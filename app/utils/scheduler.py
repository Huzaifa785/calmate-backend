from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from appwrite.services.databases import Databases
from app.utils.appwrite_client import get_client
from app.config import settings

async def reset_daily_calories():
    try:
        client = get_client()
        database = Databases(client)
        
        users = database.list_documents(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089'
        )
        
        for user in users['documents']:
            database.update_document(
                database_id=settings.DATABASE_ID,
                collection_id='6758085b003d85763089',
                document_id=user['$id'],
                data={'calories_consumed_today': 0}
            )
            print(f"Reset calories for user: {user['$id']}")
    except Exception as e:
        print(f"Error resetting calories: {str(e)}")

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
    
    return scheduler