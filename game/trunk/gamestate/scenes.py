import gamestate
from xml.dom import minidom, Node
import os.path

class Scene(object):
    def __init__(self, world):
        self.world = world
        
    def generate_spawn_position(self):
        return (0, 0)
        
    def _setup_level_boundaries(self, filepath):
        """
        Takes an xml-style file that specifies all of the level's static boundinglinesegments, and creates those
        bounds in the world.
        """
        xml_data = minidom.parse(filepath)
        docRoot = xml_data.getElementsByTagName('segments')[0].childNodes
        for segmentNode in docRoot:
            if segmentNode.nodeType == Node.ELEMENT_NODE and segmentNode.nodeName == 'segment':
                point1_data = self._getXMLNode(segmentNode, "point1").attributes
                point2_data = self._getXMLNode(segmentNode, "point2").attributes
                normal_data = self._getXMLNode(segmentNode, "normal").attributes
                
                point1 = (float(point1_data["x"].nodeValue),  -float(point1_data["z"].nodeValue))
                point2 = (float(point2_data["x"].nodeValue),  -float(point2_data["z"].nodeValue))
                normal = (float(normal_data["x"].nodeValue),  float(normal_data["z"].nodeValue))
                
                boundary_wall = gamestate.objects.GameObject(self.world)
                boundary_wall.isPassable = False
                boundary_wall.position = point1
                
                boundary_wall.bounding_shape = gamestate.collision.BoundingLineSegment(point1, point2, normal)
                
                self.world.add_object(boundary_wall)
                
    def _getXMLNode(self, base, name):
        """
        This function basically doubles as both a test for element 
        existence and a getter for that element node... used with setup_level_boundaries()
        """
        if base.hasChildNodes:
            baseChildNodes = base.childNodes
            
            for node in baseChildNodes:
                if node.nodeType == Node.ELEMENT_NODE and node.nodeName == name:
                    return node
            
            return False


class TestScene(Scene):
    def __init__(self, world):
        Scene.__init__(self, world)
        
        # Add boundary lines for map walls.       
        self._setup_level_boundaries(os.path.join("media", "levelbounds.bounds"))