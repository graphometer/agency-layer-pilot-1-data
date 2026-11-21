#include <span>

int total(std::span<const int> xs) {
    int s = 0;
    for (int x : xs) s += x;
    return s;
}

int main() {
    int xs[] = {1, 2, 3};
    return total(xs) == 6 ? 0 : 1;
}
