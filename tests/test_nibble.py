from pathlib import Path

import pytest

from nibble import CPU, AssemblyError, CPUError, assemble, disassemble

PROGRAMS = Path(__file__).parent.parent / "programs"


def run(src: str) -> CPU:
    return CPU.with_program(assemble(src)).run()


def test_ldi_and_out():
    assert run("LDI R0, 42\nOUT R0\nHLT").output == [42]


def test_add_sets_carry_and_wraps():
    cpu = run("LDI R0, 200\nLDI R1, 100\nADD R0, R1\nHLT")
    assert cpu.regs[0] == 44 and cpu.c and not cpu.z


def test_sub_borrow_and_zero():
    cpu = run("LDI R0, 5\nLDI R1, 5\nSUB R0, R1\nHLT")
    assert cpu.regs[0] == 0 and cpu.z and not cpu.c
    cpu = run("LDI R0, 3\nLDI R1, 5\nSUB R0, R1\nHLT")
    assert cpu.regs[0] == 254 and cpu.c and cpu.n


def test_logic_ops():
    cpu = run("LDI R0, 0b1100\nLDI R1, 0b1010\nMOV R2, R0\nAND R2, R1\nMOV R3, R0\nXOR R3, R1\nOR R0, R1\nHLT")
    assert cpu.regs[0] == 0b1110 and cpu.regs[2] == 0b1000 and cpu.regs[3] == 0b0110


def test_shifts():
    cpu = run("LDI R0, 0x81\nSHL R0\nHLT")
    assert cpu.regs[0] == 0x02 and cpu.c
    cpu = run("LDI R0, 0x03\nSHR R0\nHLT")
    assert cpu.regs[0] == 0x01 and cpu.c


def test_memory_and_pointers():
    cpu = run("LDI R0, 7\nST R0, 0xA0\nLD R1, 0xA0\nLDI R2, 0xB0\nSTR R1, [R2]\nLDR R3, [R2]\nHLT")
    assert cpu.mem[0xA0] == 7 and cpu.mem[0xB0] == 7 and cpu.regs[3] == 7


def test_conditional_jumps_countdown():
    src = """
        LDI R0, 3
        LDI R1, 1
    top: OUT R0
        SUB R0, R1
        JNZ top
        HLT
    """
    assert run(src).output == [3, 2, 1]


def test_fibonacci_program():
    cpu = run((PROGRAMS / "fibonacci.asm").read_text())
    assert cpu.output == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]


@pytest.mark.parametrize("a,b", [(13, 11), (0, 9), (15, 15), (1, 200)])
def test_multiply_program(a, b):
    src = (PROGRAMS / "multiply.asm").read_text()
    src = src.replace("a:      .db 13", f"a:      .db {a}").replace("b:      .db 11", f"b:      .db {b}")
    cpu = run(src)
    assert cpu.output == [(a * b) & 0xFF]
    assert cpu.mem[0xF0] == (a * b) & 0xFF


def test_sum_array_program():
    assert run((PROGRAMS / "sum_array.asm").read_text()).output == [150]


def test_labels_and_org():
    prog = assemble("JMP start\n.org 0x10\nstart: HLT")
    assert prog[1] == 0x10 and prog[0x10] == 0x00


def test_assembler_errors():
    with pytest.raises(AssemblyError, match="line 2"):
        assemble("LDI R0, 1\nFOO R1")
    with pytest.raises(AssemblyError):
        assemble("LDI R9, 1")
    with pytest.raises(AssemblyError):
        assemble("LDI R0, 300")
    with pytest.raises(AssemblyError):
        assemble("JMP nowhere")


def test_infinite_loop_guard():
    with pytest.raises(CPUError):
        CPU.with_program(assemble("x: JMP x")).run(max_cycles=1000)


def test_disassemble_roundtrip():
    src = "LDI R1, 5\nADD R1, R2\nSHR R3\nJZ 0x00\nLDR R0, [R1]\nOUT R1\nHLT"
    lines = disassemble(assemble(src))
    assert lines == ["00: LDI R1, 5", "02: ADD R1, R2", "03: SHR R3", "04: JZ 0x00",
                     "06: LDR R0, [R1]", "07: OUT R1", "08: HLT"]
