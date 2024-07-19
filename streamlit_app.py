import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
import calendar

ALPHA_VANTAGE_API_KEY = "5XOQ6YHBS0O3KBLF"

def main():
    st.set_page_config(layout="wide", page_title="Stock Market Analysis")
    
    # Add custom CSS for dark theme
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stSelectbox, .stTextInput {
        color: #fafafa;
    }
    .stPlotlyChart {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("Stock Market Analysis")
    menu = ["Overview", "Stock Performance", "Company Info", "News"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Overview":
        overview()
    elif choice == "Stock Performance":
        stock_performance()
    elif choice == "Company Info":
        company_info()
    elif choice == "News":
        news()

def overview():
    st.title("Stock Market Overview")
    
    symbol = "AAPL"  # Default to Apple Inc.
    
    # Set up the layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create the stock chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        # Fetch stock data
        data = fetch_stock_data(symbol)
        
        # Add candlestick chart
        fig.add_trace(go.Candlestick(x=data.index, open=data['1. open'], high=data['2. high'],
                                     low=data['3. low'], close=data['4. close'], name="OHLC"),
                      row=1, col=1)
        
        # Add volume bars
        fig.add_trace(go.Bar(x=data.index, y=data['5. volume'], name="Volume"),
                      row=2, col=1)
        
        # Add moving averages
        fig.add_trace(go.Scatter(x=data.index, y=data['4. close'].rolling(window=50).mean(),
                                 name="50-day MA", line=dict(color='orange', width=1)),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['4. close'].rolling(window=200).mean(),
                                 name="200-day MA", line=dict(color='purple', width=1)),
                      row=1, col=1)
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - Stock Price",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=600,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Financial data table
        financial_data = fetch_financial_data(symbol)
        
        st.subheader("Financial Data")
        for key, value in financial_data.items():
            st.text(f"{key}: {value}")

def fetch_stock_data(symbol):
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
    data, _ = ts.get_daily(symbol=symbol, outputsize='full')
    data = data.iloc[::-1]  # Reverse the dataframe so it's in chronological order
    return data.tail(365)  # Return the last year of data

def fetch_financial_data(symbol):
    # This is a placeholder. In a real application, you'd fetch this data from an API
    return {
        "Market Cap": "2.93T",
        "P/E Ratio": "30.82",
        "EPS (ttm)": "6.43",
        "Dividend Yield": "0.51%",
        "52 Week High": "240.00",
        "52 Week Low": "170.00",
    }

def calculate_percentage_change(start_price, end_price):
    return ((end_price - start_price) / start_price) * 100

def generate_range_statistics(data):
    ranges = ['ON', 'IB', 'RTH', 'RTH/IB', 'VOLUME']
    periods = ['5 DAY', '10 DAY', '20 DAY', '100 DAY']
    
    stats = {}
    for period in periods:
        days = int(period.split()[0])
        period_data = data.tail(days)
        
        stats[period] = {
            'MIN': period_data['3. low'].min(),
            'MEAN': period_data['4. close'].mean(),
            'MAX': period_data['2. high'].max(),
            'VOLUME': data['5. volume'].tail(days).sum() / 1000
        }
    
    df = pd.DataFrame(index=ranges)
    
    for period in periods:
        df[f"{period}_MIN"] = [stats[period]['MIN']] * 4 + [np.nan]
        df[f"{period}_MEAN"] = [stats[period]['MEAN']] * 4 + [stats[period]['VOLUME']]
        df[f"{period}_MAX"] = [stats[period]['MAX']] * 4 + [np.nan]
    
    return df

def stock_performance():
    st.title("Stock Performance")
    symbol = st.text_input("Enter stock symbol (e.g., AAPL for Apple):")
    if symbol:
        data = fetch_stock_data(symbol)
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                                             open=data['1. open'],
                                             high=data['2. high'],
                                             low=data['3. low'],
                                             close=data['4. close'])])
        
        fig.update_layout(title=f"{symbol} Stock Price",
                          xaxis_title="Date",
                          yaxis_title="Price",
                          xaxis_rangeslider_visible=False,
                          template="plotly_dark")

        # Add time frame selection
        time_frames = ['1M', '3M', '6M', '1Y']
        selected_time_frame = st.selectbox("Select Time Frame", time_frames)

        if selected_time_frame == '1M':
            start_date = data.index[-1] - pd.Timedelta(days=30)
        elif selected_time_frame == '3M':
            start_date = data.index[-1] - pd.Timedelta(days=90)
        elif selected_time_frame == '6M':
            start_date = data.index[-1] - pd.Timedelta(days=180)
        else:  # 1Y
            start_date = data.index[-1] - pd.Timedelta(days=365)

        fig.update_xaxes(range=[start_date, data.index[-1]])
        
        st.plotly_chart(fig, use_container_width=True)

        # Generate range statistics
        range_stats = generate_range_statistics(data)

        # Display the table
        st.subheader("RANGE STATISTICS")
        
        # Apply custom CSS
        st.markdown("""
        <style>
        table {
            color: white;
            font-size: 12px;
        }
        thead tr th {
            text-align: center !important;
            font-weight: bold;
        }
        thead tr:first-child th {
            background-color: #4a4a4a !important;
        }
        thead tr:nth-child(2) th {
            background-color: #333333 !important;
        }
        tbody tr:nth-of-type(even) {
            background-color: #333333;
        }
        tbody tr:nth-of-type(odd) {
            background-color: #1a1a1a;
        }
        th, td {
            text-align: right !important;
            padding: 5px !important;
        }
        th:first-child, td:first-child {
            text-align: left !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display the table
        st.table(range_stats.style.format({
            col: '{:.2f}' for col in range_stats.columns if not col.endswith('_MEAN')
        }).format({
            col: '{:.1f} K' for col in range_stats.columns if col.endswith('_MEAN')
        }).format('{:.2f}', na_rep='-'))

        # Calculate weekly and monthly percentage changes
        latest_price = data['4. close'].iloc[-1]
        
        # Weekly changes
        weekly_changes = []
        for i in range(4):  # Last 4 weeks
            start_date = data.index[-1] - pd.Timedelta(days=7*(i+1))
            end_date = data.index[-1] - pd.Timedelta(days=7*i)
            week_data = data[(data.index > start_date) & (data.index <= end_date)]
            if not week_data.empty:
                start_price = week_data['4. close'].iloc[0]
                end_price = week_data['4. close'].iloc[-1]
                weekly_changes.append({
                    'Period': f'Week {i+1}',
                    'Change (%)': calculate_percentage_change(start_price, end_price)
                })

        # Monthly changes
        monthly_changes = []
        for i in range(12):  # Last 12 months
            end_date = data.index[-1] - pd.Timedelta(days=30*i)
            start_date = end_date - pd.Timedelta(days=30)
            month_data = data[(data.index > start_date) & (data.index <= end_date)]
            if not month_data.empty:
                start_price = month_data['4. close'].iloc[0]
                end_price = month_data['4. close'].iloc[-1]
                month_name = calendar.month_name[end_date.month]
                monthly_changes.append({
                    'Period': f'{month_name} {end_date.year}',
                    'Change (%)': calculate_percentage_change(start_price, end_price)
                })

        # Create DataFrames for the tables
        weekly_df = pd.DataFrame(weekly_changes)
        monthly_df = pd.DataFrame(monthly_changes)

        # Display tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Weekly Performance")
            st.table(weekly_df.style.format({'Change (%)': '{:.2f}%'}))

        with col2:
            st.subheader("Monthly Performance")
            st.table(monthly_df.style.format({'Change (%)': '{:.2f}%'}))

        # Calculate and display average monthly movement
        avg_monthly_movement = monthly_df['Change (%)'].abs().mean()
        current_month_move = abs(monthly_df['Change (%)'].iloc[0])
        difference = current_month_move - avg_monthly_movement

        st.subheader("Monthly Movement Analysis")
        st.write(f"Average monthly movement: {avg_monthly_movement:.2f}%")
        st.write(f"Current month's movement: {current_month_move:.2f}%")
        st.write(f"Difference from average: {difference:.2f}%")

        if difference > 0:
            st.write(f"The stock is moving {difference:.2f}% more than its average monthly movement.")
        else:
            st.write(f"The stock is moving {abs(difference):.2f}% less than its average monthly movement.")

def company_info():
    st.title("Company Information")
    st.write("This section will display company information. It's currently under development.")

def news():
    st.title("Stock Market News")
    st.write("This section will display stock market news. It's currently under development.")

if __name__ == "__main__":
    main()