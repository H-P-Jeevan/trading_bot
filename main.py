from application_utils_v2 import *
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta
import logging

# Setup basic config
logging.basicConfig(
    filename='app.log',         # Log to file
    filemode='a',               # Append mode
    level=logging.INFO,         # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Login
client = login(file_path="./login.csv")  

tickers = ['ASHOKLEY', 'TATASTEEL', 'LT', 'SAIL', 'CDSL',
           # 'COALINDIA', 'BAJAJFINSV', 'DSSL', 'PPLPHARMA', 'WIPRO', ABB', 'RECLTD', 'IRFC', 'EASEMYTRIP', 'CIPLA', 
           # 'BHEL', 'PRESTIGE', 'NMDC', 'CUMMINSIND', 'ITC', 'POWERGRID', 'JINDALSTEL', 'DLF', 'MOTHERSON',
           # 'RALLIS', 'IRCTC', 'GRSE', 'INDUSTOWER', 'BEL', 'HINDALCO', 'APLLTD', 'MANAPPURAM', 'TRENT', 'BEML',
           # 'IDEA', 'VEDL', 'ASIANPAINT', 'JSWSTEEL', 'RVNL', 'HAL', 'ZEEL', 'BIOCON', 'COCHINSHIP', 'NHPC',
           # 'MANGLMCEM', 'SYMPHONY', 'HEROMOTOCO', 'EIHOTEL', 'MSUMI', 'MANAPPURAM.NS', 'TCS.NS', 'WELCORP.NS',
           # 'KOTAKBANK.NS', 'INDUSTOWER.NS', 'NMDC.NS', 'YESBANK.NS', 'ICICIBANK.NS', 'UNIONBANK.NS', 'HDFCBANK.NS', 'PNB.NS', 'AXISBANK.NS', "BEL.NS"
           ]

# Get the instrument tokens
instrument_tokens, tickers = get_instrument_tokens(client, tickers)
ticker_dict = dict(zip(tickers, instrument_tokens))
instrument_dict = dict(zip(instrument_tokens, tickers))

# Empty the files and get historical data for all the tickers
buff_no = True
empty_file("all_data_True.csv" )
empty_file("all_data_False.csv" )
get_historical_data(instrument_tokens, tickers)

# Callback functions
def on_message(message):
    """
    Callback function triggered when a new message comes.
    """
    global buff_no
    message_data = message["data"]
    
    # Check if data available for each tk
    data = [[item["tk"], item["ltp"]] for item in message_data if item.get('tk') is not None and item.get('ltp') is not None]
    # Write all the data colleted to file
    with open(f"all_data_{buff_no}.csv", mode='a', newline='') as file:
        file_writer = writer(file).writerows(data)
        
def on_error(message):
    global client, instrument_tokens
    """
    Callback function triggered when an error occurs.
    """
    print("[On Error]", message)
    # if message == "Connection to remote host was lost.":
    create_main_thread(client, instrument_tokens)

def on_close(message):
    """
    Callback function triggered when the connection is closed.
    """
    print("[On Close]", message)

def on_open(message):
    """
    Callback function triggered when the connection is Open.
    """
    print("[On Open]", message)
        
client.on_message = on_message
client.on_error = on_error  
client.on_close = on_close
client.on_open = on_open

# 5 minite task
def task_5():
    global start_time, buff_no
    print(f"[INFO] Strategy execution started at {datetime.now().strftime('%H:%M')}")
        
    # Update buffer
    prev_buff_no = buff_no
    buff_no = not buff_no
    
    get_ltp_by_token(f"all_data_{prev_buff_no}.csv")
    empty_file(f"all_data_{prev_buff_no}.csv")
    update_historical_data(instrument_tokens)
    buys, sells = supertrend_strategy(instrument_tokens)
    logging.info(f"Buys: {buys} Sells: {sells}")
    print(f"Buys: {buys} Sells: {sells}")
    order_stocks(client, buys, sells, instrument_dict)

    # Calculate next execution time 
    start_time += timedelta(minutes=5)

    # Schedule next execution if within working hours
    if start_time <= end_time:
        scheduler.add_job(task_5, 'date', run_date=start_time)
        print(f"[INFO] Next strategy execution scheduled at {start_time.strftime('%H:%M')}")

# Define start time and end time
start_time = datetime.now().replace(hour=9, minute=20, second=0, microsecond=0)
end_time = datetime.now().replace(hour=15, minute=29, second=0, microsecond=0)

# Schedule the first task at 9:20 AM
scheduler = BackgroundScheduler()
scheduler.add_job(task_5, 'date', run_date=start_time)

# Start the scheduler
scheduler.start()
print(f"[INFO] Next strategy execution scheduled at {start_time.strftime('%H:%M')}")

# Wait till 9:15 to get data
print("[INFO] Waiting for 9:15....")
while True:
   if dt.datetime.now().strftime('%H:%M') == "09:15":
       break
       time.sleep(1)
 
# Start the main thread to get data
create_main_thread(client, instrument_tokens)

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
