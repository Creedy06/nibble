"""The Nibble instruction set.

Every instruction starts with one byte:

    7  6  5  4   3  2   1  0
    [ opcode  ] [ rd ] [ rs ]

Instructions marked (2) take a second byte: an 8-bit immediate or address.

    op  mnemonic        meaning
    0   HLT             stop the CPU
    1   LDI rd, imm (2) rd <- imm
    2   LD  rd, addr(2) rd <- mem[addr]
    3   ST  rd, addr(2) mem[addr] <- rd
    4   MOV rd, rs      rd <- rs
    5   ADD rd, rs      rd <- rd + rs          (sets Z, C, N)
    6   SUB rd, rs      rd <- rd - rs          (C = borrow)
    7   AND rd, rs      rd <- rd & rs
    8   OR  rd, rs      rd <- rd | rs
    9   XOR rd, rs      rd <- rd ^ rs
    A   SHL rd / SHR rd shift left (rs=0) or right (rs=1); C = bit shifted out
    B   CMP rd, rs      flags from rd - rs, result discarded
    C   JMP/JZ/JNZ/JC   (2) jump to addr; rd field picks the condition
    D   LDR rd, [rs]    rd <- mem[rs]           (pointer load)
    E   STR rd, [rs]    mem[rs] <- rd           (pointer store)
    F   OUT rd          append rd to the output port
"""

REGISTERS = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}

OPCODES = {
    "HLT": 0x0, "LDI": 0x1, "LD": 0x2, "ST": 0x3, "MOV": 0x4,
    "ADD": 0x5, "SUB": 0x6, "AND": 0x7, "OR": 0x8, "XOR": 0x9,
    "SHL": 0xA, "SHR": 0xA, "CMP": 0xB,
    "JMP": 0xC, "JZ": 0xC, "JNZ": 0xC, "JC": 0xC,
    "LDR": 0xD, "STR": 0xE, "OUT": 0xF,
}

JUMP_CONDITIONS = {"JMP": 0, "JZ": 1, "JNZ": 2, "JC": 3}

TWO_BYTE = {0x1, 0x2, 0x3, 0xC}


def encode(op: int, rd: int = 0, rs: int = 0) -> int:
    return (op << 4) | (rd << 2) | rs


def decode(byte: int) -> tuple[int, int, int]:
    return byte >> 4, (byte >> 2) & 0b11, byte & 0b11
