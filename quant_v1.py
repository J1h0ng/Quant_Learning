import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. 設定參數
ticker = '2330-TW'  # 台積電
start_date = '2023-01-01'
end_date = '2026-01-13'

# 2. 獲取數據 (改用更穩定的 Ticker.history 方法)
print(f"正在透過 Ticker 物件下載 {ticker} 的數據...")
stock = yf.Ticker(ticker)
# auto_adjust=True 表示下載回來的 'Close' 已經是還原權值後的價格 (即 Adj Close)
data = stock.history(start=start_date, end=end_date, auto_adjust=True)

# --- 工程師的 Debug 區 ---
print(f"下載完成，欄位名稱為: {data.columns}")
# -----------------------

# 3. 資料清洗 (Data Cleaning)
# 因為用了 auto_adjust=True，所以我們直接用 'Close' 當作調整後收盤價
if 'Close' in data.columns:
    df = data[['Close']].copy()

     # 改名以符合後面的邏輯
elif 'Adj Close' in data.columns:
    df = data[['Adj Close']].copy()
else:
    raise ValueError(f"錯誤：找不到收盤價欄位，現有欄位: {data.columns}")

# 4. 計算指標 (Indicators)
# A. 移動平均線 (SMA)
df['SMA_20'] = df['Adj Close'].rolling(window=20).mean()
df['SMA_60'] = df['Adj Close'].rolling(window=60).mean()

# B. 計算 RSI
delta = df['Adj Close'].diff()
gain = (delta.where(delta > 0, 0))
loss = (-delta.where(delta < 0, 0))

avg_gain = gain.ewm(com=13, adjust=False).mean()
avg_loss = loss.ewm(com=13, adjust=False).mean()
rs = avg_gain / avg_loss
df['RSI'] = 100 - (100 / (1 + rs))

# 5. 制定策略邏輯
# 買入：(短 > 長) AND (RSI < 70)
condition_buy = (df['SMA_20'] > df['SMA_60']) & (df['RSI'] < 70)
df['Signal'] = np.where(condition_buy, 1.0, 0.0)

# 計算買賣點 (1: Buy, -1: Sell)
df['Position'] = df['Signal'].diff()

# 6. 視覺化 (Visualization)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

# 上圖：股價與均線
ax1.plot(df.index, df['Adj Close'], label='Price', color='gray', alpha=0.5)
ax1.plot(df.index, df['SMA_20'], label='SMA 20', color='orange', alpha=0.8)
ax1.plot(df.index, df['SMA_60'], label='SMA 60', color='blue', alpha=0.8)

# 標記買入點
buy_idx = df[df['Position'] == 1].index
buy_val = df['SMA_20'][df['Position'] == 1]
ax1.plot(buy_idx, buy_val, '^', markersize=10, color='green', label='Buy')

# 標記賣出點
sell_idx = df[df['Position'] == -1].index
sell_val = df['SMA_20'][df['Position'] == -1]
ax1.plot(sell_idx, sell_val, 'v', markersize=10, color='red', label='Sell')

ax1.set_title(f'{ticker} Strategy: SMA + RSI Filter (Fixed Version)')
ax1.set_ylabel('Price (TWD)')
ax1.legend(loc='upper left')
ax1.grid(True)

# 下圖：RSI
ax2.plot(df.index, df['RSI'], color='purple', label='RSI')
ax2.axhline(70, color='red', linestyle='--', label='Overbought (70)')
ax2.axhline(30, color='green', linestyle='--', label='Oversold (30)')
ax2.set_ylabel('RSI')
ax2.set_xlabel('Date')
ax2.legend(loc='upper left')
ax2.grid(True)

plt.show()
print("正在進行績效回測計算...")

# 1. 計算每日的市場報酬率 (Market Returns)
# pct_change() 計算 (今天價格 - 昨天價格) / 昨天價格
df['Market_Returns'] = df['Adj Close'].pct_change()

# 2. 計算策略報酬率 (Strategy Returns)
# 關鍵工程邏輯：我們必須用「昨天」的訊號來決定「今天」的動作。
# 所以 Signal 必須 shift(1) 往後移一天。如果不移，就是偷看答案 (Look-ahead Bias)。
df['Strategy_Returns'] = df['Market_Returns'] * df['Signal'].shift(1)

# 3. 計算累積報酬率 (Cumulative Returns)
# 使用 cumprod() (累積乘積) 來模擬複利效果
df['Cumulative_Market'] = (1 + df['Market_Returns']).cumprod()
df['Cumulative_Strategy'] = (1 + df['Strategy_Returns']).cumprod()

# 4. 算出最終總報酬 (Total Return)
final_market_return = df['Cumulative_Market'].iloc[-1] - 1
final_strategy_return = df['Cumulative_Strategy'].iloc[-1] - 1

print(f"----- 回測結果 (2022-2024) -----")
print(f"台積電買進持有總回報: {final_market_return:.2%}")
print(f"SMA+RSI 策略總回報:   {final_strategy_return:.2%}")

# 5. 繪製績效對比圖 (Performance Chart)
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['Cumulative_Market'], label='Buy & Hold (Market)', color='blue', alpha=0.6)
plt.plot(df.index, df['Cumulative_Strategy'], label='SMA + RSI Strategy', color='orange', linewidth=2)

plt.title(f'{ticker} Performance Comparison: Strategy vs. Market')
plt.ylabel('Cumulative Return (1.0 = Breakeven)')
plt.legend(loc='best')
plt.grid(True)
plt.show()