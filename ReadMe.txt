CS415---Compilers----Rutgers University----Project-1

These are register allocators, coded in python from scratch. I've implemented 3 allocators: A bottom-up allocator ("b"), a top down allocator ("s") [both explained in the textbook "Engineering a Compiler"] and a top down allocator ("t") that uses the concept of live-ranges and max-live.

There are two files: alloc.py and ILOCInstruction.py
  
To run the bottom-up allocator with 5 registers on linux on a file named test.i, use the command:

[Only a subset of ILOC instructions are supported. They are: load, loadI, add, sub, mult, output, store, lshift, rshift]

python alloc.py 5 b test.i
