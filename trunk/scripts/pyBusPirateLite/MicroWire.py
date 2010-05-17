#!/usr/bin/env python
# encoding: utf-8

import sys,time

from optparse import OptionParser
from pyBusPirateLite.RAW_WIRE import *



def main():
    # First of all parse the command line
    
    parser = OptionParser()
    
    parser.add_option("-s", "--size", dest="size", help="size of the memory chip.", type="int")
    parser.add_option("-o", "--org", dest="org", help="specify the memory organization mode (8 or 16).", type="int")
    parser.add_option("-a", "--addr", dest="addr", help="set the starting offset of the read or write procedure.", type="int", default=0)
    parser.add_option("-c", "--count", dest="count", help="the number of data elements to read or write.", type="int", default=0)
    parser.add_option("-f", "--file", dest="file", help="the input or output file.", metavar="FILE")
    parser.add_option("-r", "--read", dest="action", help="read the memory chip.", default="read")
    parser.add_option("-w", "--write", dest="action", help="write to the memory chip.")
    parser.add_option("-d", "--device", dest="device", help="serial interface where bus pirate is in.[/dev/bus_pirate]", default="/dev/bus_pirate")
    parser.add_option("-v", "--verbose", dest="verbose", help="don't be quiet.", action="store_true")
    parser.add_option("-m", "--more", dest="more", help="only for testing: read more data elements", type="int", default=0)
    
    (options,args) = parser.parse_args()
    
    if (not options.size) or (not options.org) or (not options.file):
        parser.print_help()
        exit()      
    
    # Create an instance of the RAW_WIRE class as we are using the BitBang/RAW_WIRE mode
    rw = RAW_WIRE( '/dev/bus_pirate', 115200 )
    
    if not rw.BBmode():
        print "Can't enter into BitBang mode."
        exit()

    # We have succesfully activated the BitBang Mode, so we continue with
    # the raw-wire mode.
    if not rw.enter_rawwire():
        print "Can't enable the raw-wire mode."
        exit()
        
    # Now we have raw-wire mode enabled, so first configure peripherals
    # (Power, PullUps, AUX, CS)
    
    if not rw.raw_cfg_pins( PinCfg.POWER ):
        print "Error enabling the internal voltage regulators."
        
    # Configure the raw-wire mode
    
    if not rw.cfg_raw_wire( (RAW_WIRECfg.BIT_ORDER & RAW_WIRE_BIT_ORDER_TYPE.MSB) | (RAW_WIRECfg.WIRES & RAW_WIRE_WIRES_TYPE.THREE) | (RAW_WIRECfg.OUT_TYPE & RAW_WIRE_OUT_TYPE._3V3) ):
        print "Error configuring the raw-wire mode."
    
    # Set raw-wire speed
    
    if not rw.set_speed( RAW_WIRESpeed._5KHZ ):
        print "Error setting raw-wire speed."

    # Open the file for reading or writting
    
    if options.action == "read":
        f = file(options.file, "wb")
    else:
        f = file(options.file, "rb")
        
    # How many elements to read or write?
    
    N = options.size / options.org
    
    N += options.more
    
    # Opcodes for microwire memory devices
    #
    #                Op             Address                 Data
    #Instruction SB Code        x8         x16          x8          x16     Comments
    #   READ     1   10     A8 – A0     A7 – A0                             Reads data stored in memory, at specified address
    #   EWEN     1   00    11XXXXXXX    11XXXXXX                            Write enable must precede all programming modes

    if options.action == "read":
        # Enable the Chip select signal
        rw.CS_High()
    
        # Send the start bit and the opcode
        rw.data_high()
        rw.clk_tick()
    
        # the opcode, ad data is high we don't send it again
        rw.clk_tick()
    
        rw.data_low()
        rw.clk_tick()
    
        # now the address to read
        
        # if we are reading bytes we will need an extra bit (yes I know, it depends of the memory size but first I will test with 4K ones)
        if options.org == 8:
            if options.addr and 0x100:
                rw.data_high()
            else:
                rw.data_low()
                
            rw.clk_tick()
            
        rw.bulk_trans(1,"\x00")
    
        # ignore the  dummy 0 on the data out
        
        rw.clk_tick()
        
        # and read the items
        
        if options.verbose:
            print "Reading %d bits in %d elements of %d bits" % (options.size, N, options.org)
        
        if options.org == 8:
            for i in range(0,N):
                byte = rw.read_byte()
                f.write(byte)
                
                if options.verbose:
                    print "%02X" % (ord(byte),) ,
                    
        else:
            for i in range(0,N):
                byte = rw.read_byte()
                f.write(byte)
                
                if options.verbose:
                    print "%02X" % (ord(byte),) ,
                
                byte = rw.read_byte()
                f.write(byte)
                
                if options.verbose:
                    print "%02X" % (ord(byte),) ,
        
        f.close()
        
        print "Done."
    

    
    # Reset the bus pirate
    rw.resetBP();


if __name__ == '__main__':
    
    main()
    
