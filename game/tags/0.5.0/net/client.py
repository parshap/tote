from twisted.internet import reactor, protocol

import threading, time, struct
from Queue import Queue
from event import Event
import packets


class ClientProtocol(protocol.Protocol):
    def connectionMade(self):
        server = self.transport.getPeer()
        print "Connected to %s:%s." % (server.host, server.port)
        self.factory.server_transport = self.transport
        self.factory.connected()
        self.current_packet = None
        self.buffer = ""
    
    def dataReceived(self, data):
        self.buffer += data
        self._processBuffer()
        
    def _processBuffer(self):
        if self.current_packet is None and len(self.buffer) >= 3:
            self.current_packet = packets.Packet()
            self.current_packet.unpack(self.buffer)
            
        if self.current_packet is not None and len(self.buffer) >= self.current_packet.size:
            packet = packets.unpack(self.buffer)
            self.buffer = self.buffer[packet.size:]
            self.factory.input.put_nowait(packet)
            self.current_packet = None
            self._processBuffer()
    
    def connectionLost(self, reason):
        server = self.transport.getPeer()
        print "Lost connection to %s:%s." % (server.host, server.port)


class GameClient(protocol.ClientFactory):
    protocol = ClientProtocol
    
    def __init__(self, world, addr, port):
        self.world = world
        self.addr = addr
        self.port = port
        self.connected = Event()
        self.input = Queue()
        self.output = Queue()

    def startFactory(self):
        pass
        
    def stopFactory(self):
        pass

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: %s" % reason
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost: %s" % reason
        reactor.stop()
        
    def send(self):
        while not self.output.empty():
            data = self.output.get_nowait()
            self.server_transport.write(data.pack())
        
    def go(self):
        reactor.connectTCP(self.addr, self.port, self)
        reactor.run(installSignalHandlers=0)
    
    def stop(self):
        reactor.stop()