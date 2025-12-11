import json
import pandas as pd
from fastapi import status

from app.core.exceptions import CustomException
from loguru import logger
from app.config import settings
from app.cache.redis import RedisCache
from app.schemas.fx import FxResponse


fx_cache = RedisCache(prefix="fx_rate", model_class=FxResponse)

async def fx_rate_service(currency, date_time):

    try:
        # Convert currency code to uppercase
        curr = currency.upper()
        fx_key = f'{str(date_time).replace(" ", "_")}_{curr}'

        # Try to get from cache first
        cached_fx = await fx_cache.get(str(fx_key))
        
        if cached_fx:
            logger.info(f"Fx {cached_fx} found in cache")
            return cached_fx

        # path for FX rate file
        file_path =  settings.FILE_PATH

        # read data from cvs file
        df = pd.read_csv(file_path)

        # Convert date_time column to datetime
        df["date_time"] = pd.to_datetime(df["date_time"])

        # round up to two decimal
        df[["buy_rate", "sell_rate"]] = df[["buy_rate", "sell_rate"]].round(2)

        # filter the data by currency code
        df = pd.DataFrame(df[df["currency_code"] == curr])
        if df.empty:

            logger.warning(f"Record not found for currency {curr}")
            raise CustomException(
                    status_code = status.HTTP_200_OK,
                    code="4001",
                    message=f"Record not found"
                )
        
        df = df.sort_values("date_time").reset_index(drop=True)
        nearest_fx = await get_nearest_rate(df, date_time, curr)
        return nearest_fx
    
    except CustomException as e:
        raise
    except Exception as e:
        raise Exception


async def get_nearest_rate(df, ts, curr):

    try:
        ts = pd.to_datetime(ts)

        # 1. EXACT MATCH CHECK
        exact_match = df[df["date_time"] == ts]
        if not exact_match.empty:
            match_df = exact_match.iloc[0]
            data_dict = match_df.to_dict()

            # Convert date_time to ISO string
            if isinstance(data_dict['date_time'], pd.Timestamp):
                data_dict['date_time'] = data_dict['date_time'].isoformat()

            fx_response = FxResponse.model_validate(data_dict)

            fx_key = f'{str(ts).replace(" ", "_")}_{curr}'
            fx_response = FxResponse.model_validate(data_dict)
            await fx_cache.set(str(fx_key), fx_response)

            return fx_response

        # 2. PAST LOOKUP ONLY (date_time < ts)
        past_df = df[df["date_time"] <= ts]

        if past_df.empty:
            logger.warning(f"Record not found for datetime: {ts}")
            raise CustomException(
                    status_code = status.HTTP_200_OK,
                    code="4001",
                    message=f"Record not found"
                )
        
        # 3. Nearest past = the last entry before ts
        nearest_past = past_df.iloc[-1] 
        # Convert to dictionary
        data_dict = nearest_past.to_dict()
        
        # Convert datetime to ISO string
        if isinstance(data_dict['date_time'], pd.Timestamp):
            data_dict['date_time'] = data_dict['date_time'].isoformat()

        fx_response = FxResponse.model_validate(data_dict)
        
        fx_key = f'{str(ts).replace(" ", "_")}_{curr}'
        await fx_cache.set(str(fx_key), fx_response)

        return fx_response
    
    except CustomException as e:
        raise
    except Exception as e:
        raise Exception