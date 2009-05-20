from twisted.internet import reactor, protocol

import threading, time
from Queue import Queue
from event import Event


class ClientProtocol(protocol.Protocol):
    def connectionMade(self):
        server = self.transport.getPeer()
        print "Connected to %s:%s." % (server.host, server.port)
        self.factory.server_transport = self.transport
        self.factory.connected()
    
    def dataReceived(self, data):
        self.factory.input.put_nowait(data)
    
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

    def startFactory(self):
        self.input = Queue()
        self.output = Queue()
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
            self.server_transport.write(data)
        
    def go(self):
        reactor.connectTCP(self.addr, self.port, self)
        reactor.run(installSignalHandlers=0)
    
    def stop(self):
        reactor.stop()