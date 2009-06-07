import struct

def unpack(packed):
    id, = struct.unpack_from("!B", packed)
    # print "Unpacking packet id=%s." % id
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
        "air": 3, 3: "air",
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
    Sent from the server to a client to let it know they are spawning in the
    world.
    Required attributes:
    element_type, x, z
    """
    id = 4
    format = "!B ff" # element_type x z
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(SpawnResponse.format,
            element_types[self.element_type], self.x, self.z)) + \
            packed

    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        etype, self.x, self.z = struct.unpack_from(SpawnResponse.format, packed, offset)
        self.element_type = element_types[etype]
        return offset + 9


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
    Optional attributes: element_type, name, owner_id ttl,
    """
    id = 6
    format = "!H B B H %ds H f" # object_id, object_type, element_type, namelen, name, owner_id, ttl 
    offset_namelen = struct.calcsize("H B B")
    
    def __init__(self):
        Packet.__init__(self)
        self.element_type = 0
        self.name = ""
        self.owner_id = 0
        self.ttl = -1
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(ObjectInit.format % len(self.name),
            self.object_id, object_types[self.object_type], element_types[self.element_type],
            len(self.name), self.name, self.owner_id, self.ttl)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        namelen = struct.unpack_from("!H", packed, offset + self.offset_namelen)
        self.object_id, otype, etype, namelen, self.name, self.owner_id, self.ttl = \
            struct.unpack_from(ObjectInit.format % namelen , packed, offset)
        self.object_type = object_types[otype]
        self.element_type = element_types[etype]
        return offset + 12 + namelen


class ObjectUpdate(Packet):
    """
    This is a packet sent from the server to the client to give updated
    information about a GameObject to the client. The server will likely send
    these packets constantly to update the client's game state.
    
    Required attributes:
    object_id, x, z, rotation, move_speed, move_direction, is_dead
    Optional attributes:
    forced
    """
    id = 7
    format = "!H ff f f f B" # object_id position rotation move_speed move_direction flags
    _flags_mask_forced = 1 << 0
    _flags_mask_is_dead = 1 << 1
    
    def __init__(self):
        Packet.__init__(self)
        self.forced = False
    
    def pack(self, packed=""):
        flags = 0
        if self.forced: flags |= self._flags_mask_forced
        if self.is_dead: flags |= self._flags_mask_is_dead
        return Packet.pack(self, struct.pack(ObjectUpdate.format,
            self.object_id, self.x, self.z, self.rotation,
            self.move_speed, self.move_direction, flags)) + \
            packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.object_id, self.x, self.z, self.rotation, self.move_speed, \
            self.move_direction, flags = \
            struct.unpack_from(ObjectUpdate.format, packed, offset)
        self.forced = (flags & self._flags_mask_forced) == self._flags_mask_forced
        self.is_dead = (flags & self._flags_mask_is_dead) == self._flags_mask_is_dead
        return offset + 23
        

class ObjectStatusUpdate(Packet):
    """
    This is a packet generally sent from the server to client(s) when the
    status (power or health) of another object needs to be updated.
    
    Required attributes:
    object_id, health, power
    """
    id = 9
    format = "!H f f" # object_id health power
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(ObjectStatusUpdate.format,
            self.object_id, self.health, self.power)) + packed
            
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.object_id, self.health, self.power = struct.unpack_from(
            ObjectStatusUpdate.format, packed, offset)
        return offset + 10


class ObjectRemove(Packet):
    """
    This is a packet generally sent from the server to client(s) when an object
    should be removed from the game world.
    
    Required attributes:
    object_id
    """
    id = 8
    format = "!H" # object_id
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(ObjectRemove.format,
            self.object_id)) + packed
            
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.object_id, = struct.unpack_from(ObjectRemove.format, packed, offset)
        return offset + 2


class AbilityRequest(Packet):
    """
    This is a packet sent from the client to the server to request to use an
    ability. The server will sen dout an AbilityUsed packet if the request is
    accepted.
    
    Required attributes:
    ability_id - the id of the ability the player is requsting ot use.
    """
    id = 10
    format = "!H" # ability_id
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(AbilityRequest.format,
            self.ability_id)) + packed
            
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.ability_id, = struct.unpack_from(AbilityRequest.format, packed, offset)
        return offset + 2


class AbilityUsed(Packet):
    """
    This is a packet sent from the server to all clients when a player uses an
    ability. This is genreally a response to an AbilityRequest packet from a
    client.
    
    Required attributes:
    object_id - the id of the player using the ability
    ability_id - the id of the ability
    """
    id = 11
    format = "!H H" # object_id ability_id
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(AbilityUsed.format,
            self.object_id, self.ability_id)) + packed
            
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.object_id, self.ability_id = struct.unpack_from(AbilityUsed.format, packed, offset)
        return offset + 4


message_types = {
    "error": 1, 1: "error",
    "notice": 2, 2: "notice",
    "success": 3, 3: "success",
    "system": 4, 4: "system",
    "death": 5, 5: "death",
}


class Message(Packet):
    """
    Required attributes:
    message - the text of the message
    type - the type of the message
    """
    id = 20
    format = "!H %ds B" # message_length, message, type
    
    def pack(self, packed=""):
        typeid = message_types[self.type]
        return Packet.pack(self, struct.pack(Message.format % len(self.message),
            len(self.message), self.message, typeid)) + packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        mlen = struct.unpack_from("!H", packed, offset)
        mlen, self.message, typeid = struct.unpack_from(Message.format % mlen, packed, offset)
        self.type = message_types[typeid]
        return offset + 3 + mlen


class ScoreUpdate(Packet):
    """
    Required attributes: player_id, score
    """
    id = 21
    format = "!H h" # player_id, score
    
    def pack(self, packed=""):
        return Packet.pack(self, struct.pack(ScoreUpdate.format,
            self.player_id, self.score)) + packed
    
    def unpack(self, packed):
        offset = Packet.unpack(self, packed)
        self.player_id, self.score = struct.unpack_from(ScoreUpdate.format,
            packed, offset)
        return offset + 4
        
class RoundStart(Packet):
    id = 22

class RoundEnd(Packet):
    id = 23

packets = {
    0: Packet,
    1: JoinRequest,
    2: JoinResponse,
    3: SpawnRequest,
    4: SpawnResponse,
    5: PlayerUpdate,
    6: ObjectInit,
    7: ObjectUpdate,
    8: ObjectRemove,
    9: ObjectStatusUpdate,
    10: AbilityRequest,
    11: AbilityUsed,
    20: Message,
    21: ScoreUpdate,
    22: RoundStart,
    23: RoundEnd,
}