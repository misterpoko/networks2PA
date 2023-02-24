"""
Where solution code to project should be written.  No other files should
be modified.
"""

import socket
import io
import time
import typing
import struct
import util
import util.logging
import array
from threading import Timer



def send(sock: socket.socket, data: bytes):
    """
    Implementation of the sending logic for sending data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.
        data -- A bytes object, containing the data to send over the network.
    """

    # Naive implementation where we chunk the data to be sent into
    # packets as large as the network will allow, and then send them
    # over the network, pausing half a second between sends to let the
    # network "rest" :)
    logger = util.logging.get_logger("project-sender")
    chunk_size = util.MAX_PACKET-8
    pause = .01
    sock.settimeout(.01)
    offsets = range(0, len(data), util.MAX_PACKET-8)
    j = 0
    for chunk in [data[i:i + chunk_size] for i in offsets]:
        checsum = check(chunk)
        theChunk = make(j, checsum, chunk)
        j = j + 1
        sent = False
        while not sent:
            #sock.send(theChunk)
            print("packet sent ", (j-1), " - ", checsum)
            try:
                returndata = sock.recv(util.MAX_PACKET)
                ackNum, checksum, nothing = extract(returndata)
                if ackNum == (j - 1):
                    sent = True
                    print("packet ack recieved ", ackNum)
            except socket.timeout:
                sock.send(theChunk)
                sock.send(theChunk)
        logger.info("Pausing for %f seconds", round(pause, 2))
        time.sleep(pause)


def recv(sock: socket.socket, dest: io.BufferedIOBase) -> int:
    """
    Implementation of the receiving logic for receiving data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.

    Return:
        The number of bytes written to the destination.
    """
    logger = util.logging.get_logger("project-receiver")
    # Naive solution, where we continually read data off the socket
    # until we don't receive any more data, and then return.
    num_bytes = 0
    sameNumber = 0
    currentNum = 0
    while True:
        data = sock.recv(util.MAX_PACKET)
        theNum, checksum, theData = extract(data)
        if (check(theData)) == checksum and currentNum == theNum:
            print("packet recieved ", theNum, " - checksum - ", checksum)
            sock.send(make(theNum,0))
            currentNum += 1
            sameNumber = 0
            print("packet recieved ", theNum, " - acknum - ", currentNum)
            logger.info("Received %d bytes", len(data))
            dest.write(theData)
            num_bytes += len(theData)
            dest.flush()
        else:
            if theNum + 1 == currentNum:
                sameNumber += 1
            if sameNumber >= 2:
                sock.send(make(theNum,0))
            print(theNum, " <- packet being sent ", currentNum, " <- packet wanted")
        if not data:
            break
    return num_bytes
    
def make(seq_num, checksum, data = b''):
    seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
    seq_bytes2 = checksum.to_bytes(4, byteorder = 'little', signed = True)
    return seq_bytes + seq_bytes2 + data

def extract(packet):
    seq_num = int.from_bytes(packet[0:4], byteorder = 'little', signed = True)
    theCheckSum = int.from_bytes(packet[4:8], byteorder = 'little', signed = True)
    return seq_num, theCheckSum, packet[8:]
    
def check(packet):
    if len(packet) % 2 != 0:
        packet += b'\0'
    res = sum(array.array("H", packet))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16
    return (~res) & 0xffff

    
