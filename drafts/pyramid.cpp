#include <iostream>

int main()
{
    int layers;
    std::cout << "How many layers does your pyramid have? ";
    std::cin >> layers;

    for (int i = 1; i <= layers; i++)
    {
        for (int j = 1; j <= layers - i; j++)
        {
            std::cout << (" ");
        }

        for (int k = 1; k <= 2 * i - 1; k++)
        {
            std::cout << ("*");
        }

        std::cout << ("\n");
    }
}