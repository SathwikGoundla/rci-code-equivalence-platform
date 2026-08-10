/**
 * Quadratic Equation Solver — C Implementation
 *
 * Solves ax^2 + bx + c = 0
 * Handles real roots, complex roots, and linear degenerate case.
 *
 * DEMO PROGRAM — for testing the RCI Code Equivalence Platform.
 */

#include <stdio.h>
#include <math.h>

typedef struct {
    double real1;
    double imag1;
    double real2;
    double imag2;
    int root_type; /* 0=two real, 1=repeated, 2=complex, 3=linear, 4=degenerate */
} QuadraticResult;

QuadraticResult solve_quadratic(double a, double b, double c) {
    QuadraticResult result = {0.0, 0.0, 0.0, 0.0, 0};

    if (a == 0.0) {
        if (b == 0.0) {
            result.root_type = 4; /* degenerate */
            return result;
        }
        result.real1 = -c / b;
        result.root_type = 3; /* linear */
        return result;
    }

    double discriminant = b * b - 4.0 * a * c;

    if (discriminant > 0.0) {
        result.real1 = (-b + sqrt(discriminant)) / (2.0 * a);
        result.real2 = (-b - sqrt(discriminant)) / (2.0 * a);
        result.root_type = 0;
    } else if (discriminant == 0.0) {
        result.real1 = -b / (2.0 * a);
        result.real2 = result.real1;
        result.root_type = 1;
    } else {
        result.real1 = -b / (2.0 * a);
        result.imag1 = sqrt(-discriminant) / (2.0 * a);
        result.real2 = result.real1;
        result.imag2 = -result.imag1;
        result.root_type = 2;
    }

    return result;
}

int main(void) {
    double a, b, c;
    scanf("%lf %lf %lf", &a, &b, &c);

    QuadraticResult r = solve_quadratic(a, b, c);

    printf("%d\n", r.root_type);
    printf("%.10f %.10f\n", r.real1, r.imag1);
    printf("%.10f %.10f\n", r.real2, r.imag2);

    return 0;
}
