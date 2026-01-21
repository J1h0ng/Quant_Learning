#include <iostream>
using namespace std;

int main()
{
    int numbers[] = {100, 200, 300, 400, 500};
    int *ptr = numbers;

    int count = 0;
    cout << "Scan the array with pointer." << endl;

    while (count < 5)
    {
        cout << *ptr << ("\n");
        ptr++;
        count++;
    }

    return 0;
}