fact = Int a => {
    Int ret;
    ret = 1;
    while (a > 0) {
        ret = ret * a;
        a = a - 1;
        while (ret > 5 ) {}
    }
    a
}
