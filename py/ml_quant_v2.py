import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier

# 1. 準備數據
print("下載數據中...")
tw = yf.download("2330.TW", start="2016-01-01", end="2026-01-01", auto_adjust=True)
us = yf.download("^SOX", start="2016-01-01", end="2026-01-01", auto_adjust=True)

# 解決 MultiIndex 問題
if isinstance(tw.columns, pd.MultiIndex): tw.columns = tw.columns.get_level_values(0)
if isinstance(us.columns, pd.MultiIndex): us.columns = us.columns.get_level_values(0)

# 2. 特徵工程 (Feature Engineering)
df = pd.DataFrame()
df['US_Change'] = us['Close'].pct_change() # 美股昨晚漲跌
df['TW_Vol'] = tw['Volume'].shift(1)       # 台股昨天量能 (注意要 shift 1，因為開盤時只知道昨天的量)
df['TW_Prev_Close'] = tw['Close'].shift(1) # 台股昨天收盤

# 關鍵：計算今天的「當沖報酬率」 (Intraday Return)
# 如果我在開盤買(Open)，收盤賣(Close)，我會賺多少？
df['Open'] = tw['Open']
df['Close'] = tw['Close']
df['Intraday_Ret'] = (df['Close'] - df['Open']) / df['Open']

# 3. 定義新目標 (Target)
# 我們不再猜「漲跌」，我們要猜「這根K棒是不是紅的？」
# 也就是：收盤價 > 開盤價
df['Target'] = np.where(df['Intraday_Ret'] > 0, 1, 0)

# 清除空值 (對齊日期)
df = df.dropna()

# 4. 準備考卷
X = df[['US_Change', 'TW_Vol']]
y = df['Target']

# 切分數據 (前 80% 訓練，後 20% 回測)
split = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# 5. 訓練 AI
print("AI 訓練中...")
model = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=42)
model.fit(X_train, y_train)

# 6. 策略回測 (Backtesting)
# 取得 AI 對未來的預測
predictions = model.predict(X_test)

# 計算策略績效
# 邏輯：如果 AI 預測 1 (會收紅)，我們就去賺那個 Intraday_Ret
# 如果 AI 預測 0 (會收黑)，我們就空手 (Return = 0)
strategy_returns = predictions * df['Intraday_Ret'].iloc[split:]

# 計算「買入持有」(Buy & Hold) 的績效當對照組
# 這裡用的是 Open-to-Close 的累積，比較公平
benchmark_returns = df['Intraday_Ret'].iloc[split:]

# 7. 畫出資金曲線 (Equity Curve)
plt.figure(figsize=(12, 6))
# cumsum() 是累積加總，讓我們看到資產變化
plt.plot(strategy_returns.cumsum(), label='AI Strategy (Day Trading)', color='red')
plt.plot(benchmark_returns.cumsum(), label='Buy & Hold (Intraday)', color='gray', alpha=0.5)

plt.title("AI Strategy vs Buy & Hold (Intraday Only)")
plt.legend()
plt.grid(True)
plt.show()

# 8. 報明牌：AI 覺得明天會怎樣？
# 我們拿「最後一天」的數據來預測「下一個交易日」
last_data = X.iloc[[-1]]
next_pred = model.predict(last_data)
print(f"--------------------------------")
print(f"數據截止日: {last_data.index.item().date()}")
print(f"昨晚美股漲跌: {last_data['US_Change'].item()*100:.2f}%")
print(f"--------------------------------")
if next_pred == 1:
    print("AI 建議: 【明天開盤買進】 (預測會收紅棒)")
else:
    print("AI 建議: 【明天觀望】 (預測會收黑棒/上影線)")
print(f"--------------------------------")