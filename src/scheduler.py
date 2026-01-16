from apscheduler.schedulers.background import BackgroundScheduler

from src.sync import sync_products

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(sync_products, "interval", minutes=300)
    scheduler.start()
