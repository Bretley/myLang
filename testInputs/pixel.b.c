#include<stdarg.h>
#include<stdlib.h>
#include<stdio.h>
typedef struct string {
    int length;
    char[] str;
} String;

String* createString(int length,char str) {
    String* ret;
    ret = malloc(sizeof(String));
    ret->length = length;
    ret->str = str;
    return ret;
}
typedef struct pixel {
    int r;
    int g;
    int b;
} Pixel;

Pixel* createPixel(int r,int g,int b) {
    Pixel* ret;
    ret = malloc(sizeof(Pixel));
    ret->r = r;
    ret->g = g;
    ret->b = b;
    return ret;
}

int clamp(int n) {
    if (n>255) {
        return 255;
    } else if (n<0) {
        return 0;
    } else {
        return n;
    }
}


int pixIntensity(Pixel* destructuredPixel) {
    int r;
    int g;
    int b;
    if (destructuredPixel == NULL) {exit(1);}
    r = destructuredPixel->r;
    g = destructuredPixel->g;
    b = destructuredPixel->b;
return (((r+g)+b)/3);
}


int main() {
    int g;
    Pixel* r;
    g = 5;
    r = createPixel(4,5,6);
    return 0;
}
