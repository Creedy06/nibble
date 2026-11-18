"""The Nibble CPU: fetch, decode, execute."""

from __future__ import annotations

from dataclasses import dataclass, field

from .isa import TWO_BYTE, decode

NAMES = ["HLT", "LDI", "LD", "ST", "MOV", "ADD", "SUB", "AND", "OR", "XOR",
         "SH", "CMP", "J", "LDR", "STR", "OUT"]
JUMPS = ["JMP", "JZ", "JNZ", "JC"]


class CPUError(RuntimeError):
    pass


@dataclass
class CPU:
    mem: bytearray = field(default_factory=lambda: bytearray(256))
    regs: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    pc: int = 0
    z: bool = False   # zero
    c: bool = False   # carry / borrow
    n: bool = False   # negative (bit 7 set)
    halted: bool = False
    cycles: int = 0
    output: list[int] = field(default_factory=list)

    @classmethod
    def with_program(cls, program: bytes) -> "CPU":
        cpu = cls()
        cpu.mem[:len(program)] = program
        return cpu

    def _flags(self, result: int, carry: bool | None = None) -> int:
        value = result & 0xFF
        self.z = value == 0
        self.n = bool(value & 0x80)
        if carry is not None:
            self.c = carry
        return value

    def _fetch(self) -> int:
        byte = self.mem[self.pc]
        self.pc = (self.pc + 1) & 0xFF
        return byte

    def step(self) -> None:
        if self.halted:
            return
        op, rd, rs = decode(self._fetch())
        arg = self._fetch() if op in TWO_BYTE else None
        r = self.regs
        self.cycles += 1

        if op == 0x0:
            self.halted = True
        elif op == 0x1:
            r[rd] = arg
        elif op == 0x2:
            r[rd] = self.mem[arg]
        elif op == 0x3:
            self.mem[arg] = r[rd]
        elif op == 0x4:
            r[rd] = r[rs]
        elif op == 0x5:
            total = r[rd] + r[rs]
            r[rd] = self._flags(total, carry=total > 0xFF)
        elif op == 0x6:
            r[rd] = self._flags(r[rd] - r[rs], carry=r[rs] > r[rd])
        elif op == 0x7:
            r[rd] = self._flags(r[rd] & r[rs])
        elif op == 0x8:
            r[rd] = self._flags(r[rd] | r[rs])
        elif op == 0x9:
            r[rd] = self._flags(r[rd] ^ r[rs])
        elif op == 0xA:
            if rs == 0:
                r[rd] = self._flags(r[rd] << 1, carry=bool(r[rd] & 0x80))
            else:
                r[rd] = self._flags(r[rd] >> 1, carry=bool(r[rd] & 0x01))
        elif op == 0xB:
            self._flags(r[rd] - r[rs], carry=r[rs] > r[rd])
        elif op == 0xC:
            take = (rd == 0) or (rd == 1 and self.z) or (rd == 2 and not self.z) or (rd == 3 and self.c)
            if take:
                self.pc = arg
        elif op == 0xD:
            r[rd] = self.mem[r[rs]]
        elif op == 0xE:
            self.mem[r[rs]] = r[rd]
        elif op == 0xF:
            self.output.append(r[rd])

    def run(self, max_cycles: int = 100_000) -> "CPU":
        while not self.halted:
            if self.cycles >= max_cycles:
                raise CPUError(f"no HLT after {max_cycles} cycles (infinite loop?)")
            self.step()
        return self

    def state(self) -> str:
        flags = "".join(f if v else "-" for f, v in (("Z", self.z), ("C", self.c), ("N", self.n)))
        regs = " ".join(f"R{i}={v:3d}" for i, v in enumerate(self.regs))
        return f"PC={self.pc:02X} {regs} [{flags}]"


def disassemble(program: bytes) -> list[str]:
    lines = []
    pc = 0
    while pc < len(program):
        op, rd, rs = decode(program[pc])
        start = pc
        pc += 1
        arg = None
        if op in TWO_BYTE and pc < len(program):
            arg = program[pc]
            pc += 1
        name = NAMES[op]
        if op == 0x0:
            text = "HLT"
        elif op in (0x1,):
            text = f"LDI R{rd}, {arg}"
        elif op in (0x2, 0x3):
            text = f"{name} R{rd}, 0x{arg:02X}"
        elif op == 0xA:
            text = f"{'SHL' if rs == 0 else 'SHR'} R{rd}"
        elif op == 0xC:
            text = f"{JUMPS[rd]} 0x{arg:02X}"
        elif op in (0xD, 0xE):
            text = f"{name} R{rd}, [R{rs}]"
        elif op == 0xF:
            text = f"OUT R{rd}"
        else:
            text = f"{name} R{rd}, R{rs}"
        lines.append(f"{start:02X}: {text}")
    return lines
