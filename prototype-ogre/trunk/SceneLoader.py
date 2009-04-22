#!/usr/bin/env python
# SceneLoader.py

# Copyright (C) 2008  Colin McCulloch
#

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This module contains the dotscene file loader implementation we 
will be using in this application.  While this does not implemet the 
entire dotscene feature set, it does (or rather will) implement 
everthing we need

Author: Colin "Zyzle" McCulloch

Last Edit By: $Author$

"""

__version__ = "$Revision$"
__date__ = "$Date$"

from xml.dom import minidom, Node

import ogre.renderer.OGRE as ogre

# This is to compensate for the rather annoying habit of the blender
# exporter to export modules at a very small scale. I think rather than
# having this here we should probably set it in the constructor for
# the dotsceneloader.
GLOBAL_SCALE_FACTOR = 1

# dictionary to hold the various light types used by ogre and the 
# equivilents in the blender export
LIGHT_TYPES = {'point' : ogre.Light.LT_POINT,
               'directional' : ogre.Light.LT_DIRECTIONAL,
               'spotLight' : ogre.Light.LT_SPOTLIGHT,
               'radPoint' : ogre.Light.LT_POINT
              }
              
PROJECTION_TYPES = {'perspective' : ogre.PT_PERSPECTIVE,
                    'orthographic' : ogre.PT_ORTHOGRAPHIC
                   }

def getNode(base, name):
    """This function basically doubles as both a test for element 
    existence and a getter for that element node
    """
    if base.hasChildNodes:
        baseChildNodes = base.childNodes
        
        for node in baseChildNodes:
            if node.nodeType == Node.ELEMENT_NODE and node.nodeName == name:
                return node
        
        return False

class DotSceneLoader(object):
    """This class gives us access to the ogre.scene xml file format"""
    
    def __init__(self, file, sceneManager):
        """The constructor takes in the dotscene file name and the
        sceneManager of the game"""
        self.file = file
        self.sceneManager = sceneManager
        
        self.dotSceneXML = minidom.parse(file)
        
        # for the moment we are ignoring the environment and externals
        # of the .scene file
        self.docRoot = self.dotSceneXML.getElementsByTagName('nodes')[0] \
                        .childNodes
                        
        self.nodeNames = {}
        self.geomList = []
        
    def parseDotScene(self):
        """This method parses the dotscene file and creates the various meshes,
        cameras and lights in the file. 
        """
        for node in self.docRoot:
            if node.nodeType == Node.ELEMENT_NODE and node.nodeName == 'node':
                newNode = self.sceneManager.getRootSceneNode() \
                            .createChildSceneNode(node.getAttribute('name'))
                
                self.nodeNames[node.getAttribute('name')] = newNode
                
                posNode = getNode(node, 'position').attributes

                newNode.setPosition(float(posNode['x'].nodeValue)
                                    * GLOBAL_SCALE_FACTOR,
                                    float(posNode['y'].nodeValue)
                                    * GLOBAL_SCALE_FACTOR,
                                    float(posNode['z'].nodeValue)
                                    * GLOBAL_SCALE_FACTOR)
                
                rotationNode = getNode(node, 'quaternion').attributes

                newNode.setOrientation(ogre.Quaternion(
                                        float(rotationNode['w'].nodeValue), 
                                        float(rotationNode['x'].nodeValue), 
                                        float(rotationNode['y'].nodeValue), 
                                        float(rotationNode['z'].nodeValue)))
                
                scaleNode = getNode(node, 'scale').attributes
                
                newNode.setScale(float(scaleNode['x'].nodeValue) 
                                    * GLOBAL_SCALE_FACTOR, 
                                    float(scaleNode['y'].nodeValue) 
                                    * GLOBAL_SCALE_FACTOR, 
                                    float(scaleNode['z'].nodeValue)
                                    * GLOBAL_SCALE_FACTOR)
                
                entNode = getNode(node, 'entity')
                lightNode = getNode(node, 'light')
                cameraNode = getNode(node, 'camera')
                
                if entNode:
                    entity = entNode.attributes
                    name = entity['name'].nodeValue
                    mesh = entity['meshFile'].nodeValue
                    ent = self.sceneManager.createEntity(name, mesh)
                    newNode.attachObject(ent)
                    # TODO: The idea is that we can create a list of all
                    # geometry here and then add the ode collision stuff
                    # to it from the Scene class
                
                if lightNode:
                    lightattr = lightNode.attributes
                    diffuse = getNode(lightNode, 'colourDiffuse').attributes
                    specular = getNode(lightNode, 'colourSpecular').attributes
                    if getNode(lightNode, 'lightAttenuation'):
                        attenuation = getNode(lightNode, 
                                            'lightAttenuation').attributes
                    else:
                        attenuation = None
                    
                    light = self.sceneManager.createLight(
                                                  lightattr['name'].nodeValue)
                    light.type = LIGHT_TYPES[lightattr['type'].nodeValue]
                    light.diffuseColour = (float(diffuse['r'].nodeValue)
                                           * GLOBAL_SCALE_FACTOR,
                                           float(diffuse['g'].nodeValue)
                                           * GLOBAL_SCALE_FACTOR,
                                           float(diffuse['b'].nodeValue)
                                           * GLOBAL_SCALE_FACTOR
                                          )
                                          
                    light.specularColour = (float(specular['r'].nodeValue)
                                            * GLOBAL_SCALE_FACTOR,
                                            float(specular['g'].nodeValue)
                                            * GLOBAL_SCALE_FACTOR,
                                            float(specular['b'].nodeValue)
                                            * GLOBAL_SCALE_FACTOR
                                           )
                    if attenuation:
                        light.setAttenuation(float(attenuation['range'] \
                                                                .nodeValue)
                                                / GLOBAL_SCALE_FACTOR,
                                            float(attenuation['constant'] \
                                                                .nodeValue)
                                                / GLOBAL_SCALE_FACTOR,
                                            float(attenuation['linear'] \
                                                                .nodeValue)
                                                / GLOBAL_SCALE_FACTOR,
                                            float(attenuation['quadratic'] \
                                                                .nodeValue)
                                                / GLOBAL_SCALE_FACTOR
                                            )
                    #print "Adding Light"
                    newNode.attachObject(light)
                    
                if cameraNode:
                    camattr = cameraNode.attributes
                    clipping = getNode(cameraNode, 'clipping').attributes
                    
                    camera = self.sceneManager.createCamera(camattr['name'] \
                                                            .nodeValue)
                    camera.setProjectionType(PROJECTION_TYPES[ \
                                                camattr['projectionType'] \
                                                    .nodeValue])
                    camera.FOVy = ogre.Degree(float(camattr['fov'].nodeValue))
                    camera.nearClipDistance = float(clipping['nearPlaneDist'] \
                                                        .nodeValue) \
                                                        * GLOBAL_SCALE_FACTOR
                    camera.farClipDistance = float(clipping['farPlaneDist'] \
                                                        .nodeValue) \
                                                        * GLOBAL_SCALE_FACTOR
                    newNode.attachObject(camera)
                    
    def getNodeByName(self, name):
        """This method is used to return any node created by the
        dotscene file, although ogre has its own functions to
        do the same thing this can be easier at times.
        """
        try:
            return self.nodeNames[name]
        except KeyError:
            return False
        
    def iterGeometry(self):
        for geom in self.geomList:
            yield geom