/**
 * Vector Magnitude Calculator — C Implementation
 * 
 * Computes the Euclidean norm of an N-dimensional vector.
 * Input: N followed by N double values.
 *
 * DEMO PROGRAM — for testing the RCI Code Equivalence Platform.
 */

#include <stdio.h>
#include <math.h>

#define MAX_DIM 1024

double vector_magnitude(const double *v, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += v[i] * v[i];
    }
    return sqrt(sum);
}

int main(void) {
    int n;
    double v[MAX_DIM];

    scanf("%d", &n);
    if (n <= 0 || n > MAX_DIM) {
        fprintf(stderr, "Error: n must be between 1 and %d\n", MAX_DIM);
        return 1;
    }

    for (int i = 0; i < n; i++) {
        scanf("%lf", &v[i]);
    }

    double mag = vector_magnitude(v, n);
    printf("%.10f\n", mag);

    return 0;
}
