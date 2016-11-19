#!/usr/bin/python3
# Memory model
# Copyright 2016 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math

class LengthMismatch(Exception):
    pass

class Memory:
    def __init__(self, data):
        self.data = data
        l = [len(d) for d in self.data]
        if l[1:] != l[:-1]:
            raise LengthMismatch()
        self.size = l[0]

    def __len__(self):
        return self.size

    def __getitem__(self, address):
        return [self.data[i][address] for i in range(len(self.data))]


if __name__ == '__main__':
    filenames = ['u41_800000-036a.bin',  # MSB
                 'u51_800000-035a.bin',  # LSB
                 'u28_800000-037a.bin']  # fast select
    
    if False:
        memory = Memory([open(fn, 'rb').read() for fn in filenames])

        for a in range(len(memory)):
            w = memory[a]
            print('%04x:' % a, ' '.join(['%02x' % d for d in w]))

    else:
        from intelhex import IntelHex
        hex_filenames = [fn.replace('.bin', '.hex') for fn in filenames]
        print(hex_filenames)
        data = [IntelHex().read(open(fn, 'rb')) for fn in hex_filenames]
        print(data)
        hex_memory = Memory(data)

        for a in range(len(hex_memory)):
            w = hex_memory[a]
            print('%04x:' % a, ' '.join(['%02x' % d for d in w]))
        print("done")
        
