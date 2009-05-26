import struct

def unpack(packed):
    id, = struct.unpack_from("!B", packed)
    print "Unpacking packet id=%s" % id
    packet = packets[id]()
    packet.unpack(packed)
    return packet


class Packet(object):
    id = 0
    format = "!BH"

    def pack(self, packed=""):
        return struct.pack(Packet.format, self.id, 3 + len(packed)) + \
            packed

    def unpack(self, packed):
        size = 3 #struct.calcsize(Packet.format)
        self.id, self.size = struct.unpack_from(Packet.format, packed)
        return size


element_types = {
        "fire": 1, 1: "fire",
        "earth": 2, 2: "earth",
        "wind": 3, 3: "wind",
        "water": 4, 4: "water",
    }


class JoinRequest(Packet):
    id = 1
    format = "!H%ds"
    
    def pack(self, packed=""):
        format = JoinRequest.format % len(self.player_name)
        return Packet.pack(self, struct.pack(format,
            len(self.player_name), self.player_name)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        pname_length, = struct.unpack_from("!H", packed, offset)
        self.player_name, = struct.unpack_from("%ds" % pname_length, packed, offset+2)
        return offset + 2 + pname_length


class JoinResponse(Packet):
    id = 1
    format = "!H"
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(JoinResponse.format,
            self.player_id)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.player_id, = struct.unpack_from(JoinResponse.format, packed, offset)
        return offset + 2


class SpawnRequest(Packet):
    id = 3
    format = "!B"

    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(SpawnRequest.format,
            element_types[self.element_type])) + \
            packed

    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        etype, = struct.unpack_from(SpawnRequest.format, packed, offset)
        self.element_type = element_types[etype]
        return offset + 1


class SpawnResponse(Packet):
    id = 4

packets = {
    0: Packet,
    1: JoinRequest,
    2: JoinResponse,
    3: SpawnRequest,
    4: SpawnResponse,
}