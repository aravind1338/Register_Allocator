from ILOCInstruction import ILOCInstruction
import string
import sys

theClass = None

num_registers = int(sys.argv[1])

allocator = sys.argv[2]

theClass = ILOCInstruction()

file_name = sys.argv[3]

file_name = open(file_name, "r")

ILOCInstruction.parseFile(theClass, num_registers, allocator, file_name)