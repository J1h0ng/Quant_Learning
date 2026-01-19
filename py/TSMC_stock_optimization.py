import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# 1. 獲取數據 (Data Acquisition)
print("正在下載台積電 (2330.TW) 歷史數據...")
# 下載 2014 年至今的數據
df = yf.download('2330.TW', start='2014-01-01', end='2024-01-01')

# 只留收盤價，並確保沒有空值
df = df[['Close']].copy()
df.dropna(inplace=True)

# 2. 設定參數網格 (Parameter Grid)
# 我們要測試哪些均線組合？
short_mas = [5, 10, 20, 60]  # 短線候選人
long_mas = [20, 60, 120, 240]  # 長線候選人 (分別代表月線、季線、半年線、年線)

# 建立一個矩陣來存結果
results = pd.DataFrame(index=short_mas, columns=long_mas)

print(f"開始暴力運算 {len(short_mas) * len(long_mas)} 種策略組合...")

# 3. 網格搜索 (Grid Search)
for short_window in short_mas:
    for long_window in long_mas:

        if short_window >= long_window:
            # 短線比長線還長，這不合邏輯，直接跳過 (填 NaN)
            results.loc[short_window, long_window] = np.nan
            continue

        # --- 快速回測核心 (Vectorized Backtest) ---
        # 這裡不用 for 迴圈跑每一天，直接整排計算，速度極快

        # 計算兩條均線
        # 注意：yfinance 新版下載的欄位可能是 MultiIndex，我們用 .squeeze() 確保它是 Series
        price = df['Close'].squeeze()
        ma_short = price.rolling(window=short_window).mean()
        ma_long = price.rolling(window=long_window).mean()

        # 產生訊號 (1 是持有，0 是空手)
        # 當 短 > 長，信號為 1；否則為 0
        signal = np.where(ma_short > ma_long, 1, 0)

        # shift(1) 很重要！因為今天的訊號是收盤才確定的，我們只能「明天」開盤執行
        # 所以我們的持倉狀況要往後移一天
        position = pd.Series(signal, index=price.index).shift(1)

        # 計算每日報酬率 (股價變化百分比)
        daily_returns = price.pct_change()

        # 策略報酬率 = 持倉狀態 * 每日報酬
        # 如果 position 是 1，我就賺到了漲跌幅；如果是 0，我就沒賺沒賠
        strategy_returns = position * daily_returns

        # 計算累積報酬 (複利計算)
        # (1+r1)*(1+r2)*... - 1
        total_return = (1 + strategy_returns).cumprod().iloc[-1] - 1

        # 存入結果矩陣 (轉成百分比)
        results.loc[short_window, long_window] = total_return * 100

print("運算完成！")

# 4. 畫出熱力圖 (Heatmap)
plt.figure(figsize=(10, 8))

# 轉換型別為浮點數，不然畫圖會報錯
results = results.astype(float)

sns.heatmap(results,
            annot=True,  # 顯示數字
            fmt=".1f",  # 小數點一位
            cmap="RdYlGn",  # 紅黃綠配色 (綠色代表賺錢，紅色代表賠錢)
            center=0,  # 0% 設為中間色
            cbar_kws={'label': 'Total Return (%)'})

plt.title('TSMC (2330.TW) MA Crossover Strategy Performance (10 Years)')
plt.xlabel('Long MA Window')
plt.ylabel('Short MA Window')
plt.show()

# 5. 找出最強組合
# stack() 把矩陣拉成一條長列，idxmax() 找出數值最大的索引
best_params = results.stack().idxmax()
max_return = results.stack().max()

print(f"--------------------------------------------------")
print(f"🏆 過去十年台積電最強均線組合: 短線 {best_params[0]} 日 vs 長線 {best_params[1]} 日")
print(f"💰 十年總報酬率: {max_return:.2f}%")
print(f"--------------------------------------------------")