from __future__ import division
import math
import ogre.renderer.OGRE as ogre # access to ogre.Vector3

class BoundingShape:
    def __init__(self):
        pass
        
class BoundingCircle(BoundingShape):
    def __init__(self, radius):
        self.radius = radius
        self.shapeType = "circle"

class BoundingLineSegment(BoundingShape):
    def __init__(self, point1, point2, normal):
        self.position = point1
        self.vector = ogre.Vector3(point2.x - point1.x, point2.y - point1.y, point2.z - point1.z)
        self.normal = normal
        self.shapeType = "linesegment"
        
class CollisionDetector:
    def castRay(originPoint, orientation, queryDistance, possibleObjects):
        # for each object
        for object in possibleObjects:
            # get the object's bounding shape
            shapeType = object.shapeType
            
            # determine the shapetype and run the appropriate ray query function
            if shapeType == "circle":
                return _ray_circle_collision(originPoint, orientation, queryDistance, object.boundingShape, object.position)
            elif shapeType == "linesegment":
                return _ray_segment_collision(originPoint, orientation, queryDistance, object.boundingShape, object.position)
            else:
                pass
            
    def checkCollision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition):
        # determine type of shape and call appropriate helper function
        if colliderShape.shapeType == "circle" and collideeShape == "linesegment":
            return _check_circle_segment_collision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition)
        pass
            
    def _ray_circle_collision(originPoint, orientation, queryDistance, circle, circlePosition):
        # calculate distance between points
        distance = _get_xz_distance(originPoint, position)
        
        # optimization... if the points are two far away to possibly collide, don't process this
        if queryDistance < distance - radius:
            return False
        
        # get the absolute position of the ray's endpoints
        endx = originPoint.x + math.cos(orientation)*queryDistance
        endz = originPoint.z + math.sin(orientation)*queryDistance
        endPoint = ogre.Vector3(endx, 0, endz)
        
        point1 = originPoint
        point2 = endPoint
        
        # first transform the segment vertices to coordinates relative to the circle's center
        localP1 = ogre.Vector3(originPoint.x - circlePosition.x, 0, originPoint.z - circlePosition.z)
        localP2 = ogre.Vector3(endPoint.x - circlePosition.x, 0, endPoint.z - circlePosition.z)
        
        # pre-calculate p1-p2 for easy reference
        p2Minusp1 = ogre.Vector3(endPoint.x - originPoint.x, 0, endPoint.z - originPoint.z)
        
        # get quadratic coefficients
        a = (p2Minusp1.x * p2Minusp1.x) + (p2Minusp1.z * p2Minusp1.z)
        b = 2 * ((p2Minusp1.x * localP1.x) + (p2Minusp1.z * localP1.z))
        c = (localP1.x * localP1.x) + (localP1.z * localP1.z) - (circle.radius * circle.radius)
        
        discrim = b * b - 4 * a * c
        
        
        if discrim < 0: # no collision
            return False
        else:
            solution1 = (-b + math.sqrt(discrim))/(2*a)
            solution2 = (-b - math.sqrt(discrim))/(2*a)
            
            if solution1 >= 0 and solution1 <= 1:
                return True
            if solution2 >= 0 and solution2 <= 1:
                return True
            return False
          
    def _get_xz_distance(point1, point2):
        dx = point1.x - point2.x
        dz = point1.z - point2.z
        return math.sqrt(dx*dx + dz*dz)
    
    def _ray_segment_collision(originPoint, orientation, distance, segment, position):
        # get the 4 relevant points
        
        # a1 and a2 define the ray cast segment
        a1 = originPoint
        a2 = ogre.Vector3(originPoint.x + math.cos(orientation)*distance, 0, originPoint.z + math.sin(orientation)*distance)
        
        # b1 and b2 define the line segment we are checking against
        b1 = position
        b2 = position + segment.vector
        
        # calculate denominator
        denom = ((b2.z - b1.z) * (a2.x - a1.x)) - ((b2.x - b1.x) * (a2.z - a1.z))
        
        if denom == 0: # the segments are parallel
            return False # no collision
        else:
            # otherwise we have to solve for the intersection points
            ua = (((b2.x - b1.x) * (a1.z - b1.z)) - ((b2.z - b1.z) * (a1.x - b1.x))) / denom
            ub = (((a2.x - a1.x) * (a1.z - b1.z)) - ((a2.z - a1.z) * (a1.x - b1.x))) / denom
            
            # ua and ub represent the % along the corresponding segment the intersection happens
            # if ua or ub is less than 0 (0%) or greater than 1 (100%) then segments did not collide, return False
            if (ua < 0) or (ua > 1) or (ub < 0) or (ub > 1):
                return False
            else:
                return True

    
    def _check_circle_segment_collision(circle, circlePosition, segment, segmentPosition):
        # get the absolute position of the line segment vertices
        point1 = segment.position
        point2 = segment.position + segment.vector
        
        # first transform the segment vertices to coordinates relative to the circle's center
        localP1 = ogre.Vector3(point1.x - circlePosition.x, 0, point1.z - circlePosition.z)
        localP2 = ogre.Vector3(point2.x - circlePosition.x, 0, point2.z - circlePosition.z)
        
        # pre-calculate p1-p2 for easy reference
        p2Minusp1 = ogre.Vector3(point2.x - point1.x, 0, point2.z - point1.z) # same as segment.vector?
        
        # get quadratic coefficients
        a = (p2Minusp1.x * p2Minusp1.x) + (p2Minusp1.z * p2Minusp1.z)
        b = 2 * ((p2Minusp1.x * localP1.x) + (p2Minusp1.z * localP1.z))
        c = (localP1.x * localP1.x) + (localP1.z * localP1.z) - (circle.radius * circle.radius)
        
        discrim = b * b - 4 * a * c
        
        
        if discrim < 0: # no collision
            return None
        elif discrim == 0: # perfect collision
            # u is the % of the distance from p1 to p2 the intersection point falls at
            u = -b / (2 * a)
            collisionPoint = (point1.x + u * p2Minusp1.x, 0, point1.z + u * p2Minusp1.z)
            if u < 0 or u > 1:
                return None
            else:
                return collisionPoint
        elif discrim > 0: # collision with 2 intersection points
            u1 = (-b + math.sqrt(discrim)) / (2 * a)
            u2 = (-b - math.sqrt(discrim)) / (2 * a)
            
            # check to make sure the collision point falls between point1 and point2 on the line
            avg = (u1 + u2)/2
            if avg < 0 or avg > 1:
                return None
            
            # now we calculate the two collision points (where the circle intersects the segment
            intersectionPoint1 = ogre.Vector3(point1.x + u1 * p2Minusp1.x, 0, point1.z + u1 * p2Minusp1.z)
            intersectionPoint2 = ogre.Vector3(point1.x + u2 * p2Minusp1.x, 0, point1.z + u2 * p2Minusp1.z)
            
            # find the point on the segment where the circle collided initially
            collisionPoint = intersectionPoint1.midPoint(intersectionPoint2)
            
            # the distance to space the circle and the segment when collision is resolved
            spacing = 0.00001
            
            # the distance to place the center of the circle from the point of collision
            distance = circle.radius + spacing
            
            
            # translate the circle's position along the segment's normal 'radius' units
            resolvedPosition = ogre.Vector3(collisionPoint.x + distance * segment.normal.x, collisionPoint.y + distance * segment.normal.y, collisionPoint.z + distance * segment.normal.z)
            
            return resolvedPosition