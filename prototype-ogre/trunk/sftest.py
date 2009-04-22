#!/usr/bin/env python 
# This code is Public Domain. 
"""Python-Ogre Basic Tutorial 01: The SceneNode, Entity, and SceneManager constructs.""" 
 
import ogre.renderer.OGRE as ogre 
import SampleFramework as sf 
import SceneLoader
 
class TutorialApplication (sf.Application): 
    """Application class.""" 
 
    def _createScene (self):        
        # Setup the ambient light. 
        sceneManager = self.sceneManager 
 
        # load scene
        loader = SceneLoader.DotSceneLoader('testtilescene.scene', sceneManager)
        loader.parseDotScene()
 
if __name__ == '__main__': 
    ta = TutorialApplication () 
    ta.go ()