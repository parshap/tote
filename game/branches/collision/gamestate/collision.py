from __future__ import division
import math
import ogre.renderer.OGRE as ogre # access to ogre.Vector3


class BoundingShape(object):
    def __init__(self):
        pass


class BoundingCircle(BoundingShape):
    def __init__(self, radius):
        BoundingShape.__init__(self)
        self.radius = radius
        self.shapeType = "circle"


class BoundingLineSegment(BoundingShape):
    def __init__(self, point1, point2, normal):
        BoundingShape.__init__(self)
        self.vector = ogre.Vector3(point2[0] - point1[0], 0, point2[1] - point1[1])
        self.normal = ogre.Vector3(normal[0], 0, normal[1])
        self.shapeType = "linesegment"


class CollisionDetector(object):
    @staticmethod
    def cast_ray(originPoint, endPoint, collideeShape, collideeShapePosition):
        # Convert the points from (x,z) tuples to ogre.Vector3
        # @todo: decide on one point data structure...
        originPoint = ogre.Vector3(originPoint[0], 0, originPoint[1])
        endPoint = ogre.Vector3(endPoint[0], 0, endPoint[1])
        collideeShapePosition = ogre.Vector3(collideeShapePosition[0], 0, collideeShapePosition[1])
        
        # get the collidee's bounding shape type
        shapeType = collideeShape.shapeType
        
        # determine the shapetype and run the appropriate ray query function
        if shapeType == "circle":
            return CollisionDetector._ray_circle_collision(originPoint, endPoint, collideeShape, collideeShapePosition)
        elif shapeType == "linesegment":
            return CollisionDetector._ray_segment_collision(originPoint, endPoint, collideeShape, collideeShapePosition)
        else:
            pass

    @staticmethod
    def check_collision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition):
        # Convert the points from (x,z) tuples to ogre.Vector3
        # @todo: decide on one point data structure...
        colliderShapePosition = ogre.Vector3(colliderShapePosition[0], 0, colliderShapePosition[1])
        collideeShapePosition = ogre.Vector3(collideeShapePosition[0], 0, collideeShapePosition[1])
        
        # determine type of shape and call appropriate helper function
        if colliderShape.shapeType == "circle" and collideeShape.shapeType == "linesegment":
            return CollisionDetector._resolve_circle_segment_collision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition)
        elif colliderShape.shapeType == "circle" and collideeShape.shapeType == "circle":
            return CollisionDetector._resolve_circle_circle_collision(colliderShape, colliderShapePosition, collideeShape, collideeShapePosition)

    @staticmethod
    def _ray_circle_collision(originPoint, endPoint, circle, circlePosition):
        # calculate distances
        rayLength = CollisionDetector._get_xz_distance(originPoint, endPoint)
        distanceToCircle = CollisionDetector._get_xz_distance(originPoint, circlePosition) - circle.radius

        # optimization... if the points are two far away to possibly collide, don't process this
        if rayLength < distanceToCircle:
            return False
       
        # first transform the ray's endpoints to coordinates relative to the circle's center
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

    @staticmethod
    def _get_xz_distance(point1, point2):
        dx = point1.x - point2.x
        dz = point1.z - point2.z
        return math.sqrt(dx*dx + dz*dz)

    @staticmethod
    def _ray_segment_collision(originPoint, endPoint, segment, segmentPos):
        # a1 and a2 define the ray cast segment
        a1 = originPoint
        a2 = endPoint

        # b1 and b2 define the line segment we are checking against
        b1 = segmentPos
        b2 = b1 + segment.vector

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

    @staticmethod
    def _resolve_circle_segment_collision(circle, circlePosition, segment, segmentPosition):
        # get the absolute position of the line segment vertices
        point1 = segmentPosition
        point2 = segmentPosition + segment.vector
        
        # print "Ray Orientation: %.2f" % (orientation/math.pi)

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
            collisionPoint = ogre.Vector3(point1.x + u * p2Minusp1.x, 0, point1.z + u * p2Minusp1.z)
            if u < 0 or u > 1:
                return None
            else:
                return (collisionPoint.x, collisionPoint.z)
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
            spacing = 0.1

            # the distance to place the center of the circle from the point of collision
            distance = circle.radius + spacing

            # translate the circle's position along the segment's normal 'radius' units
            resolvedPosition = ogre.Vector3(collisionPoint.x + distance * segment.normal.x, collisionPoint.y + distance * segment.normal.y, collisionPoint.z + distance * segment.normal.z)
            
            # get the relative translation vector to resolve the object's position
            # this vector is what the collider object must be translated by for the collision to be resolved correctly
            resolutionVector = (resolvedPosition.x - circlePosition.x, resolvedPosition.z - circlePosition.z)

            return resolutionVector
    
    @staticmethod
    def _resolve_circle_circle_collision(circle1, center1, circle2, center2):            
        # get distance between circle centers
        distance = CollisionDetector._get_xz_distance(center1, center2)
        
        # check to see if collision happened
        if distance > circle1.radius + circle2.radius:
            # no collision
            return None
        
        # otherwise we have a collision
        else:
            # calculate the resolution translation vector (rtv)
            dx = center1.x - center2.x
            dz = center1.z - center2.z
            
            theta = math.atan2(dz, dx)
            
            # the distance to space the circle from the point of collision when we resolve the collision
            spacing = 0.1
            
            # this is the collision point
            resolutionPoint = ogre.Vector3(center2.x + (circle2.radius+spacing) * math.cos(theta),
                                           0,
                                           center2.z + (circle2.radius+spacing) * (-math.sin(theta)))
            
            # calculate the resolution translation vector relative to the current position of circle1
            rtv = (resolutionPoint.x - center1.x, resolutionPoint.z - center1.z)
            
            # return the value
            return rtv
                
                
            