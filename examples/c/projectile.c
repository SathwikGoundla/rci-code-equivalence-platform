/**
 * Projectile Motion Calculator — C Implementation
 * 
 * Computes the range, maximum height, and time of flight for a projectile
 * given initial velocity and launch angle.
 *
 * Inputs (stdin):
 *   v0     - initial velocity in m/s (double)
 *   angle  - launch angle in degrees (double)
 *
 * Outputs (stdout):
 *   Range (m)
 *   Max Height (m)
 *   Time of Flight (s)
 *
 * DEMO PROGRAM — for testing the RCI Code Equivalence Platform.
 * Not actual DRDO/RCI source code.
 */

#include <stdio.h>
#include <math.h>

#define PI 3.14159265358979323846
#define G  9.80665

double deg_to_rad(double deg) {
    return deg * PI / 180.0;
}

double compute_range(double v0, double angle_deg) {
    double angle_rad = deg_to_rad(angle_deg);
    return (v0 * v0 * sin(2.0 * angle_rad)) / G;
}

double compute_max_height(double v0, double angle_deg) {
    double angle_rad = deg_to_rad(angle_deg);
    double vy0 = v0 * sin(angle_rad);
    return (vy0 * vy0) / (2.0 * G);
}

double compute_flight_time(double v0, double angle_deg) {
    double angle_rad = deg_to_rad(angle_deg);
    return (2.0 * v0 * sin(angle_rad)) / G;
}

int main(void) {
    double v0, angle;

    scanf("%lf %lf", &v0, &angle);

    if (v0 <= 0.0) {
        fprintf(stderr, "Error: initial velocity must be positive\n");
        return 1;
    }
    if (angle <= 0.0 || angle >= 90.0) {
        fprintf(stderr, "Error: angle must be between 0 and 90 degrees (exclusive)\n");
        return 1;
    }

    double range      = compute_range(v0, angle);
    double max_height = compute_max_height(v0, angle);
    double flight_time = compute_flight_time(v0, angle);

    printf("%.6f\n", range);
    printf("%.6f\n", max_height);
    printf("%.6f\n", flight_time);

    return 0;
}
