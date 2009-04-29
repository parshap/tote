import math
import ogre

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
        self.vector = ogre.vector3(point1.x - point2.x, point1.y - point2.y, point1.z - point2.z)
        self.normal = normal
        self.shapeType = "linesegment"
        
class CollisionDetector:
    def castRay(originPoint, orientation):
        pass
    
    def checkCollision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition):
        # determine type of shape and call appropriate helper function
        if(colliderShape.shapeType == "circle" and collideeShape == "linesegment"):
            return _check_circle_segment_collision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition)
        pass
    
    def _check_circle_segment_collision(segment, segmentPosition, circle, circlePosition):
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
        
        
        if(discrim < 0): # no collision
            return None
        elif (discrim == 0): # perfect collision
            # u is the % of the distance from p1 to p2 the intersection point falls at
            u = -b / (2 * a)
            collisionPoint = (point1.x + u * p2Minusp1.x, 0, point1.z + u * p2Minusp1.z)
            if(u < 0 or u > 1):
                return None
            else:
                return collisionPoint
        elif (discrim > 0): # collision with 2 intersection points
            u1 = (-b + math.sqrt(discrim)) / (2 * a)
            u2 = (-b - math.sqrt(discrim)) / (2 * a)
            
            # check to make sure the collision point falls between point1 and point2 on the line
            avg = (u1 + u2)/2
            if(avg < 0 or avg > 1):
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