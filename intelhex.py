#!/usr/bin/python3
# Intel hex file reader
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

import io

class IntelHex:

    class BadChecksum(Exception):
        pass

    class UnknownRecordType(Exception):
        pass
    
    class Discontiguous(Exception):
        pass
    
    def get_bytes(self, count):
        s = self.f.read(2*count)
        if len(s) != 2*count:
            raise EOFError()
        return bytearray([int(s[2*i:2*i+2], 16) for i in range(count)])

    def get_ui8(self):
        return self.get_bytes(1)[0]
    
    def get_ui16(self):
        b = self.get_bytes(2)
        return (b[0] << 8) + b[1]
        

    def get_colon(self):
        while True:
            b = self.f.read(1)
            if len(b) == 0:
                raise EOFError()
            if b[0] == 0x3a:
                return
        


    def get_record(self):
        self.get_colon()
        self.rn += 1
        data_length = self.get_ui8()
        addr = self.get_ui16()
        rec_type = self.get_ui8()
        data = self.get_bytes(data_length)
        expected_checksum = (((data_length +
                               ((addr >> 8) & 0xff) +
                               (addr & 0xff) +
                               rec_type +
                               sum(data)) ^ 0xff) + 1) & 0xff
        checksum = self.get_ui8()
        if checksum != expected_checksum:
            raise IntelHex.BadChecksum('Bad checksum for record #%d' % self.rn)
        if rec_type == 0x00:  # data
            if self.load_addr is None:
                self.load_addr = addr
            if self.expected_addr is not None and self.expected_addr != addr:
                raise IntelHex.Discontiguous('Unexpected address for data record #%d' % self.rn)
            self.memory[self.load_addr:self.load_addr+data_length] = data
            self.expected_addr = addr + data_length
            self.load_addr += data_length
            self.limit = max(self.limit, self.load_addr)

        elif rec_type == 0x01:  # end of file
            raise EOFError()  # end of file
        elif rec_type == 0x04:
            return True
        else:
            raise IntelHex.UnknownRecordType('Unknown record type %02x for record #%d' % (rec_type, self.rn))
        return True


    def read(self, f):
        if isinstance(f, bytearray):
            self.f = io.BytesIO(f)
        else:
            self.f = f
        self.memory = bytearray(65536)
        self.rn = 0
        self.load_addr = 0
        self.expected_addr = None
        self.limit = 0

        try:
            while True:
                self.get_record()
        except EOFError as e:
            pass

        return self.memory[:self.limit]
