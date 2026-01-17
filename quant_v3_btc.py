import yfinance as yf
import pandas as pd
import numpy as np
import itertools

# 1. 設定參數
ticker = 'BTC-USD'
start_date = '2023-01-01'
end_date = '2026-01-01'
fee_rate = 0.001  # 0.1% 手續費 (單邊)

print(f"下載數據中... 標的: {ticker}")
data = yf.Ticker(ticker).history(start=start_date, end=end_date)
df_base = data[['Close']].copy()

# 2. 定義參數網格
# 為了示範，我們縮小範圍，專注看手續費的影響
short_windows = [5, 10, 20]
long_windows = [20, 40, 60]
rsi_thresholds = [70, 85, 100]

results = []

print(f"開始回測 (含手續費 {fee_rate * 100}%)...")

for short_w, long_w, rsi_limit in itertools.product(short_windows, long_windows, rsi_thresholds):
    if short_w >= long_w: continue

    df = df_base.copy()

    # A. 指標計算
    df['SMA_S'] = df['Close'].rolling(window=short_w).mean()
    df['SMA_L'] = df['Close'].rolling(window=long_w).mean()

    # RSI 計算
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(com=13, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # B. 策略訊號
    condition = (df['SMA_S'] > df['SMA_L']) & (df['RSI'] < rsi_limit)
    df['Signal'] = np.where(condition, 1.0, 0.0)

    # === C. 關鍵修改：計算交易次數與扣除手續費 ===

    # 1. 找出交易點：今天訊號跟昨天不一樣，就是有動作 (0->1 買, 1->0 賣)
    # .diff().abs() 會讓買賣點都變成 1，不動的時候是 0
    df['Trade_Action'] = df['Signal'].diff().abs()

    # 2. 計算原始策略回報 (不含手續費)
    # shift(1) 是因為我們用昨天的訊號賺今天的錢
    df['Raw_Return'] = df['Close'].pct_change() * df['Signal'].shift(1)

    # 3. 計算淨回報 (Net Return) = 原始回報 - (交易動作 * 手續費)
    # 注意：這裡將手續費直接從當日報酬率中扣除
    df['Net_Return'] = df['Raw_Return'] - (df['Trade_Action'] * fee_rate)

    # D. 統計結果
    # 總交易次數
    total_trades = df['Trade_Action'].sum()

    # 累積淨值
    total_net_return = (1 + df['Net_Return']).cumprod().iloc[-1] - 1
    total_raw_return = (1 + df['Raw_Return']).cumprod().iloc[-1] - 1

    # 記錄
    results.append({
        'Params': f"{short_w}/{long_w}/{rsi_limit}",
        'Trades': int(total_trades),
        'Gross_Ret': total_raw_return,  # 扣費前
        'Net_Ret': total_net_return,  # 扣費後
        'Fee_Impact': total_raw_return - total_net_return  # 手續費吃掉了多少利潤
    })

# 3. 分析結果
results_df = pd.DataFrame(results)

# 按照「淨回報」排序
top_results = results_df.sort_values(by='Net_Ret', ascending=False).head(5)

print("\n----- 真實戰場結果 (Net Returns) TOP 5 -----")
print(top_results.to_string(formatters={
    'Gross_Ret': '{:.2%}'.format,
    'Net_Ret': '{:.2%}'.format,
    'Fee_Impact': '{:.2%}'.format
}))

# 找出一個「高頻交易」的失敗案例 (交易次數最多，但被手續費吃光)
sad_story = results_df.sort_values(by='Trades', ascending=False).iloc[0]
print("\n----- 警世故事：過度交易的代價 -----")
print(f"參數組合: {sad_story['Params']}")
print(f"交易次數: {sad_story['Trades']} 次")
print(f"扣費前賺: {sad_story['Gross_Ret']:.2%}")
print(f"扣費後賺: {sad_story['Net_Ret']:.2%}")
print(f"結論: 手續費吃掉了 {sad_story['Fee_Impact']:.2%} 的利潤！")