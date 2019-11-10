int fact(int a) {
    if (a>1) {
        return (a*fact((a-1)));
    } else {
        return 1;
    }
}

int main() {
    printf("%d", fact(5));
}
