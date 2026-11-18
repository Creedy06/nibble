# Nibble

An 8-bit CPU I designed: an instruction set, an emulator that runs it, and a
two-pass assembler that turns assembly into machine code.

It covers the core of a computer organization course: registers, flags, memory,
the fetch-decode-execute cycle, branching, and pointers. Instead of reading
about a CPU, you write programs for one and watch every instruction run.

```
$ python -m nibble programs/fibonacci.asm
Assembled 15 bytes
Halted after 92 instructions
Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
Final:  PC=0F R0=144 R1=233 R2=121 R3=  0 [-C-]
```

## The machine

| Part | Spec |
| --- | --- |
| Registers | 4 general purpose, 8-bit (`R0`–`R3`) |
| Memory | 256 bytes, shared by code and data (von Neumann) |
| Flags | `Z` zero, `C` carry/borrow, `N` negative |
| Instructions | 16 opcodes, 1 or 2 bytes each |
| I/O | `OUT` writes to an output port |

Each instruction's first byte is `[opcode:4][rd:2][rs:2]`, which is where the name
*Nibble* comes from: the opcode is one nibble (4 bits). Loads, stores, immediates,
and jumps add a second byte for the value or address.

| Op | Instruction | Does |
| --- | --- | --- |
| 0 | `HLT` | stop |
| 1 | `LDI rd, imm` | load an 8-bit constant |
| 2 / 3 | `LD rd, addr` / `ST rd, addr` | load / store memory |
| 4 | `MOV rd, rs` | copy a register |
| 5 / 6 | `ADD` / `SUB rd, rs` | arithmetic, sets Z C N |
| 7 / 8 / 9 | `AND` / `OR` / `XOR rd, rs` | bitwise logic |
| A | `SHL rd` / `SHR rd` | shift, the bit shifted out goes to C |
| B | `CMP rd, rs` | subtract for flags only |
| C | `JMP` / `JZ` / `JNZ` / `JC addr` | jumps (the rd bits pick the condition) |
| D / E | `LDR rd, [rs]` / `STR rd, [rs]` | load / store through a pointer |
| F | `OUT rd` | write to the output port |

## Assembler

Two passes: the first records each label's address, the second emits bytes. That
way a jump can point at a label further down the file.

```asm
; comments start with a semicolon
        LDI R0, 3
        LDI R1, 1
top:    OUT R0          ; labels end in a colon
        SUB R0, R1
        JNZ top         ; loop until R0 hits zero
        HLT
data:   .db 10, 20, 30  ; raw bytes
        .org 0x80       ; place what follows at address 0x80
```

Errors give a line number (`line 2: unknown instruction 'FOO'`), and numbers that
don't fit in 8 bits are caught.

## Example programs

- `fibonacci.asm` prints Fibonacci numbers and uses the **carry flag** to stop
  when the next one would overflow 8 bits
- `multiply.asm` is **shift-and-add multiplication**, the algorithm hardware
  multipliers use, since the ISA has no multiply instruction
- `sum_array.asm` walks an array with a **pointer register**

## Run it

Requires Python 3.10+. No third-party packages.

```
python -m nibble programs/multiply.asm --dis     # show the machine code
python -m nibble programs/sum_array.asm --trace  # registers after every step
python -m pytest                                 # 17 tests
```

## Code layout

- `nibble/isa.py`: opcode table and bit-level encode/decode
- `nibble/assembler.py`: two-pass assembler with labels, `.db`, `.org`
- `nibble/cpu.py`: fetch/decode/execute loop, flags, disassembler
- `tests/`: every instruction, flag edge cases (overflow, borrow), and the example programs

## Ideas for next steps

- `CALL`/`RET` with a stack pointer
- Memory-mapped I/O (a fake LED bank or 7-segment display)
- Rebuild the CPU in Verilog and run it on an FPGA
