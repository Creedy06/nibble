; Sum an array using a pointer register (LDR = load through a pointer).
        LDI R0, data    ; pointer
        LDI R1, 0       ; running sum
        LDI R3, 1
        LD  R2, count   ; items left
loop:   LDR R2, [R0]    ; R2 = *pointer  (reuse R2 after reading the count)
        ADD R1, R2
        ADD R0, R3      ; pointer++
        LD  R2, count
        SUB R2, R3
        ST  R2, count
        JNZ loop
        OUT R1
        HLT
count:  .db 5
data:   .db 10, 20, 30, 40, 50
