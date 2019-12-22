#include<stdarg.h>
#include<stdlib.h>
#include<stdio.h>
typedef struct cartesian {
    int x;
    int y;
} Cartesian;

typedef struct polar {
    float r;
    float theta;
} Polar;

typedef enum pointcase {
    CartesianPoint,PolarPoint
} PointCase;

typedef struct {
    PointCase type;
    union {
        Cartesian cartesian;
        Polar polar;
    };
} Point;

Point * createPoint(PointCase type, ... ) {
    Point * ret = malloc(sizeof(Point));
    va_list args;
    va_start(args, type);
    if (type == PolarPoint) {
        ret->polar.r = (va_arg(args, double));
        ret->polar.theta = (va_arg(args, double));
    } else if (type == CartesianPoint ) {
        ret->cartesian.x = (va_arg(args, int));
        ret->cartesian.y = (va_arg(args, int));
    }
    va_end(args);
    return ret;
}


int main() {
    Point* point = createPoint(PolarPoint,3.5,4.5);
    //printf("(%d,%f)\n", point->cartesian.x, point->cartesian.y);
    printf("(%f,%f)\n", point->polar.r, point->polar.theta);
    free(point);
}

