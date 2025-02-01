import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="Advanced Stock Analysis Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: white;
        color: #1e1e1e;
        border: 1px solid #e1e4e8;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #f5f5f5;
        border-color: #d1d1d1;
    }
    .stTextInput>div>div>input {
        color: #1e1e1e;
    }
    .highlight {
        border-radius: 0.4rem;
        color: white;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    .css-1d391kg {
        padding: 1rem 1rem 1.5rem;
    }
    .css-12oz5g7 {
        padding: 1rem 1rem 1.5rem;
    }
    .metric-card {
        border: 1px solid #e1e4e8;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .metric-card h4 {
        margin: 0;
        font-size: 1.2rem;
        color: #1e1e1e;
    }
    .metric-card p {
        margin: 0;
        font-size: 1rem;
        color: #555;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #1e1e1e;
    }
    .stMarkdown p {
        color: #555;
    }
    .stSidebar {
        background-color: #f8f9fa;
    }
    .stSidebar .stMarkdown h1, .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3 {
        color: #1e1e1e;
    }
    .stSidebar .stMarkdown p {
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Configuration")
    st.subheader("Time Period")
    start_date = st.date_input(
        "Start Date",
        value=date.today() - timedelta(days=365),
        min_value=date(1980, 1, 1),
        max_value=date.today()
    )
    end_date = st.date_input(
        "End Date",
        value=date.today(),
        min_value=date(1980, 1, 1),
        max_value=date.today()
    )
    st.subheader("Analysis Parameters")
    percent_threshold = st.slider(
        "Market Movement Threshold (%)",
        min_value=5,
        max_value=40,
        value=20,
        help="Percentage change threshold for identifying significant market movements"
    )
    
    ma_periods = st.multiselect(
        "Moving Averages",
        options=[20, 50, 100, 200],
        default=[50, 200],
        help="Select moving average periods to display"
    )

st.title("Advanced Stock Analysis Dashboard")
# st.markdown("""
#     <div class='highlight' style='background-color: #1e1e1e;'>
#     <h4 style='margin:0;'>Warren Buffett's Wisdom:</h4>
#     <i>"Be fearful when others are greedy and be greedy when others are fearful."</i>
#     </div>
#     """, unsafe_allow_html=True)

# Stock selection
col1, col2 = st.columns([2, 1])
with col1:
    selected_stock = st.text_input(
        "Enter Stock Symbol",
        value="AAPL",
        help="Enter the stock symbol (e.g., AAPL for Apple)"
    ).upper()

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  
    analyze_button = st.button("Analyze Stock", type="primary")

popular_stocks = {
    "AAPL": "Apple",
    "GOOGL": "Google",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "META": "Meta"
}

cols = st.columns(len(popular_stocks))
for idx, (symbol, name) in enumerate(popular_stocks.items()):
    with cols[idx]:
        if st.button(f"{symbol}\n{name}"):
            selected_stock = symbol

# Function to get stock data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_stock_data(symbol, start_date, end_date):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date)
        if df.empty:
            return None
        
        # Get basic info
        info = {}
        try:
            stock_info = stock.info
            info = {
                'marketCap': stock_info.get('marketCap', 0),
                'fiftyTwoWeekLow': stock_info.get('fiftyTwoWeekLow', 0),
                'fiftyTwoWeekHigh': stock_info.get('fiftyTwoWeekHigh', 0)
            }
        except:
            info = {
                'marketCap': 0,
                'fiftyTwoWeekLow': df['Low'].min(),
                'fiftyTwoWeekHigh': df['High'].max()
            }
        
        return {
            'df': df,
            'info': info
        }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

if analyze_button or selected_stock:
    data_load = get_stock_data(selected_stock, start_date, end_date)
    if data_load:
        df = data_load['df']
        info = data_load['info']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Current Price",
                f"${df['Close'][-1]:.2f}",
                f"{((df['Close'][-1] - df['Close'][-2]) / df['Close'][-2] * 100):.2f}%"
            )
        with col2:
            st.metric(
                "Market Cap",
                f"${info['marketCap'] / 1e9:.2f}B"
            )
        with col3:
            st.metric(
                "52 Week Range",
                f"${info['fiftyTwoWeekLow']:.2f} - ${info['fiftyTwoWeekHigh']:.2f}"
            )

        st.subheader("Technical Analysis")
        
        # Calculate moving averages
        for period in ma_periods:
            df[f'MA{period}'] = df['Close'].rolling(window=period).mean()

        # Create interactive chart
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC'
        ))
        
        for period in ma_periods:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[f'MA{period}'],
                name=f'{period} Day MA',
                line=dict(width=2)
            ))
        
        # Update layout
        fig.update_layout(
            title=f'{selected_stock} Stock Price',
            yaxis_title='Stock Price (USD)',
            xaxis_title='Date',
            template='plotly_dark',
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Market Analysis
        st.subheader("Market Analysis")
        
        # Calculate peaks and troughs
        df['Rolling_Max'] = df['Close'].rolling(window=20).max()
        df['Rolling_Min'] = df['Close'].rolling(window=20).min()
        
        current_price = df['Close'][-1]
        peak_price = df['Rolling_Max'][-1]
        trough_price = df['Rolling_Min'][-1]
        
        # Market status
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Market Status")
            percent_from_peak = ((current_price - peak_price) / peak_price) * 100
            
            if percent_from_peak <= -percent_threshold:
                st.markdown(f"""
                    <div class='metric-card' style='border-left: 4px solid #4CAF50;'>
                        <h4 style='color: #4CAF50; margin:0;'>BUY Signal</h4>
                        <p>Market is down {abs(percent_from_peak):.2f}% from peak</p>
                    </div>
                    """, unsafe_allow_html=True)
            elif percent_from_peak >= percent_threshold:
                st.markdown(f"""
                    <div class='metric-card' style='border-left: 4px solid #f44336;'>
                        <h4 style='color: #f44336; margin:0;'>SELL Signal</h4>
                        <p>Market is up {percent_from_peak:.2f}% from trough</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card' style='border-left: 4px solid #FFA500;'>
                        <h4 style='color: #FFA500; margin:0;'>HOLD Signal</h4>
                        <p>Market is within normal range</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            # Volatility analysis
            st.markdown("### Volatility Analysis")
            df['Daily_Return'] = df['Close'].pct_change()
            volatility = df['Daily_Return'].std() * np.sqrt(252) * 100  # Annualized volatility
            
            st.markdown(f"""
                <div class='metric-card'>
                    <h4 style='margin:0;'>Annual Volatility</h4>
                    <p style='font-size: 24px; margin:0;'>{volatility:.2f}%</p>
                </div>
                """, unsafe_allow_html=True)

        # Volume Analysis
        st.subheader("Volume Analysis")
        
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume'
        ))
        
        fig_volume.update_layout(
            title='Trading Volume',
            yaxis_title='Volume',
            xaxis_title='Date',
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig_volume, use_container_width=True)

        st.subheader("Risk Analysis")
        
        returns = df['Close'].pct_change()
        
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=returns,
            name='Returns Distribution',
            nbinsx=50,
            histnorm='probability'
        ))
        
        fig_dist.update_layout(
            title='Returns Distribution',
            xaxis_title='Daily Returns',
            yaxis_title='Probability',
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("---")
st.markdown("""
    <div style='text-align: center;'>
    <h4>📊 Advanced Stock Analysis Dashboard</h4>
    <p>Disclaimer: This tool is for informational purposes only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

if st.button("Clear Cache"):
    st.cache_data.clear()
    st.success("Cache cleared!")