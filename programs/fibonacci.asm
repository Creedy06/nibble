; Print Fibonacci numbers until they overflow 8 bits (> 255).
        LDI R0, 0       ; a
        LDI R1, 1       ; b
loop:   OUT R0
        MOV R2, R0
        ADD R2, R1      ; R2 = a + b, sets carry on overflow
        JC  done
        MOV R0, R1
        MOV R1, R2
        JMP loop
done:   OUT R1          ; last value that fit
        HLT
