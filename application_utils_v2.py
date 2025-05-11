# Import required libraries
from neo_api_client import NeoAPI
import pandas as pd
import datetime as dt
import yfinance as yf
import pandas_ta as ta
import requests
import os
from csv import writer
import time

interval = "5m" # historical data
no_of_days = 6
no_of_candles = 50

def login(file_path=None, data=None):
    """
    Logs in to the NeoAPI using either a CSV file or a provided dictionary containing login credentials.
    """
    # Read the CSV file containing login credentials
    login_data = pd.read_csv(file_path, index_col=False)
    login_data = login_data.to_dict("records")[0]
    print("[INFO] Login.csv file read completed")

    # Initialize the NeoAPI client with provided keys and environment
    client = NeoAPI(
        consumer_key=login_data["consumer_key"],
        consumer_secret=login_data["consumer_secret"],
        environment="prod"
    )

    # Perform the initial login using mobile number and password
    client.login(
        mobilenumber="+91" + str(login_data["mobilenumber"]), password=login_data["password"]
    )

    print("[INFO] Login Sucess!")

    client.session_2fa(OTP=login_data["mpin"])
    print("[INFO] Authetication Sucess!")

    return client

def empty_file(filename):
    """
    Empties the content of the specified file.
    """
    f = open(filename, "w+")
    f.close()

# def on_message(message):
    # """
    # Callback function triggered upon receiving messages.
    # Writes the received message data to a CSV file, using a buffer file based on current time.
    # """
    # global buff_no
    # try:
        # # print("[On message]", message)
        # if message["type"] == "stock_feed":
            # # # Convert the message to a DataFrame and append it to a CSV file named according to the buffer slot.
            # with open(f"all_data_{buff_no}.csv", mode='a', newline='') as file:
                # file_writer = writer(file)
                # file_writer.writerows([[entry["tk"], entry["ltp"]] for entry in message['data']])

    # except Exception as e:
        # print(f"[ERROR] Failed to process message: {e}")
     
# def on_message(message):
    # """
    # Callback function triggered upon receiving messages.
    # Writes the received message data to a CSV file, using a buffer file based on current time.
    # """
    # global buff_no
    # try:
        # # print("[On message]", message)
        # data = [[entry["tk"], entry["ltp"]] for entry in message['data'] if entry["ltp"] is not None]
           
        # # Convert the message to a DataFrame and append it to a CSV file named according to the buffer slot.
        # with open(f"all_data_{buff_no}.csv", mode='a', newline='') as file:
            # file_writer = writer(file)
            # file_writer.writerows(data)

    # except Exception as e:
        # print(f"[ERROR] Failed to process message: {e}")
        
# def on_message2(message):
    # global buff_no
    # message_data = message["data"]
    # with open(f"all_data_{buff_no}.csv", mode='a', newline='') as file:
        # file_writer = writer(file)
        # for i in message_data:
            # try:
                # tk = i.get('tk')
                # ltp = i.get('ltp')
                # if tk is not None and ltp is not None:
                    # file_writer.writerow([tk, ltp])
            # except Exception as e:
                # # print(f"[ERROR] Failed to process message: {e}")
                # pass

def get_instrument_tokens(client, tickers):
    """
    Retrieves instrument tokens for the given tickers from the NSE scrip master.
    """
    # Get the URL for the scrip master CSV file and read it into a DataFrame
    url = client.scrip_master(exchange_segment = "NSE")
    nse_df = pd.read_csv(url, sep = ",")

    # Clean column names
    nse_df.columns = [c.strip() for c in nse_df.columns]

    # Filter for requested tickers
    filtered_df = nse_df[(nse_df["pGroup"] == "EQ") & (nse_df["pSymbolName"].isin(tickers))]

    # Extract instrument tokens as a list of strings
    instrument_tokens = filtered_df["pSymbol"].astype(str).tolist()
    tickers = filtered_df["pSymbolName"].astype(str).tolist()
    
    print("[INFO] Got Instrument tokens")
    return instrument_tokens, tickers

def get_historical_data(instrument_tokens, tickers):
    """
    Downloads historical data for the provided tickers using yfinance.
    Saves the historical OHLC data to CSV files in the './history/' directory.
    """
    # Ensure history directory exists
    os.makedirs("./history", exist_ok=True)

    # Set up session with headers for better reliability
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0"
    }
    session = requests.Session()
    session.headers.update(headers)

    # Define the start and end dates for the historical data (last 5 days)
    start = dt.datetime.now() - dt.timedelta(days=no_of_days)
    end = dt.datetime.now()

    # Batch download data for all tickers at once
    # data = yf.download([f"{ticker}.NS" for ticker in tickers], start=start, end=end, interval=interval, session=session, group_by="ticker")

    for ticker, token in zip(tickers, instrument_tokens):
        try:
            # Try download data for ticker
            try: 
                df=yf.download(f"{ticker}.NS",start=start, end=end, interval=interval)
            except Exception as e:
                print(f"[ERROR] Failed to download data - {e}")
            
            if df.empty:
                print(f"[WARNING] No data for {ticker}, skipping...")
                continue

            # df = df.drop(columns=["Adj Close", "Volume"])
            df = df.tail(no_of_candles)
            df = df.drop(columns=["Volume"])
            
            # Save data to CSV
            df.columns = ["Close","High","Low","Open"]
            df.to_csv(f"./history/{token}.csv", index=False) 

            print(f"[INFO] Saved {ticker} data to {token}.csv")

        except KeyError:
            print(f"[ERROR] Missing data for {ticker}, skipping...")

    print("[INFO] Historical Data collection completed")

def create_main_thread(client, instrument_tokens):
    """
    Subscribes to live data feeds for the provided instrument tokens.
    """
    if not instrument_tokens or not isinstance(instrument_tokens, list):
        print("[ERROR] Invalid instrument_tokens: Expected a non-empty list")
        return
    
    tokens_list = [{"instrument_token": token, "exchange_segment": "nse_cm"} for token in instrument_tokens]
    
    try:
        client.subscribe(instrument_tokens=tokens_list, isIndex=False, isDepth=False)
        print(f"[INFO] Successfully subscribed to {len(tokens_list)} instruments")
    except Exception as e:
        print(f"[ERROR] Subscription failed: {e}")

def get_ltp_by_token(input_file):
    """
    Reads a CSV file containing live data and separates it by instrument token.
    Each token's prices are written to individual CSV files in the './by_token/' directory.
    """
    # Ensure input file exists
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file '{input_file}' not found.")
        return
    
    # Read CSV into a DataFrame
    try:
        df = pd.read_csv(input_file)
        df.columns = ["instrument_token", "price"]
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return

    # Check if DataFrame is empty
    if df.empty:
        print("[WARNING] Input CSV is empty. No processing required.")
        return

    # Group the DataFrame by 'instrument_token' and write each group's 'price' column to a separate CSV file
    for token, group in df.groupby("instrument_token"):
        output_file = f"./by_token/instrument_token_{token}.csv"
        group[["price"]].to_csv(output_file, index=False, header=False, mode="w")
        
def update_historical_data(instrument_tokens):
    """
    Updates historical data CSV files with the latest OHLC data calculated from live prices.
    """
    # For each instrument token, calculate OHLC from the live data CSV and append to historical CSV
    for token in instrument_tokens:
        live_data_file = f"./by_token/instrument_token_{token}.csv"

        # Check if live data file exists
        if not os.path.exists(live_data_file):
            print(f"[WARNING] Live data file for token {token} not found. Skipping...")
            continue

        try:
            data = pd.read_csv(live_data_file, header=None)

            if data.empty:
                print(f"[WARNING] Live data file for token {token} is empty. Skipping...")
                continue
        
            # Calculate OHLC
            Low = data.min()[0]  # Low
            High = data.max()[0]  # High
            Open = data.iloc[0][0]  # Open
            Close = data.iloc[-1][0]  # Close

            data = [Close,High,Low,Open]  
            
            # Append to historical data CSV
            with open(f"./history/{token}.csv", 'a', newline='') as file:
                writer_obj = writer(file)
                writer_obj.writerow(data)
        except Exception as e:
            print(f"[ERROR] Failed to process token {token}: {e}")

def supertrend_strategy(instrument_tokens):
    """
    Reads the last 40 candles from historical data CSV files, computes the Supertrend indicator,
    and returns stocks to buy or sell based on the latest signal.    """
    read_lines = 40
    buys, sells = [], []  # Lists to store buy/sell signals

    for token in instrument_tokens:
        file_path = f"./history/{token}.csv"

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"[WARNING] Historical data file for token {token} not found. Skipping...")
            continue

        try:
            # Read last 40 lines of the file efficiently
            df = pd.read_csv(file_path)
            df = df.tail(read_lines)

            if df.empty or len(df) < 7:  # Ensure sufficient data for Supertrend calculation
                print(f"[WARNING] Not enough data for token {token}. Skipping...")
                continue
        
            # Compute Supertrend Indicator
            sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=7, multiplier=3)
            super_trend_signal = sti["SUPERTd_7_3.0"].to_numpy()
        
            # conditions
            c1, c2 = super_trend_signal[-1], super_trend_signal[-2]

            # Identify Buy & Sell Signals
            if c1 == 1 and c2 != 1:  # Buy Condition
                buys.append(token)
            elif c1 != 1 and c2 == 1:  # Sell Condition
                sells.append(token)

        except Exception as e:
            print(f"[ERROR] Failed to process Supertrend for token {token}: {e}")

    return buys, sells
    
# def order_stocks(client, buys, sells, ticker_dict):
    # for sell in sells:
        # ticker = ticker_dict[str(sell)] + "-EQ"
        # # read file and check if ticker in the file if there execute else continue
        # try:
            # client.place_order(exchange_segment='nse_cm', product='NRML', price='0', order_type='MKT', quantity="20", validity='DAY', trading_symbol="ASHOKLEY-EQ",
                        # transaction_type='B', amo="NO", disclosed_quantity="0", market_protection="0", pf="N",
                        # trigger_price="0", tag=None)
            
            # print(f"[INFO] Order excecuted > TIcker:{ticker}, Quantity: 20")
        # except Exception as e:
            # print(f"[INFO] Unable to excecute order > TIcker:{ticker}: {e}")
        
    # for buy in buys:
        # ticker = ticker_dict[str(buy)] + "-EQ"
        # try:
            # client.place_order(exchange_segment='nse_cm', product='NRML', price='0', order_type='MKT', quantity="20", validity='DAY', trading_symbol="ASHOKLEY-EQ",
                        # transaction_type='B', amo="NO", disclosed_quantity="0", market_protection="0", pf="N",
                        # trigger_price="0", tag=None)
            
            # print(f"[INFO] Order excecuted > TIcker:{ticker}, Quantity: 20")
        # except Exception as e:
            # print(f"[INFO] Unable to excecute order > TIcker:{ticker}: {e}")


def order_stocks(client, buys, sells, instrument_dict):
    buys = [instrument_dict[str(buy)] for buy in buys]
    sells = [instrument_dict[str(sell)] for sell in sells]
    
    # Read existing file content into a set
    try:
        with open("positions.txt", 'r') as f:
            current_stocks = set(line.strip() for line in f)
    except FileNotFoundError:
        current_stocks = set()

    # Add buys and remove sells
    current_stocks.update(buys)
    current_stocks.difference_update(sells)

    # Write updated set back to file
    with open("positions.txt", 'w') as f:
        f.write('\n'.join(sorted(current_stocks)) + '\n')
