! Vector Magnitude Calculator — Fortran Implementation
!
! Equivalent to vector_magnitude.c
! NOTE: Arrays are 1-based in Fortran (DO i = 1, n)
!       vs 0-based in C (for i = 0; i < n).
!       The IR comparison layer normalizes this difference.
!
! DEMO PROGRAM — for testing the RCI Code Equivalence Platform.

FUNCTION vector_magnitude(v, n) RESULT(mag)
    IMPLICIT NONE
    INTEGER, INTENT(IN) :: n
    DOUBLE PRECISION, INTENT(IN) :: v(n)
    DOUBLE PRECISION :: mag, sum_sq
    INTEGER :: i

    sum_sq = 0.0D0
    DO i = 1, n
        sum_sq = sum_sq + v(i) * v(i)
    END DO
    mag = DSQRT(sum_sq)
END FUNCTION vector_magnitude

PROGRAM VectorMagnitude
    IMPLICIT NONE
    INTEGER :: n, i
    INTEGER, PARAMETER :: MAX_DIM = 1024
    DOUBLE PRECISION :: v(MAX_DIM), mag
    DOUBLE PRECISION :: vector_magnitude

    READ(*,*) n
    IF (n <= 0 .OR. n > MAX_DIM) THEN
        WRITE(*,*) 'Error: n must be between 1 and', MAX_DIM
        STOP 1
    END IF

    DO i = 1, n
        READ(*,*) v(i)
    END DO

    mag = vector_magnitude(v, n)
    WRITE(*,'(F20.10)') mag

END PROGRAM VectorMagnitude
