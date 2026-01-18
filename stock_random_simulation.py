import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

initial_capital = 100000
capital = initial_capital
position = 0
history = [100]
print(f"初始資金: {initial_capital}")

for j in range(365):
    delta = float(np.random.uniform(-0.03, 0.03))
    new_price = history[-1] * (1 + delta)
    history.append(new_price)

df = pd.DataFrame(history, columns=['Price'])
df['MA5'] = df['Price'].rolling(window=5).mean()
df['MA20'] = df['Price'].rolling(window=20).mean()

plt.figure(figsize=(14, 7))
plt.plot(df['Price'], label='Price', color='gray', alpha=0.5)
plt.plot(df['MA5'], label='MA5 (Short)', color='blue', linewidth=1.5)
plt.plot(df['MA20'], label='MA20 (Long)', color='orange', linewidth=1.5)

for i in range(20, len(df)):
    current_price = df['Price'][i]

    if df["MA5"][i - 1] <= df["MA20"][i - 1] and df["MA5"][i] >= df["MA20"][i]:
        plt.scatter(i, current_price, marker='^', color='red', s=100, zorder=5)

        if position == 0:
            shares_to_buy = int(capital / current_price)
            cost = shares_to_buy * current_price
            capital -= cost
            position = shares_to_buy
            print(f"Day {i}: 🔥 買入 {shares_to_buy} 股 @ {current_price:.2f}")

    elif df["MA5"][i - 1] >= df["MA20"][i - 1] and df["MA5"][i] <= df["MA20"][i]:
        plt.scatter(i, current_price, marker='v', color='green', s=100, zorder=5)

        if position > 0:
            revenue = position * current_price
            capital += revenue
            position = 0
            print(f"Day {i}: 💀 賣出獲利了結 @ {current_price:.2f}")

if position > 0:
    capital += position * df['Price'].iloc[-1]

total_return = (capital - initial_capital) / initial_capital * 100
color_result = 'red' if total_return > 0 else 'green'  # 台灣慣例：紅賺綠賠

# transform=plt.gca().transAxes 代表使用「相對座標」 (0,0是左下, 1,1是右上)
# (0.02, 0.95) 代表左上角位置
info_text = (
    f"Initial Capital: ${initial_capital}\n"
    f"Final Asset:     ${capital:.2f}\n"
    f"Total Return:    {total_return:.2f}%"
)

plt.text(0.02, 0.95, info_text,
         transform=plt.gca().transAxes,  # 鎖定在視窗座標，不隨數據移動
         fontsize=14,
         verticalalignment='top',
         color=color_result,  # 賺錢顯紅，賠錢顯綠
         fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))  # 加個白底框框才看得清楚

plt.title("MA Strategy Backtest Result")
plt.xlabel("Days")
plt.ylabel("Price")
plt.grid(True)
plt.legend()
plt.show()