"""Two-pass assembler: Nibble assembly text -> bytes.

Syntax:
    ; comment
    loop:              label (on its own line or before an instruction)
    LDI R0, 10         decimal, 0x hex, or 0b binary immediates
    JNZ loop           labels work anywhere an address goes
    .db 1, 2, 3        raw data bytes
    .org 0x80          continue assembling at this address
"""

from __future__ import annotations

from .isa import JUMP_CONDITIONS, OPCODES, REGISTERS, TWO_BYTE, encode


class AssemblyError(ValueError):
    def __init__(self, line_no: int, msg: str):
        super().__init__(f"line {line_no}: {msg}")
        self.line_no = line_no


def _clean(source: str):
    for no, raw in enumerate(source.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        while ":" in line:
            label, line = line.split(":", 1)
            yield no, ("label", label.strip()), None
            line = line.strip()
        if line:
            parts = line.replace(",", " ").split()
            yield no, ("stmt", parts[0].upper()), parts[1:]


def _number(tok: str, labels: dict[str, int], line_no: int) -> int:
    if tok in labels:
        return labels[tok]
    try:
        val = int(tok, 0)
    except ValueError:
        raise AssemblyError(line_no, f"unknown label or number {tok!r}") from None
    if not -128 <= val <= 255:
        raise AssemblyError(line_no, f"{tok} does not fit in 8 bits")
    return val & 0xFF


def _reg(tok: str, line_no: int) -> int:
    reg = REGISTERS.get(tok.upper().strip("[]"))
    if reg is None:
        raise AssemblyError(line_no, f"expected a register R0-R3, got {tok!r}")
    return reg


def _size(mnemonic: str, args: list[str]) -> int:
    if mnemonic == ".db":
        return len(args)
    return 2 if OPCODES[mnemonic] in TWO_BYTE else 1


def assemble(source: str) -> bytes:
    lines = list(_clean(source))

    # Pass 1: find every label's address.
    labels: dict[str, int] = {}
    pc = 0
    for no, (kind, word), args in lines:
        if kind == "label":
            if word in labels:
                raise AssemblyError(no, f"label {word!r} defined twice")
            labels[word] = pc
        elif word == ".ORG":
            pc = int(args[0], 0)
        elif word == ".DB":
            pc += len(args)
        elif word in OPCODES:
            pc += _size(word, args)
        else:
            raise AssemblyError(no, f"unknown instruction {word!r}")

    # Pass 2: emit bytes.
    mem = bytearray(256)
    end = 0
    pc = 0
    for no, (kind, word), args in lines:
        if kind == "label":
            continue
        if word == ".ORG":
            pc = int(args[0], 0)
            continue
        if word == ".DB":
            out = [_number(a, labels, no) for a in args]
        else:
            out = _encode(word, args, labels, no)
        if pc + len(out) > 256:
            raise AssemblyError(no, "program does not fit in 256 bytes")
        mem[pc:pc + len(out)] = bytes(out)
        pc += len(out)
        end = max(end, pc)
    return bytes(mem[:end])


def _encode(m: str, args: list[str], labels: dict[str, int], no: int) -> list[int]:
    op = OPCODES[m]

    def need(n):
        if len(args) != n:
            raise AssemblyError(no, f"{m} takes {n} operand(s), got {len(args)}")

    if m == "HLT":
        need(0)
        return [encode(op)]
    if m in ("LDI", "LD", "ST"):
        need(2)
        return [encode(op, _reg(args[0], no)), _number(args[1], labels, no)]
    if m in ("MOV", "ADD", "SUB", "AND", "OR", "XOR", "CMP", "LDR", "STR"):
        need(2)
        return [encode(op, _reg(args[0], no), _reg(args[1], no))]
    if m in ("SHL", "SHR"):
        need(1)
        return [encode(op, _reg(args[0], no), 0 if m == "SHL" else 1)]
    if m in JUMP_CONDITIONS:
        need(1)
        return [encode(op, JUMP_CONDITIONS[m]), _number(args[0], labels, no)]
    if m == "OUT":
        need(1)
        return [encode(op, _reg(args[0], no))]
    raise AssemblyError(no, f"cannot encode {m}")
