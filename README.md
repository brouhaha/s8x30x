# s8x30x - Disassembler for Signetics 8X300/8X305

Copyright 2016 Eric Smith <spacewar@gmail.com>

s8x30x development is hosted at the
[s8x30x Github repository](https://github.com/brouhaha/s8x30x/).

## Introduction

Western Digital's earliest hard disk controllers were board-level
products based on the Signetics 8X300 or 8X305 bipolar processors.

s8x30x provides a disassembler for the 8X300/8X305.

s8x30x was developed to support reverse-engineering and modification of
the firmware of the Western Digital WD100x family of disk controllers,
and consequently some features that would be of use for general purpose
8X300/8X305 support are not present.

## Syntax

The output of the disassember is in a custom syntax that does not match
the Signetics MCCAP assembler, or any other existing assembler.  It is
intended that an assembler be added to the s8x30x package in the future.

Bit positions are designated with bit 0 as the least significant bit and
bit 7 as the most significant bit, which is the opposite of the notation
Signetics uses, but matches almost everything else using microprocessor
and peripheral chips, including the I/O on the WD100x disk controllers.

The syntax for source and destination registers and I/O ports incorporates
the length and rotation fields.

* When an entire register is used without rotation or length, it is represented
  as just the register name, e.g., `r5`.

* When an entire register is used with rotation, it is represented as the
  register name with a right rotation operator, e.g., `r5>>>3`.

* When an entire I/O port is used as an operand, it is by default represented
  as `sliv` or `sriv` for left or right I/O ports as a source, and
  `dliv` or `driv` for left or right I/O ports used as a destination.  The
  fast I/O select decoding, if used, may substitute the I/O port names.

* When a single bit of an I/O port is used as an operand, it is represented
  as the I/O port name subscripted by a bracketed bit number,
  e.g., `sliv[7]` for the most significant bit of the source left I/O register.

* When a range of bits of an I/O port are used as an operand, they are
  represented as the I/O port name subscripted by a bracketed bit range,
  witht he leftmost and rightmost bit numbers separated by a colon,
  e.g., `sriv[3:0]` for the least significant four bits of the source right
  I/O register.

## Disassembler limitations

As of this writing, the output of the disassembler has not been
reassembled with any assembler, so it's possible and even likely that
there are bugs resulting in inacurate disassembly.

The support for Fast I/O Select ROMs is currently hard-coded to the
configuration used by the WD1000 controller. The WD1001 will require
some changes, but actually the Fast I/O select support should be
generalized.

## Disassembler usage

The dis8x30x disassembler can accept either raw binary input files
(default), or
[Intel hex format](https://en.wikipedia.org/wiki/Intel_HEX)
input files if the "`--hex`" option is given
on the command line.  If other file formats are needed, the srec_cat
utility of [srecord](http://srecord.sourceforge.net/) is recommended.

At least two input files are required.  The first and second input
files are the most significant and least significant byte of the
8X30x instruction. Any further input files provide fast select data,
used by hardware other than the 8X30x processor.

The "`-l`" option causes the disassembler output to be generated in
a format similar to an assembler listing file, with the address and
object code for each disassembled instruction to the left of the
disassembled instruction.

## Disassembler examples

The examples of command lines given below do not show the path to the
executable, nor, for operating systems that require it, the explicit
specification of the Python interpreter.


* `dis8x30x msb.bin lsb.bin fast.bin >wd1000.dis`

  Disassembles from three raw binary files, and
  generates output in the form of assembly source

* `dis8x30x -l --hex msb.hex lsb.hex fast.hex >wd1000.dis`

  Disassembles from three Intel hex files, and
  generates output in the form of a listing.

## License information

This program is free software: you can redistribute it and/or modify
it under the terms of version 3 of the GNU General Public License
as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
