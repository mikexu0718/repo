import streamlit as st
import pandas as pd
import numpy as np
import talib
from get_fut_data import get_fut
from config import DATA_DIR
import plotly.graph_objects as go

def create_gauge(value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 20], 'color': "lightgray"},
                {'range': [20, 40], 'color': "lightgray"},
                {'range': [40, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "lightgray"},
                {'range': [80, 100], 'color': "lightgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig.update_layout(paper_bgcolor="lavender", 
                      font={'color': "darkblue", 'family': "Arial"})
    return fig


def create_candlestick_chart(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])

    fig.add_trace(go.Scatter(x=df['date'], y=df['close'].rolling(window=5).mean(), mode='lines', name='MA5', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['date'], y=df['close'].rolling(window=10).mean(), mode='lines', name='MA10', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df['date'], y=df['close'].rolling(window=20).mean(), mode='lines', name='MA20', line=dict(color='purple')))
    
    fig.update_layout(
        title='股票价格走势图',
        xaxis_title='日期',
        yaxis_title='价格',
        xaxis_rangeslider_visible=False
    )
    return fig


def calculate_technical_indicators(df):
    # 计算MA
    df['ma5'] = talib.SMA(df['close'], timeperiod=5)
    df['ma10'] = talib.SMA(df['close'], timeperiod=10)
    df['ma20'] = talib.SMA(df['close'], timeperiod=20)
    
    # 计算BBI
    df['bbi'] = (talib.SMA(df['close'], timeperiod=3) + talib.SMA(df['close'], timeperiod=6) +
                 talib.SMA(df['close'], timeperiod=12) + talib.SMA(df['close'], timeperiod=24)) / 4
    
    # 计算RSI
    df['rsi_6'] = talib.RSI(df['close'], timeperiod=6)
    df['rsi_12'] = talib.RSI(df['close'], timeperiod=12)
    
    # 计算MACD
    df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    
    # 计算KD
    df['slowk'], df['slowd'] = talib.STOCH(df['high'], df['low'], df['close'],
                                           fastk_period=3, slowk_period=3, slowd_period=9)
    
    # 计算WR
    df['wr'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
    
    # 计算ADX
    df['plus_di'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
    df['minus_di'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
    df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
    
    return df

# 根据技术指标判断交易方向
def determine_trade_signal(df):
    signals = {}

    macd_signal = '看多' if df['macd'].iloc[-1] > df['macdsignal'].iloc[-1] else '看空'
    signals['MACD指标'] = macd_signal
    
    rsi_signal = '超卖' if df['rsi_6'].iloc[-1] < 30 else ('超买' if df['rsi_6'].iloc[-1] > 70 else '中性')
    signals['RSI相对强弱指标'] = rsi_signal

    rsi_cross = '看多' if df['rsi_6'].iloc[-1] > df['rsi_12'].iloc[-1] else ('看空' if df['rsi_6'].iloc[-1] < df['rsi_12'].iloc[-1] else '中性')
    signals['RSI交叉(6,12)'] = rsi_cross
    
    kd_signal = '看多' if df['slowk'].iloc[-1] > df['slowd'].iloc[-1] else '看空'
    signals['KD随机指标'] = kd_signal

    bbi_signal = '看多' if df['close'].iloc[-1] > df['bbi'].iloc[-1] else ('看空' if df['close'].iloc[-1] < df['bbi'].iloc[-1] else '中性')
    signals['BBI指标'] = bbi_signal
    
    wr_signal = '看多' if df['wr'].iloc[-1] < -80 else ('看空' if df['wr'].iloc[-1] > -20 else '中性')
    signals['WR威廉指标'] = wr_signal
    
    if df['adx'].iloc[-1] > 25:
        if df['plus_di'].iloc[-1] > df['minus_di'].iloc[-1]:
            adx_signal = '看多'
        else:
            adx_signal = '看空'
    else:
        adx_signal = '中性'
    signals['ADX趋势指标'] = adx_signal

    ma_5_signal = '看多' if df['close'].iloc[-1] > df['ma5'].iloc[-1] else ('看空' if df['close'].iloc[-1] < df['ma5'].iloc[-1] else '中性')
    signals['移动平均线(5)'] = ma_5_signal

    ma_10_signal = '看多' if df['close'].iloc[-1] > df['ma10'].iloc[-1] else ('看空' if df['close'].iloc[-1] < df['ma10'].iloc[-1] else '中性')
    signals['移动平均线(10)'] = ma_10_signal

    ma_20_signal = '看多' if df['close'].iloc[-1] > df['ma20'].iloc[-1] else ('看空' if df['close'].iloc[-1] < df['ma20'].iloc[-1] else '中性')
    signals['移动平均线(20)'] = ma_20_signal

    return signals

def add_arrows_to_signals(signals):
    for key, value in signals.items():
        if value == '看多':
            signals[key] += ' 🔴⬆'
        elif value == '看空':
            signals[key] += ' 🟢⬇'
    return signals

# Streamlit界面
st.markdown(
    """
    <style>
    .title {
        font-size: 32px;
        font-weight: bold;
        color: #A9A9A9;
        text-align: center;
        border-radius: 10px;
        font-family: 'SimSun', serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">MK期貨-技術分析工具</div>', unsafe_allow_html=True)

# 上传CSV数据
uploaded_file = st.file_uploader('上传期货数据文件', type=['csv'])
futures_code = st.text_input('或者输入期货代码')

if futures_code:
    csv_file = get_fut(futures_code)
    file_ads = DATA_DIR.joinpath(futures_code + '.csv')
    uploaded_file = file_ads

if st.button('开始分析'):

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df['date'] = pd.to_datetime(df['date'])
        st.write(df)
        st.write("上传的数据：", df.head())
        fig = create_candlestick_chart(df)
        st.plotly_chart(fig, use_container_width=True)
        df.columns = df.columns.str.lower()
        df = calculate_technical_indicators(df)
        trade_signals = determine_trade_signal(df)
        st.write("技术指标计算结果：", df.tail())
        trade_signals = add_arrows_to_signals(trade_signals)
        signal_df = pd.DataFrame.from_dict(trade_signals, orient='index', columns=['交易方向信号'])
        st.write("交易信号：", signal_df)
