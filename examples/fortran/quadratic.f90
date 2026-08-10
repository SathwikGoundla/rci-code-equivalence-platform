! Quadratic Equation Solver — Fortran Implementation
!
! Solves a*x^2 + b*x + c = 0
! Equivalent to quadratic.c
!
! NOTE: Intentional precision difference for gap detection demo:
!   C uses 'double' (FLOAT64), this Fortran version uses REAL (FLOAT32)
!   for the intermediate discriminant calculation.
!   This is a deliberate GAP to demonstrate the Precision Mismatch detector.
!
! DEMO PROGRAM — for testing the RCI Code Equivalence Platform.

PROGRAM QuadraticSolver
    IMPLICIT NONE
    DOUBLE PRECISION :: a, b, c
    DOUBLE PRECISION :: discriminant
    DOUBLE PRECISION :: real1, imag1, real2, imag2
    INTEGER :: root_type

    READ(*,*) a, b, c

    ! NOTE: Using REAL (not DOUBLE PRECISION) for discriminant here is intentional
    !       to demonstrate the precision mismatch gap detection.
    REAL :: disc_single  ! GAP: PRECISION_MISMATCH — C uses double for discriminant

    disc_single = REAL(b * b - 4.0D0 * a * c)
    discriminant = DBLE(disc_single)

    imag1 = 0.0D0
    imag2 = 0.0D0
    root_type = 0

    IF (a == 0.0D0) THEN
        IF (b == 0.0D0) THEN
            root_type = 4
            real1 = 0.0D0
            real2 = 0.0D0
        ELSE
            root_type = 3
            real1 = -c / b
            real2 = 0.0D0
        END IF
    ELSE IF (discriminant > 0.0D0) THEN
        real1 = (-b + DSQRT(discriminant)) / (2.0D0 * a)
        real2 = (-b - DSQRT(discriminant)) / (2.0D0 * a)
        root_type = 0
    ELSE IF (discriminant == 0.0D0) THEN
        real1 = -b / (2.0D0 * a)
        real2 = real1
        root_type = 1
    ELSE
        real1 = -b / (2.0D0 * a)
        imag1 = DSQRT(-discriminant) / (2.0D0 * a)
        real2 = real1
        imag2 = -imag1
        root_type = 2
    END IF

    WRITE(*,'(I1)') root_type
    WRITE(*,'(F20.10,1X,F20.10)') real1, imag1
    WRITE(*,'(F20.10,1X,F20.10)') real2, imag2

END PROGRAM QuadraticSolver
