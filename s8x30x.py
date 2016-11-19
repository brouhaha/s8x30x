#!/usr/bin/python3
# Signetics 8X300/8X305 definitions
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

from enum import Enum, IntEnum, unique

CpuType = Enum('CpuType', ['s8x300', 's8x305'])

class UnknownMnemonic(Exception):
    def __init__(self, mnem):
        super().__init__('unknown mnemonic "%s"' % mnem)

class NoMatchingForm(Exception):
    def __init__(self):
        super().__init__('no matching form')

class OperandOutOfRange(Exception):
    def __init__(self):
        super().__init__('operand out of range')

class BadInstruction(Exception):
    def __init__(self, instr):
        super().__init__('bad instruction %04x' % instr)



@unique
class Reg(IntEnum):
    aux  = 0o00     # aka r0
    r1   = 0o01
    r2   = 0o02
    r3   = 0o03
    r4   = 0o04
    r5   = 0o05
    r6   = 0o06
    ivl  = 0o07  # left bank register
    ovf  = 0o10
    r11  = 0o11
    r12  = 0o12  # 8x305 only, can't use for normal XMIT
    r13  = 0o13  # 8x305 only, can't use for normal XMIT
    r14  = 0o14  # 8x305 only
    r15  = 0o15  # 8x305 only
    r16  = 0o16  # 8x305 only
    ivr  = 0o17  # right bank register
    liv0 = 0o20
    liv1 = 0o21
    liv2 = 0o22
    liv3 = 0o23
    liv4 = 0o24
    liv5 = 0o25
    liv6 = 0o26
    liv7 = 0o27
    riv0 = 0o30
    riv1 = 0o31
    riv2 = 0o32
    riv3 = 0o33
    riv4 = 0o34
    riv5 = 0o35
    riv6 = 0o36
    riv7 = 0o37

    def is_iv(self):
        return self >= self.liv0

    def is_src_reg(self, cpu_type = CpuType.s8x300):
        if self >= self.liv0:
            return False
        if self < self.ivl or self is self.ovf or self is self.r11:
            return True;
        return cpu_type is CpuType.s8x305

    def is_dest_reg(self, cpu_type = CpuType.s8x300):
        if self >= self.liv0:
            return False
        if self is self.ovf:
            return False
        if self <= self.r11 or self is self.ivr:
            return True;
        return cpu_type is CpuType.s8x305

        

# operand type
# defined outside the I89 class and with very short name because
# it will be used a lot in the __inst_set class attribute of I89
OT = Enum('OT', ['sr',           # source register
                 'dr',           # destination register
                 'siv', 'div',   # IV 
                 'blen',         # length, 1-8 bits (8 encoded as zero)
                 'brot',         # rotation, 0-7 bits
                 'imm',          # immediate value, 5 or 8 bit
                 'jmp',          # jump target (absolute address)
                ])


def bit_count(v):
    return bin(v).count('1')


class BitField:
    def __init__(self, byte_count = 0):
        self.width = 0  # width of the field within the instruction
        self.mask = bytearray(byte_count)

    def __repr__(self):
        return 'BitField(width = %d, mask = %s' % (self.width, str(self.mask))

    def append(self, mask_byte):
        self.mask.append(mask_byte)
        self.width += bit_count(mask_byte)

    def pad_length(self, length):
        if len(self.mask) < length:
            self.mask += bytearray(length - len(self.mask))

    def insert(self, bits, value):
        assert isinstance(value, int)
        for i in range(len(bits)):
            for b in [1 << j for j in range(8)]:
                if self.mask[i] & b:
                    if value & 1:
                        bits[i] |= b
                    value >>= 1
        #assert value == 0  # XXX causes negative 8-bit immediates to fail
        

# An instruction form is a variant of an instruction that takes
# specific operand types.
class Form:
    @staticmethod
    def __byte_parse(bs):
        b = 0
        m = 0
        f = { }
        for i in range(8):
            c = bs[7-i]
            if c == '0':
                m |= (1 << i)
            elif c == '1':
                b |= (1 << i)
                m |= (1 << i)
            else:
                if c not in f:
                    f[c] = 0
                f[c] |= (1 << i)
        return b, m, f

    @staticmethod
    def __encoding_parse(encoding):
        ep_debug = False
        if ep_debug:
            print('encoding', encoding)
        encoding = encoding.replace(' ', '')
        bits = []
        mask = []
        fields = { }
        second_flag = False
        while len(encoding):
            assert len(encoding) >= 8
            byte = encoding[:8]
            encoding = encoding[8:]
            if ep_debug:
                print('byte', byte)
            b, m, f = Form.__byte_parse(byte)
            if ep_debug:
                print('b: ', b, 'm:', m, 'f:', f)
            bits.append(b)
            mask.append(m)
            for k in f:
                if k not in fields:
                    fields[k] = BitField(len(bits)-1)
                fields[k].append(f[k])
        if ep_debug:
            print('fields before:', fields)
        for k in fields:
            fields[k].pad_length(len(bits))
        if ep_debug:
            print('fields after:', fields)
        return bits, mask, fields

    def __init__(self, encoding, operands):
        self.operands = operands
        self.encoding = encoding
        self.bits, self.mask, self.fields = Form.__encoding_parse(encoding)

    def __len__(self):
        return len(self.bits)

    def insert_fields(self, fields):
        bits = bytearray(self.bits)
        assert set(self.fields.keys()) == set(fields.keys())
        for k, bitfield in self.fields.items():
            bitfield.insert(bits, fields[k])
        return bits
        


# An instruction has a single mnemonic, but possibly multiple
# forms.
class Inst:
    def __init__(self, mnem, *forms):
        self.mnem = mnem
        self.forms = forms


class S8X30x:
    # The source operand precedes the destination operand
    __inst_set = [
        Inst('nop',   Form('00000000 00000000', ())),
        Inst('xml',   Form('11001010 iiiiiiii', (OT.imm,))),
        Inst('xmr',   Form('11001011 iiiiiiii', (OT.imm,))),
        
        Inst('move',  Form('000sssss rrrddddd', (OT.sr,  OT.brot, OT.dr)),	# source -> dest
                      Form('000sssss lllddddd', (OT.sr,  OT.blen, OT.div)),
                      Form('000sssss lllddddd', (OT.siv, OT.blen, OT.dr)),
                      Form('000sssss lllddddd', (OT.siv, OT.blen, OT.div))),

        Inst('add',   Form('001sssss rrrddddd', (OT.sr,  OT.brot, OT.dr)),	# source + AUX -> dest, updates OVF
                      Form('001sssss lllddddd', (OT.sr,  OT.blen, OT.div)),
                      Form('001sssss lllddddd', (OT.siv, OT.blen, OT.dr)),
                      Form('001sssss lllddddd', (OT.siv, OT.blen, OT.div))),
                                              
        Inst('and',   Form('010sssss rrrddddd', (OT.sr,  OT.brot, OT.dr)),	# source & AUX -> dest
                      Form('010sssss lllddddd', (OT.sr,  OT.blen, OT.div)),
                      Form('010sssss lllddddd', (OT.siv, OT.blen, OT.dr)),
                      Form('010sssss lllddddd', (OT.siv, OT.blen, OT.div))),
                                              
        Inst('xor',   Form('011sssss rrrddddd', (OT.sr,  OT.brot, OT.dr)),	# source & AUX -> dest
                      Form('011sssss lllddddd', (OT.sr,  OT.blen, OT.div)),
                      Form('011sssss lllddddd', (OT.siv, OT.blen, OT.dr)),
                      Form('011sssss lllddddd', (OT.siv, OT.blen, OT.div))),
                                              
        Inst('xmit',  Form('100ddddd iiiiiiii', (OT.imm, OT.dr)),               # immediate -> dest
                      Form('100ddddd llliiiii', (OT.imm, OT.blen, OT.div))),
                                              
                                              
        Inst('nzt',   Form('101sssss iiiiiiii', (OT.sr, OT.imm)),               # jump if S is non-zero
                      Form('101sssss llliiiii', (OT.siv, OT.blen, OT.imm))),
                                              
        Inst('xec',   Form('110sssss iiiiiiii', (OT.sr, OT.imm)),               # execute intrustion at S+i
                      Form('110sssss llliiiii', (OT.siv, OT.blen, OT.imm))),
                                              
        Inst('jmp',   Form('111jjjjj jjjjjjjj', (OT.jmp,)))
    ]


    def __opcode_init(self):
        self.__inst_by_mnemonic = { }
        self.__inst_by_opcode = { }
        for inst in self.__inst_set:
            assert inst.mnem not in self.__inst_by_mnemonic
            self.__inst_by_mnemonic[inst.mnem] = inst
            form = inst.forms[0]  # assumes all forms of an inst have same opcode
            opcode = form.bits[0] >> 5
            if opcode not in self.__inst_by_opcode:
                self.__inst_by_opcode[opcode] = []
            self.__inst_by_opcode[opcode] += [inst]

    def _opcode_table_print(self):
        for mnem in sorted(self.__inst_by_mnemonic.keys()):
            inst = self.__inst_by_mnemonic[mnem]
            for form in inst.forms:
                print('%-04s:' % mnem, form.encoding, form.operands)


    @staticmethod
    def __extract_field(inst, fields, f):
        width = 0
        v = 0
        for i in range(min(len(inst), len(fields[f].mask))):
            for j in reversed(range(8)):
                if fields[f].mask[i] & (1 << j):
                    v = (v << 1) | ((inst[i] >> j) & 1)
                    width += 1
        if width == 8 and v > 127 and f == 'j':
            v += (65536 - 256)
        return v


    @staticmethod
    def encoding_match(d, form):
        for i in range(len(d)):
            if d[i] & form.mask[i] != form.bits[i] & form.mask[i]:
                return False
        return True


    def form_search(self, fw, pc, inst):
        opcode = fw[pc][:2]
        for form in inst.forms:
            if not self.encoding_match(opcode, form):
                continue
            fields = { }
            for f in form.fields:
                fields[f] = self.__extract_field(opcode, form.fields, f)
                # XXX need to check source, dest fields for correct types
            return form, fields
        return None, None


    def inst_search(self, fw, pc):
        opcode = fw[pc][0] >> 5
        for inst in self.__inst_by_opcode[opcode]:
            form, fields = self.form_search(fw, pc, inst)
            if form is not None:
                return inst, form, fields
        raise BadInstruction(opcode)

    @staticmethod
    def ihex(v):
        s = '%xh' % v
        if s[0].isalpha():
            s = '0' + s
        return s


    def disassemble_inst(self, fw, pc, symtab_by_value = {}, disassemble_operands = True, cpu_type = CpuType.s8x300):
        try:
            inst, form, fields = self.inst_search(fw, pc)
        except BadInstruction:
            return 1, 'db      ', '%s' % self.ihex(fw[pc]), {}

        s = '%-6s' % inst.mnem
        operands = []

        if disassemble_operands:
            ftemp = fields.copy()
            for operand in form.operands:
                if operand == OT.sr or operand == OT.siv:
                    value = Reg(ftemp['s']).name
                    del ftemp['s']
                elif operand == OT.dr or operand == OT.div:
                    value = Reg(ftemp['d']).name
                    del ftemp['d']
                elif operand == OT.brot:
                    v = ftemp['r']
                    del ftemp['r']
                    value = '(' + self.ihex(v) + ')'
                elif operand == OT.blen:
                    v = ftemp['l']
                    del ftemp['l']
                    if v == 0:
                        v = 8
                    value = self.ihex(v)
                elif operand == OT.imm:
                    value = self.ihex(ftemp['i'])
                    del ftemp['i']
                elif operand == OT.jmp:
                    target = ftemp['j']
                    del ftemp['j']
                    if target in symtab_by_value:
                        value = symtab_by_value[target]
                    else:
                        value = self.ihex(target)
                else:
                    raise NotImplementedError('operand type ' + operand)
                operands.append(value)
            if ftemp:
                raise NotImplementedError('leftover fields: ' + str(ftemp))

        return s, ','.join(operands), fields


    def __init__(self):
        self.__opcode_init()

if __name__ == '__main__':
    s8x30x = S8X30x()
    s8x30x._opcode_table_print()
