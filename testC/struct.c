#include<stdio.h>

typedef struct a {
    struct b {
        int x;
    } b;
    int x;
} Struct;

int main() {
    Struct a;
    a.b.x = 5;
    printf("%d\n",a.b.x);
    return 0;
}
