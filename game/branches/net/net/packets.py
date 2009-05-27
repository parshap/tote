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
    """
    Optional attributes: player_name
    """
    id = 1
    format = "!H%ds"
    
    def __init__(self):
        Packet.__init__(self)
        self.player_name = ""
    
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
    """
    Required attributes:
    player_id
    """
    id = 2
    format = "!H" # player_id
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(JoinResponse.format,
            self.player_id)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.player_id, = struct.unpack_from(JoinResponse.format, packed, offset)
        return offset + 2


class SpawnRequest(Packet):
    """
    Required attributes:
    element_type
    """
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
    """
    Required attributes:
    x, z
    """
    id = 4
    format = "!ff"
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(SpawnResponse.format,
            self.x, self.z)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.x, self.z = struct.unpack_from(SpawnResponse.format, packed, offset)
        return offset + 8


class PlayerUpdate(Packet):
    """
    This is a packet sent from the client to the server to update the server
    with information regarding the current player.
    
    Required attributes:
    x, z, rotation, move_speed, move_direction
    """
    id = 5
    format = "!ff f f f" # position rotation move_speed move_direction
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(PlayerUpdate.format,
            self.x, self.z, self.rotation,
            self.move_speed, self.move_direction)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.x, self.z, self.rotation, self.move_speed, self.move_direction = \
            struct.unpack_from(PlayerUpdate.format, packed, offset)
        return offset + 20


object_types = {
    "player": 1, 1: "player",
}


class ObjectInit(Packet):
    """
    This is a packet sent from the server to the client to give extended
    information about a GameObject to the client. The server may likely only
    send one of these packets for each object.
    
    Required atributes: object_id, object_type
    Optional attributes: name, owner_id ttl
    """
    id = 6
    format = "!H B H %ds H f" # object_id, object_type, namelen, name, owner_id, ttl
    offset_namelen = struct.calcsize("H B")
    
    def __init__(self):
        Packet.__init__(self)
        self.name = ""
        self.owner_id = 0
        self.ttl = -1
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(ObjectInit.format % len(self.name),
            self.object_id, object_types[self.object_type],
            len(self.name), self.name, self.owner_id, self.ttl)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        namelen = struct.unpack_from("!H", packed, offset + self.offset_namelen)
        self.object_id, otype, namelen, self.name, self.owner_id, self.ttl = \
            struct.unpack_from(ObjectInit.format % namelen , packed, offset)
        self.object_type = object_types[otype]
        return offset + 11 + namelen


class ObjectUpdate(Packet):
    """
    This is a packet sent from the server to the client to give updated
    information about a GameObject to the client. The server will likely send
    these packets constantly to update the client's game state.
    
    Required attributes:
    object_id, x, z, rotation, move_speed, move_direction
    """
    id = 7
    format = "!H ff f f f" # object_id position rotation move_speed move_direction
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(ObjectUpdate.format,
            self.object_id, self.x, self.z, self.rotation,
            self.move_speed, self.move_direction)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.object_id, self.x, self.z, self.rotation, self.move_speed, self.move_direction = \
            struct.unpack_from(ObjectUpdate.format, packed, offset)
        return offset + 22


packets = {
    0: Packet,
    1: JoinRequest,
    2: JoinResponse,
    3: SpawnRequest,
    4: SpawnResponse,
    5: PlayerUpdate,
    6: ObjectInit,
    7: ObjectUpdate,
}