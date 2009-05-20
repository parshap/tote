from twisted.internet import protocol, reactor
import gamestate
from event import Event

class ServerProtocol(protocol.Protocol):
    def connectionMade(self):
        print "New connection #%s from %s." % (len(self.factory.clients), self.transport.getPeer())
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        print "Lost connection #%s from %s." % (len(self.factory.clients), self.transport.getPeer())

    def dataReceived(self, data):
        print "Message from %s: %s" % (self.transport.getPeer(), data)


class GameServer(protocol.ServerFactory):
    protocol = ServerProtocol
    
    def __init__(self, world, port):
        self.world = world
        self.port = port
        self.client_connected = Event()

    def startFactory(self):
        print "Server starting and listening on port %s." % self.port
        self.clients = []
        # This will be called before I begin listening on a Port or Connector.
        pass
        
    def stopFactory(self):
        print "Server stopping."
        # This will be called before I stop listening on all Ports/Connectors.
        pass
        
    def go(self):
        reactor.listenTCP(self.port, self)
        reactor.run(installSignalHandlers=0)
        
    def stop(self):
        reactor.stop()