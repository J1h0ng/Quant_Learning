#include <iostream>

int main()
{
    int layers;
    std::cout << "Enter layers for Pascal's Triangle: ";
    std::cin >> layers;

    // 外層迴圈：控制第幾層 (從 0 開始數比較好算組合公式)
    for (int i = 0; i < layers; i++)
    {

        // 1. 印空白 (為了排成金字塔形狀)
        for (int j = 1; j < layers - i; j++)
        {
            std::cout << " "; // 這裡只印一個空白
        }

        // 2. 印數字
        int val = 1; // 每一層的第一個數字永遠是 1
        for (int k = 0; k <= i; k++)
        {
            std::cout << val << " "; // 印出數字，後面加一個空白隔開

            // 【核心魔法】計算下一個數字
            // 下一個數字 = 當前數字 * (該層行號 - 目前位置) / (目前位置 + 1)
            val = val * (i - k) / (k + 1);
        }

        std::cout << "\n";
    }
    return 0;
}