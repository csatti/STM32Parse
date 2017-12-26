#!/usr/bin/env python
# -*- coding: cp1250 -*-

# MIT license
#
# Copyright (C) 2017 by Attila Kovács
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#
# This script converts a STM32CubeMX report to a KiPart compatible CSV file. 

import re
import sys
import csv
import collections

# Returns text if it is not a number or a string with leading zeroes if it is
def ifill(text):
    return text.zfill(5) if text.isdigit() else text

# Replaces numbers with zero filled versions inside names for more natural sorting
def name_keys(item):
    pin = item[1]
    s = pin['alt']
    if s == '': s = pin['name']
    v = ''.join([ ifill(c) for c in re.split('(\d+)', s)])    
    return v

# Default values
inputname = 'input.csv'
outputname = 'output.csv'

# Get arguments
anum = len(sys.argv)
if anum > 1: inputname = sys.argv[1]
if anum > 2: outputname = sys.argv[2]

# Partname is uppercase version of the input file name
partname = inputname.upper().replace('.CSV','')

# Parse pin file
pins = {}
# Pattern for peripheries
peri = re.compile('([A-Z0-9]+)[\w-]+')
i = 1
with open(inputname, 'rb') as csvfile:
    pinreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(pinreader, None)
    for row in pinreader:
        newpin = collections.defaultdict(str)
        pin, name, pintype, signal, label = row
        newpin['pin'] = pin
        newpin['name'] = name
        newpin['unit'] = ''
        newpin['type'] = 'tristate'
        newpin['side'] = 'left'
        newpin['alt'] = signal
        if 'Power' in pintype:
            newpin['unit'] = 'PWR'
            newpin['type'] = 'power_in'
            if 'VSS' in name: newpin['side'] = 'top'
            elif 'VDD' in name: newpin['side'] = 'bottom'
        if ('Boot' in pintype) or ('Reset' in pintype):
            newpin['unit'] = 'SYS'
            newpin['type'] = 'input'  
        if 'Input' in pintype:
            newpin['unit'] = 'GPIO'
            newpin['type'] = 'input'
            newpin['name'] = name + '/' + label
        if 'Output' in pintype:
            newpin['unit'] = 'GPIO'
            newpin['type'] = 'output'
            newpin['name'] = name + '/' + label
        if 'I/O' in pintype:
            if signal == '':
                newpin['unit'] = 'unused'
                newpin['type'] = 'noconnect'
            else:
                m = peri.match(signal)
                if m.group(1) != None:
                    newpin['unit'] = m.group(1)
                    newpin['type'] = 'bidirectional'
                    newpin['name'] = name + '/' + signal
        pins[i] = newpin
        i += 1

# Generate the output file
print 'Generating '+ outputname + ' file.'

with open(outputname, 'wb') as csvfile:
    partwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    partwriter.writerow([partname])
    partwriter.writerow([''])
    partwriter.writerow(['Pin', 'Unit', 'Type', 'Name', 'Side'])
    for k, v in sorted(pins.items(), key=name_keys):
        partwriter.writerow([v['pin'], v['unit'], v['type'], v['name'], v['side']])
        
