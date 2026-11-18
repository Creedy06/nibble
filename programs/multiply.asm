; Multiply two 8-bit numbers with shift-and-add, the way hardware multipliers do.
; Result (low 8 bits) is printed and stored at 0xF0.
        LD  R0, a       ; multiplicand
        LD  R1, b       ; multiplier
        LDI R2, 0       ; product
loop:   LDI R3, 0
        CMP R1, R3
        JZ  done        ; multiplier used up
        MOV R3, R1
        SHR R3          ; carry = low bit of multiplier
        JC  addit
        JMP next
addit:  ADD R2, R0      ; bit was 1: add the shifted multiplicand
next:   SHL R0          ; multiplicand x 2
        SHR R1          ; move to the next multiplier bit
        JMP loop
done:   ST  R2, 0xF0
        OUT R2
        HLT
a:      .db 13
b:      .db 11
