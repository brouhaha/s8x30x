#!/usr/bin/python3
# Fast I/O decode for WD1001 hard disk controller
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

import re

class WD1001():
    iv_name = { 'sriv': { 0x0: 'rd_ram'},
                'sliv': { 0x1: 'drq_clk',
                          0x2: 'rd2',
                          0x3: 'int_clk',
                          0x4: 'rd_serdes',
                          0x5: 'rd5',
                          0x6: 'rd_host_port'},
                'driv': { 0x8: 'wr_ram'},
                'dliv': { 0x0: 'ecc_sel',
                          0x1: 'rwc',
                          0x2: 'precomp_en',
                          0x3: 'step',
                          0x4: 'waen',
                          0x5: 'direction',
                          0x6: 'write_gate',
                          0x7: 'flag',
                          0xa: 'ram_addr',
                          0xb: 'reset_index',
                          0xc: 'wr_serdes',
                          0xd: 'drive_head_sel',
                          0xe: 'wr_host_port',
                          0xf: 'mac_control'
                          }}

    # process Fast I/O selects, currently hard-coded for WD1000
    def fast_io_decode(self, ext, operands):
        rr = ext[0] & 0x7
        rr_needed = rr != 0x7

        wr = (ext[0] >> 4) & 0xf
        wr_needed = wr != 0xf

        # is s[lr]iv in operands?
        siv = re.search('s[lr]iv', operands)
        if siv:
            generic_name = siv.group()
            if rr in self.iv_name[generic_name]:
                operands = operands.replace(generic_name,
                                            self.iv_name[generic_name][rr])
                rr_needed = False

        # is d[lr]iv in operands?
        div = re.search('d[lr]iv', operands)
        if div:
            generic_name = div.group()
            if wr in self.iv_name[generic_name]:
                operands = operands.replace(generic_name,
                                            self.iv_name[generic_name][wr])
                wr_needed = False

        # is iv[lr] in operands?  (xmit destination)
        div = re.search('iv[lr]', operands)
        if div:
            generic_name_1 = div.group()
            generic_name_2 = { 'ivl' : 'dliv', 'ivr' : 'driv' } [generic_name_1]
            if wr in self.iv_name[generic_name_2]:
                operands = operands.replace(generic_name_1,
                                            self.iv_name[generic_name_2][wr])
                wr_needed = False

        if rr_needed or wr_needed:
            operands += ' //'
            if rr_needed:
                operands += ' rd=%d' % rr
            if wr_needed:
                operands += ' wr=%d' % wr

        return operands
