from igdb.sync import sync_games
from amazon.sync import sync_prices
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

scheduler.add_job(sync_prices, 'interval', hours=2, next_run_time=datetime.now())
scheduler.add_job(sync_games, 'interval', days=1)

scheduler.start()