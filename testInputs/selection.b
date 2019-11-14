ack = Int m n =>
    [(m > 0) => ack(m-1, ack(m))
    [ non => 1

comparator = Int a b =>
    [(a > b) => 1
    [(a < b) => -1
    [ non => 0

fact = Int a =>
    [(a > 1) => a * fact(a-1)
    [ non => 1

