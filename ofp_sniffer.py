#!/usr/bin/env python

"""
    This code is the AmLight OpenFlow Sniffer

    Current version: 0.4

    Author: Jeronimo Bezerra <jab@amlight.net>
"""
import datetime
import sys
import libs.cli
from libs.gen.packet import Packet
from libs.printing import PrintingOptions
from libs.sanitizer import Sanitizer
from apps.oess_fvd import OessFvdTracer


class RunSniffer(object):
    """

    """
    def __init__(self):
        self.printing_options = PrintingOptions()
        self.sanitizer = Sanitizer()
        self.oft = None
        self.cap = None
        self.position = None
        self.load_apps = []
        self.ctr = 1
        self.load_config()

    def load_config(self):
        """

        """
        # Get CLI params and call the pcapy loop
        self.cap, self.position, self.load_apps, sanitizer = libs.cli.get_params(sys.argv)
        self.sanitizer.process_filters(sanitizer)

        # Start Apps
        if 'oess_fvd' in self.load_apps:
            self.oft = OessFvdTracer()

    def run(self):
        """
            This is how it starts: cap.loop continuously capture packets w/ pcapy
            print_options and sanitizer are global variables
            Exits:
                0 - Normal, reached end of file
                1 - Normal, user requested with CRTL + C
                2 - Error
                3 - Interface or file not found
        """
        exit_code = 0
        self.cap.loop(-1, self.process_packet)
        try:
            pass
            # self.cap.loop(-1, self.process_packet)
        except KeyboardInterrupt:
            exit_code = 1
        except Exception as exception:
            print('Error: %s ' % exception)
            exit_code = 2
        finally:
            print('Exiting...')
            sys.exit(exit_code)

    def process_packet(self, header, packet):
        """
            Every packet captured by cap.loop is then processed here.
            If packets are bigger than 62 Bytes, we process them. If it is 0, means there are
                no more packets. If it is something in between, it is a fragment,
                we ignore for now.
            Args:
                header: header of the captured packet
                packet: packet captured from file or interface
        """
        if len(packet) >= 62 and self.position_defined():

            pkt = Packet(packet, self.ctr)
            pkt.process_packet_header(header)

            if pkt.is_openflow_packet:
                result = pkt.process_openflow_messages()

                if result is 1:
                    # Adding support to apps
                    # If no apps are selected, just print
                    if isinstance(self.oft, OessFvdTracer):
                        self.oft.process_packet(pkt)
                    else:
                        pkt.print_packet()
            del pkt
        elif len(packet) is 0:
            sys.exit(0)
        self.ctr += 1

    def position_defined(self):
        """
            In case user wants to see a specific packet inside a
                specific pcap file, provide file name with the position
                -r file.pcap:position
            Returns:
                True if ctr is good
                False: if ctr is not good
        """
        if self.position > 0:
            return True if self.ctr == self.position else False
        else:
            return True


if __name__ == "__main__":
    sniffer = RunSniffer()
    sniffer.run()
