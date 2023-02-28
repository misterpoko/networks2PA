"""
Where solution code to project should be written.  No other files should
be modified.
"""
#
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
    logger = util.logging.get_logger("project-sender")

    offsets = range(0, len(data), util.MAX_PACKET-8)
    chunk_size = util.MAX_PACKET-8
    thetimeout = .005
    sock.settimeout(thetimeout)
    currentWindowSize = 2
    sending = True
    j = 0
    timeoutAmount = 0
    connectionOver = 0
    sendingCurrentWindow = True
    done = False
    k = 0
    while sending:
        i = 0
        while sendingCurrentWindow:
            sendChunkz(j,currentWindowSize, data, sock, done)
            if done:
                break
            time1 = time.time()
            currentWindowSize += 1
            first = True
            waiting = True
            while waiting:
                try:
                    returnData = sock.recv(util.MAX_PACKET)
                    ackNum, checksum, noData = extract(returnData)
                    print("ack ", ackNum)
                    if j <= ackNum:
                        j = ackNum + 1
                    timeoutAmount = 0
                    if isLast(j - 1, data):
                        waiting = False
                        sending = False
                        sendingCurrentWindow = False
                        return
                except socket.timeout:
                    if first:
                        time2 = time.time()
                        thetimeout = avgTimeBetweenPackets(thetimeout,(time2 - time1))
                        sock.settimeout(thetimeout)
                        first = False
                    print("waiting on chunk")
                    timeoutAmount += 1
                    if timeoutAmount == 3:
                        currentWindowSize = round(currentWindowSize * .5)
                        if currentWindowSize <= 0:
                            currentWindowSize = 1
                    waiting = False
                    time.sleep(thetimeout)
                        
                if time.time() - time1 >= (thetimeout * currentWindowSize):
                    waiting = False
            
            
                    
                    
 
            
                           
            
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
    #changeableBuffer = io.BytesIO(bytearray(1392))
    #change = changeableBuffer.getbuffer()
    while True:
        data = sock.recv(util.MAX_PACKET)
        theNum, checksum, theData = extract(data)
        if (check(theData)) == checksum and currentNum == theNum:
            sock.send(make(theNum,0))
            print("ack--> ", currentNum)
            currentNum += 1
            sameNumber = 0
            logger.info("Received %d bytes", len(data))
            print (num_bytes, " - ", num_bytes + len(theData), " --Recieved: ", theNum)
            dest.write(theData)
            num_bytes += len(theData)
            dest.flush()
        else:
            if theNum + 1 == currentNum:
                sameNumber += 1
            if sameNumber >= 1:
                sock.send(make(currentNum -1 ,0))
            print(theNum, " <- packet being sent ", currentNum, " <- packet wanted")
        if not data:
            break
    return num_bytes
    
def avgTimeBetweenPackets(currentAvg, newEntry):
    currentAvg = currentAvg *.67 + newEntry * .33
    return currentAvg
    
def sendChunkN(n, data: bytes):
    chunk_size = util.MAX_PACKET-8
    offsets = range(0, len(data), util.MAX_PACKET-8)
    j = 0
    for chunk in [data[i:i + chunk_size] for i in offsets]:
        if j == n:
            checsum = check(chunk)
            theChunk = make(j, checsum, chunk)
            return theChunk
        else:
            j += 1

def sendChunkz(n,amount, data: bytes, sock: socket.socket, done):
    sending = True
    i = 0
    j = 0
    while sending:
        if not isLast(n + i, data) and i < amount:
            chunk = sendChunkN(n + i, data)
            try:
                sock.send(chunk)
                i += 1
                j = 0
            except TypeError:
                print("wrong type")
                j += 1
                if j >= 20:
                    done = True
                    i += 1 
        elif i < amount:
            chunk = sendChunkN(n + i, data)
            try:
                sock.send(chunk)
                i += 1
                done = True
            except TypeError:
                print("wrong type last")
        else:
            sending = False
                
        

def isLast(i, data):
    offsets = range(0, len(data), util.MAX_PACKET-8)
    chunk_size = util.MAX_PACKET-8
    return i == offsets[-1]/chunk_size
    
    
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

    
