import yfinance as yf
import pandas as pd
import numpy as np
import itertools

# 1. 獲取數據 (鎖定你指定的 2024-2026 區間)
ticker = 'BTC-USD'
start_date = '2023-01-01'
end_date = '2026-01-13'

print(f"正在下載 {ticker} 數據 ({start_date} ~ {end_date})...")
stock = yf.Ticker(ticker)
data = stock.history(start=start_date, end=end_date, auto_adjust=True)

# 資料清洗
if 'Close' in data.columns:
    df_base = data[['Close']].copy()
    df_base.rename(columns={'Close': 'Adj Close'}, inplace=True)
else:
    df_base = data[['Adj Close']].copy()

# 計算大盤(買入持有)的基準報酬
market_return = (df_base['Adj Close'].iloc[-1] / df_base['Adj Close'].iloc[0]) - 1
print(f"基準大盤報酬 (Buy & Hold): {market_return:.2%}")
print("-" * 50)

# 2. 定義參數範圍 (Parameter Grid)
# 我們要測試的參數組合
short_windows = range(1, 15, 2)  # 短均線：3, 5, 7... 13
long_windows = range(20, 120, 5)  # 長均線：20, 25... 60
rsi_thresholds = [70, 75, 80, 85, 90, 95, 100]  # RSI 限制：70(保守) ~ 100(完全不限制)

results = []

print("開始進行參數最佳化 (Grid Search)... 這可能需要幾秒鐘...")

# 3. 暴力迴圈 (Brute Force Loop)
# 使用 itertools.product 產生所有組合
param_combinations = list(itertools.product(short_windows, long_windows, rsi_thresholds))

for short_w, long_w, rsi_limit in param_combinations:
    # 邏輯保護：短均線必須小於長均線，否則跳過
    if short_w >= long_w:
        continue

    # 複製一份乾淨的數據
    df = df_base.copy()

    # A. 計算指標
    df['SMA_S'] = df['Adj Close'].rolling(window=short_w).mean()
    df['SMA_L'] = df['Adj Close'].rolling(window=long_w).mean()

    # RSI 計算 (簡化版)
    delta = df['Adj Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(com=13, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # B. 策略邏輯
    # 買入條件：短 > 長 且 RSI < 限制 (如果設 100 等於不看 RSI)
    condition = (df['SMA_S'] > df['SMA_L']) & (df['RSI'] < rsi_limit)
    df['Signal'] = np.where(condition, 1.0, 0.0)

    # C. 計算回報
    df['Market_Returns'] = df['Adj Close'].pct_change()
    df['Strategy_Returns'] = df['Market_Returns'] * df['Signal'].shift(1)

    # 累積回報
    cum_ret = (1 + df['Strategy_Returns']).cumprod().iloc[-1] - 1

    # 記錄結果
    results.append({
        'Short_MA': short_w,
        'Long_MA': long_w,
        'RSI_Limit': rsi_limit,
        'Return': cum_ret
    })

# 4. 分析結果
results_df = pd.DataFrame(results)
# 依照報酬率由高到低排序
best_results = results_df.sort_values(by='Return', ascending=False).head(5)

print("\n----- 最佳參數組合 TOP 5 -----")
print(best_results)

print("\n----- 結論分析 -----")
best_return = best_results.iloc[0]['Return']
print(f"最佳策略回報: {best_return:.2%}")
print(f"大盤回報:     {market_return:.2%}")

if best_return > market_return:
    print("成功：優化後的參數擊敗了大盤")
else:
    print("失敗：即使優化也無法擊敗大盤 (強勢多頭中，持有通常是王道)。")