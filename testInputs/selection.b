ack = Int m n => {
    [ (m == 0) => n+1;
    [ (m > 0 ^ n == 0) => ack(m-1, 1);
    [ (m > 0 ^ n > 0) => ack(m-1, ack(m, n-1));
    [ non => 0;
}
comparator = Int a b =>
    [(a > b) => 1;
    [(a < b) => -1;
    [ non => 0;

fact = Int a =>
    [(a > 1) => a * fact(a-1);
    [ non => 1;

/*
fact2 = Int a => {
    Int sum;
    sum = 1;
    while (a>1) {
        sum = sum * a;
    }
    sum
}
*/

