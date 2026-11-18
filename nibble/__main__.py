"""python -m nibble program.asm [--trace] [--dis]"""

import argparse
import sys

from .assembler import AssemblyError, assemble
from .cpu import CPU, disassemble


def main() -> None:
    ap = argparse.ArgumentParser(prog="nibble", description="Assemble and run a Nibble 8-bit program")
    ap.add_argument("file")
    ap.add_argument("--trace", action="store_true", help="print CPU state after every instruction")
    ap.add_argument("--dis", action="store_true", help="print the disassembly")
    args = ap.parse_args()

    try:
        program = assemble(open(args.file).read())
    except AssemblyError as e:
        sys.exit(f"{args.file}: {e}")

    print(f"Assembled {len(program)} bytes")
    if args.dis:
        print("\n".join(disassemble(program)))
        print()

    cpu = CPU.with_program(program)
    while not cpu.halted:
        cpu.step()
        if args.trace:
            print(cpu.state())
        if cpu.cycles > 100_000:
            sys.exit("stopped: no HLT after 100,000 instructions")

    print(f"Halted after {cpu.cycles} instructions")
    print("Output:", cpu.output)
    print("Final: ", cpu.state())


if __name__ == "__main__":
    main()
