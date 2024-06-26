# Lambda function AWS

# Imports
import time
import pandas as pd
from io import StringIO
from pandas import json_normalize
from datetime import datetime, timedelta
from log_manager import S3LogManager
from util import control_sucess, infer_schema, convert_to_string
from stocks_fiis_modules import validate_data_stocks
from json_upload import write_json_to_s3
from api_requests import Brapi_STOCKS_API, Brapi_notSTOCKS__API

# Variables imports [!WARNING] dont forget to change in config.py file.
from config import BASE_URL, REGION_NAME, \
    BUCKET, RAW_PREFIX, LOG_PREFIX, NAME_FUN, TOKEN_GENERATOR, TICKERS


# V0 inicial structure for logging ect
def lambda_handler(event, context):
    inicio = time.perf_counter()
    control = "OK"
    timestamp_SP = datetime.now() - timedelta(hours=3)
    #timestamp_SP_api_pull = timestamp_SP - timedelta(days=1)
    
    # loop df ... [!WARNING] if dont use it change in row 58
    #df_append = pd.DataFrame()

    # api class for requests
    params = {
        'range': '1d',
        'interval': '1d',
        'fundamental': 'true',
        'token': TOKEN_GENERATOR,
    }
    
    
    api = Brapi_STOCKS_API(
        url=BASE_URL,
        tickers=TICKERS, 
        params=params
    )
    
    
    # --------------------Api requests wra wrangling
    # ------------------- Use Try and execept
 
    #----------------- execept + control_var for logs management
    try:
        json_data = api.get_quotes()
        schema =infer_schema(json_data)
        check_json = validate_data_stocks(json_data)
        for coin in check_json:
            coin['dateingestion_sp'] = timestamp_SP.strftime("%Y-%m-%d %H:%M:%S")

    #----------------- execept + control_var for logs management

    
    except Exception as e:
         control = f'Error msg: {e}'
         print(
             "Project: The request returned 0 items. Original message: {msg}".format(
                 msg=e
             )
         )
                        
    # -------------------------- usual final strucuture for uploading and logging the ingestion.
    
    sucess_var = control_sucess(control)

    file_s3= 0
    if control == "OK":
        file_s3, file_size = write_json_to_s3(check_json, BUCKET, RAW_PREFIX, timestamp_SP)
        print(f"Project: Json file saved to S3 at: \n {file_s3}")
        print(f"Project: Json file size: {file_size} bytes")
        
    fim = time.perf_counter()
    log_manager = S3LogManager(BUCKET, LOG_PREFIX, control)
    time_var = round((fim - inicio),2)
    log_manager.add_log_entry(NAME_FUN, sucess_var, time_var, control, file_size)

# ! lambda_handler('','') !