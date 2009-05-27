from twisted.internet import reactor, protocol

import threading, time, struct
from Queue import Queue
from event import Event
import packets

class ServerProtocol(protocol.Protocol):
    def connectionMade(self):
        print "New connection #%s from %s." % (len(self.factory.clients), self.transport.getPeer())
        self.factory.clients.append(self)
        self.factory.client_connected(self)
        self.current_packet = None
        self.buffer = ""

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        print "Lost connection #%s from %s." % (len(self.factory.clients), self.transport.getPeer())

    def dataReceived(self, data):
        self.buffer += data
        
        if self.current_packet is None and len(self.buffer) >= 3:
            self.current_packet = packets.Packet()
            self.current_packet.unpack(self.buffer)
            
        if self.current_packet is not None and len(self.buffer) >= self.current_packet.size:
            packet = packets.unpack(self.buffer)
            self.buffer = self.buffer[packet.size:]
            self.factory.input.put_nowait((self, packet))
            self.current_packet = None


class GameServer(protocol.ServerFactory):
    protocol = ServerProtocol
    
    def __init__(self, world, port):
        self.world = world
        self.port = port
        self.client_connected = Event()

    def startFactory(self):
        print "Server starting and listening on port %s." % self.port
        self.clients = []
        self.input = Queue()
        self.output = Queue()
        pass
        
    def stopFactory(self):
        print "Server stopping."
        pass
    
    def send(self):
        while not self.output.empty():
            (client, data) = self.output.get_nowait()
            client.transport.write(data.pack())
        
    def go(self):
        reactor.listenTCP(self.port, self)
        reactor.run(installSignalHandlers=0)
        
    def stop(self):
        reactor.stop()