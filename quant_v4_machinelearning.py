import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. 獲取數據
ticker = 'BTC-USD'
data = yf.Ticker(ticker).history(start='2020-01-01', end='2025-01-10')
df = data[['Close', 'Open', 'High', 'Low', 'Volume']].copy()

print("正在進行特徵工程 (Feature Engineering)...")

# 2. 建構特徵 (Features - X)
# 這些是我們餵給 AI 吃的數據
# A. 收益率特徵
df['Returns'] = df['Close'].pct_change()

# B. 技術指標特徵 (不用太複雜，AI 自己會組合)
df['SMA_10'] = df['Close'].rolling(window=10).mean()
df['SMA_50'] = df['Close'].rolling(window=50).mean()
df['RSI_Proxy'] = (df['Close'] - df['Close'].rolling(14).min()) / (df['Close'].rolling(14).max() - df['Close'].rolling(14).min())
df['Volatility'] = df['Returns'].rolling(window=10).std()

# C. 乖離率 (價格距離均線多遠)
df['Dist_SMA10'] = df['Close'] / df['SMA_10'] - 1

# 3. 建構目標 (Target - y)
# 我們要預測：明天的收盤價 > 今天的收盤價 嗎？
# shift(-1) 是把明天的漲跌移到今天來當標籤
df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)

# 清洗數據 (去除 NaN)
df.dropna(inplace=True)

# 4. 切分訓練集與測試集 (Train / Test Split)
# 這一步最關鍵！我們用 2024-01-01 作為分界線
# 以前的數據用來讀書，以後的數據用來考試
split_date = '2024-01-01'

feature_cols = ['Returns', 'RSI_Proxy', 'Volatility', 'Dist_SMA10', 'Volume']

X = df[feature_cols]
y = df['Target']

X_train = X[X.index < split_date]
y_train = y[y.index < split_date]

X_test = X[X.index >= split_date]
y_test = y[y.index >= split_date]

print(f"訓練資料筆數: {len(X_train)} | 測試資料筆數: {len(X_test)}")

# 5. 召喚 AI 模型並訓練
print("正在訓練隨機森林 (Random Forest)...")
# n_estimators=100 代表種 100 棵樹
# min_samples_leaf=5 限制樹不能長太細，防止死背答案 (Overfitting)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=10, random_state=42)
model.fit(X_train, y_train)

# 6. 讓 AI 進行預測
print("AI 正在預測 2024 年以後的走勢...")
y_pred = model.predict(X_test)

# 評估準確率
acc = accuracy_score(y_test, y_pred)
print(f"預測準確率 (Accuracy): {acc:.2%}")

# 7. 回測績效 (Backtesting)
# 建立一個測試用的 DataFrame
test_df = df[df.index >= split_date].copy()
test_df['Predicted_Signal'] = y_pred

# 計算策略回報：如果 AI 預測漲 (1)，我們就持有；預測跌 (0)，我們就空手
# shift(1) 是因為我們是用今天的預測決定明天的持倉
test_df['Strategy_Returns'] = test_df['Returns'] * test_df['Predicted_Signal'].shift(1)

# 計算累積回報
test_df['Cum_Market'] = (1 + test_df['Returns']).cumprod()
test_df['Cum_Strategy'] = (1 + test_df['Strategy_Returns']).cumprod()

# 8. 畫圖決勝負
plt.figure(figsize=(12, 6))
plt.plot(test_df.index, test_df['Cum_Market'], label='Buy & Hold (BTC)', color='gray', alpha=0.5)
plt.plot(test_df.index, test_df['Cum_Strategy'], label='AI Random Forest', color='red', linewidth=2)

plt.title(f'AI Trading vs Bitcoin (Test Data: {split_date} ~ Now)')
plt.ylabel('Cumulative Return')
plt.legend()
plt.grid(True)
plt.show()

# 9. 特徵重要性 (Feature Importance) - AI 覺得什麼最重要？
importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\n----- AI 認為最重要的特徵 -----")
print(importances)