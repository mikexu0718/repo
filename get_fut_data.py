import akshare as ak
from datetime import datetime
import pandas as pd
import numpy as np
from config import DATA_DIR
from datetime import timedelta


def get_fut(code: str):
    code = str(code)
    df_ = ak.futures_main_sina(symbol=code, start_date="19900101", end_date=datetime.now().strftime('%Y%m%d'))
    df_.rename(columns={'日期': 'date', '开盘价': 'open', '最高价': 'high', '最低价': 'low', '收盘价': 'close',
                       '成交量': 'volume',
                       '持仓量': 'open_interest', '动态结算价': 'vwap'}, inplace=True)
    
    last_close = ak.futures_zh_spot(symbol=code)
    current_date = datetime.now().date() if datetime.now().hour < 21 else datetime.now().date() + timedelta(days=1)
    last_row = pd.DataFrame({
        'date': [current_date],
        'open': [last_close['open'].iloc[-1]],
        'high': [last_close['high'].iloc[-1]],
        'low': [last_close['low'].iloc[-1]],
        'close': [last_close['current_price'].iloc[-1]],
        'volume': [last_close['volume'].iloc[-1]],
        'open_interest': [last_close['hold'].iloc[-1]],
        'vwap': [last_close['open'].iloc[-1]],
    })
    
    df_ = pd.concat([df_, last_row], ignore_index=True)
    df_['symbol'] = code
    
    df_.to_csv(DATA_DIR.joinpath(code + '.csv'), index=None)
    
    return df_
