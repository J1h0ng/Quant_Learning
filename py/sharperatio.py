import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

print("正在下載2330-TW台積電歷史數據")
df = yf.download(tickers="2330.TW", start="2016-01-01", end="2026-01-01", auto_adjust=True)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df[["Close"]].copy()
df.dropna(inplace=True)

df["MA10"] = df["Close"].rolling(window=10).mean()  #計算均線
df["MA60"] = df["Close"].rolling(window=60).mean()  #計算均線

df['Daily_Return'] = df['Close'].pct_change()   #計算原始每日報酬

df["Signal"] = np.where(df['MA10'] > df['MA60'], 1, 0)
df['Position'] = df['Signal'].shift(1)
df['Strategy_Return'] = df['Position'] * df['Daily_Return']
daily_risk_free = 0.04/252

bh_mean = df["Daily_Return"].mean()
bh_std = df['Daily_Return'].std()
bh_sharpe = (bh_mean - daily_risk_free) / bh_std * np.sqrt(252)

st_mean = df['Strategy_Return'].mean()
st_std = df['Strategy_Return'].std()
st_sharpe = (st_mean - daily_risk_free) / st_std * np.sqrt(252)

print(f"買進持有的每日平均報酬是{bh_mean:.4f}，波動(標準差)是{bh_std:.4f}，夏普比率是{bh_sharpe:.3f}")
print(f"策略買進的每日平均報酬是{st_mean:.4f}，波動(標準差)是{st_std:.4f}，夏普比率是{st_sharpe:.3f}")

short_ma_range = range(5, 65, 5)
long_ma_range = range(20, 120, 10)
results = []
print("計算中")
for short_ma in short_ma_range:
    for long_ma in long_ma_range:
        if short_ma >= long_ma:
            continue

        temp_df = df[['Close', 'Daily_Return']].copy()
        temp_df['Short_MA'] = temp_df['Close'].rolling(window=short_ma).mean()
        temp_df['Long_MA'] = temp_df['Close'].rolling(window=long_ma).mean()

        # 2. 產生訊號
        # 只要 短 > 長 就持有 (1)，否則空手 (0)
        temp_df['Signal'] = np.where(temp_df['Short_MA'] > temp_df['Long_MA'], 1, 0)

        # 3. 計算策略報酬 (記得 shift 1 天)
        temp_df['Strategy_Return'] = temp_df['Signal'].shift(1) * temp_df['Daily_Return']

        # 4. 計算夏普比率
        daily_mean = temp_df['Strategy_Return'].mean()
        daily_std = temp_df['Strategy_Return'].std()
        # 防呆：如果標準差是 0 (完全沒交易)，夏普設為 0
        if daily_std == 0:
            sharpe = 0
        else:
            sharpe = (daily_mean - daily_risk_free) / daily_std * np.sqrt(252)

        # 5. 存檔
        results.append({
            'Short_MA': short_ma,
            'Long_MA': long_ma,
            'Sharpe': sharpe
        })

results_df = pd.DataFrame(results)
# 依照夏普比率由大到小排序
results_df = results_df.sort_values(by='Sharpe', ascending=False).reset_index(drop=True)

# --- 顯示前 10 名 ---
print("\n 最強均線組合 Top 10 ")
print(results_df.head(10))

# --- 顯示墊底 5 名 (避雷區) ---
print("\n 最爛均線組合 Bottom 5")
print(results_df.tail(5))