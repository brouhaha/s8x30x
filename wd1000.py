#!/usr/bin/python3
# Fast I/O decode for WD1000 hard disk controller
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

class WD1000():
    iv_name = { 'sriv': { 0: 'rd_ram'},
                'sliv': { 1: 'drq_clk',
                          2: 'rd2',
                          3: 'int_clk',
                          4: 'rd_serdes',
                          5: 'rd5',
                          6: 'rd_host_port'},
                'driv': { 0: 'wr_ram'},
                'dliv': { 1: 'drive_control',
                          2: 'ram_addr_low',
                          3: 'reset_index',
                          4: 'wr_serdes',
                          5: 'drive_head_sel',
                          6: 'wr_host_port',
                          7: 'mac_control'}}

    # process Fast I/O selects, currently hard-coded for WD1000
    def fast_io_decode(self, ext, operands):
        rr = ext[0] & 0x7
        rr_needed = rr != 0x07

        wr = (ext[0] >> 4) & 0x7
        wr_needed = wr != 0x0

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
