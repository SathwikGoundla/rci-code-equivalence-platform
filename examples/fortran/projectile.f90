! Projectile Motion Calculator — Fortran Implementation
!
! Equivalent to projectile.c
! Computes range, maximum height, and time of flight.
!
! Inputs (stdin):
!   v0     - initial velocity in m/s (DOUBLE PRECISION)
!   angle  - launch angle in degrees (DOUBLE PRECISION)
!
! Outputs (stdout):
!   Range (m)
!   Max Height (m)
!   Time of Flight (s)
!
! DEMO PROGRAM — for testing the RCI Code Equivalence Platform.
! Not actual DRDO/RCI source code.

MODULE PhysicsConstants
    IMPLICIT NONE
    DOUBLE PRECISION, PARAMETER :: PI = 3.14159265358979323846D0
    DOUBLE PRECISION, PARAMETER :: G  = 9.80665D0
END MODULE PhysicsConstants

FUNCTION deg_to_rad(deg) RESULT(rad)
    USE PhysicsConstants
    IMPLICIT NONE
    DOUBLE PRECISION, INTENT(IN) :: deg
    DOUBLE PRECISION :: rad
    rad = deg * PI / 180.0D0
END FUNCTION deg_to_rad

FUNCTION compute_range(v0, angle_deg) RESULT(range_val)
    USE PhysicsConstants
    IMPLICIT NONE
    DOUBLE PRECISION, INTENT(IN) :: v0, angle_deg
    DOUBLE PRECISION :: range_val, angle_rad
    DOUBLE PRECISION :: deg_to_rad
    angle_rad = deg_to_rad(angle_deg)
    range_val = (v0 * v0 * SIN(2.0D0 * angle_rad)) / G
END FUNCTION compute_range

FUNCTION compute_max_height(v0, angle_deg) RESULT(height)
    USE PhysicsConstants
    IMPLICIT NONE
    DOUBLE PRECISION, INTENT(IN) :: v0, angle_deg
    DOUBLE PRECISION :: height, angle_rad, vy0
    DOUBLE PRECISION :: deg_to_rad
    angle_rad = deg_to_rad(angle_deg)
    vy0 = v0 * SIN(angle_rad)
    height = (vy0 * vy0) / (2.0D0 * G)
END FUNCTION compute_max_height

FUNCTION compute_flight_time(v0, angle_deg) RESULT(t_flight)
    USE PhysicsConstants
    IMPLICIT NONE
    DOUBLE PRECISION, INTENT(IN) :: v0, angle_deg
    DOUBLE PRECISION :: t_flight, angle_rad
    DOUBLE PRECISION :: deg_to_rad
    angle_rad = deg_to_rad(angle_deg)
    t_flight = (2.0D0 * v0 * SIN(angle_rad)) / G
END FUNCTION compute_flight_time

PROGRAM ProjectileMotion
    USE PhysicsConstants
    IMPLICIT NONE
    DOUBLE PRECISION :: v0, angle, range_val, max_height, flight_time
    DOUBLE PRECISION :: compute_range, compute_max_height, compute_flight_time

    READ(*,*) v0, angle

    IF (v0 <= 0.0D0) THEN
        WRITE(*,'(A)') 'Error: initial velocity must be positive'
        STOP 1
    END IF
    IF (angle <= 0.0D0 .OR. angle >= 90.0D0) THEN
        WRITE(*,'(A)') 'Error: angle must be between 0 and 90 degrees (exclusive)'
        STOP 1
    END IF

    range_val   = compute_range(v0, angle)
    max_height  = compute_max_height(v0, angle)
    flight_time = compute_flight_time(v0, angle)

    WRITE(*,'(F20.6)') range_val
    WRITE(*,'(F20.6)') max_height
    WRITE(*,'(F20.6)') flight_time

END PROGRAM ProjectileMotion
