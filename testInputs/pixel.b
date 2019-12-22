type String = {
    Int length;
    Char[] str;
}
type Pixel = {
    Int r g b;
}

clamp = Int n =>
    [ (n > 255) => 255;
    [ (n < 0) => 0;
    [ non => n;

pixIntensity = Pixel {r g b} => (r + g + b) / 3

main = non => {
    g = 5;
    r = Pixel(4,5,6);
    0
}
