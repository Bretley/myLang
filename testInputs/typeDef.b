type Cartesian = {
    Int x y;
}

type Polar  = {
    Double r theta;
}

type Point = Polar | Cartesian;

main = non => {
    p = Point (3,5);
    3
}
