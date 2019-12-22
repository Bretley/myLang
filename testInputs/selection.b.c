#include<stdarg.h>
#include<stdlib.h>
#include<stdio.h>

int ack(int m, int n) {
    
        if (m==0) {
        return (n+1);
    } else if ((m>0) && (n==0)) {
        return ack((m-1),1);
    } else if ((m>0) && (n>0)) {
        return ack((m-1),ack(m,(n-1)));
    } else {
        return 0;
    }
}


int comparator(int a, int b) {
        if (a>b) {
        return 1;
    } else if (a<b) {
        return -1;
    } else {
        return 0;
    }
}


int fact(int a) {
        if (a>1) {
        return (a*fact((a-1)));
    } else {
        return 1;
    }
}
