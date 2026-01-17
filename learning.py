import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ticker = input("請輸入想查詢的股票號碼(Yahoo Finance)")
start_date = "2006-01-15"
end_date = "2026-01-15"

print("-------------------------------------------------")
print("正在下載", ticker, "數據......")
stock = yf.Ticker(ticker)
data = stock.history(start = start_date, end = end_date, auto_adjust = True)

print("下載完成", data.columns)

if "Close" in data.columns:
    df = data[["Close"]].copy()
    df.rename(columns={'Close': 'Adj Close'}, inplace=True)
elif 'Adj Close' in data.columns:
    df = data[['Adj Close']].copy()
else:
    raise ValueError(f"錯誤：找不到收盤價欄位，現有欄位: {data.columns}")

df["SMA_20"] = df["Adj Close"].rolling(window=20).mean()
df["SMA_60"] = df["Adj Close"].rolling(window=60).mean()

fig, ax1 = plt.subplots(1, 1, figsize=(14, 10))
ax1.plot(df.index, df['Adj Close'], label='Price', color='gray', alpha=0.5)
ax1.plot(df.index, df['SMA_20'], label='SMA 20', color='orange', alpha=0.8)
ax1.plot(df.index, df['SMA_60'], label='SMA 60', color='blue', alpha=0.8)

ax1.legend(loc='best')

plt.title(f"{ticker} Stock Price")
plt.xlabel("Date")
plt.ylabel("Price")

plt.show()