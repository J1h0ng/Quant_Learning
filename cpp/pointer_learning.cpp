#include <iostream>
using namespace std;

void swap(int *a, int *b)
{
    int temp = *a;
    *a = *b;
    *b = temp;
}

int main()
{
    int x = 10;
    int y = 20;

    cout << "Before swap: x = " << x << ", y = " << y << endl;
    cout << &x << "\n";
    cout << &y << "\n";
    swap(&x, &y);
    cout << "After swap: x = " << x << ", y = " << y << endl;
    cout << &x << "\n";
    cout << &y << "\n";

    return 0;
}