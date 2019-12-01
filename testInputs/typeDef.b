type Cartesian = { 
    Int x y;
}

type Polar = {
    Float r theta;
}

type Point = Cartesian | Polar;

main = non => {
    x = Point ( 5 , 4);
    0 
}
