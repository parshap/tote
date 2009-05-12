import math
import ogre.renderer.OGRE as ogre
                                             
class BoundingObject(object):
    def __init__(self, type):
        self.type = type


class BoundingCircle(BoundingObject):
    def __init__(self, radius):
        BoundingObject.__init__(self, "circle")
        self.radius = radius


class BoundingLineSegment(BoundingObject):
    def __init__(self, point1, point2, normal=None):
        BoundingObject.__init__(self, "linesegment")
        self.point1 = ogre.Vector3(point1[0], 0, point1[1])
        self.point2 = ogre.Vector3(point2[0], 0, point2[1])
        self.vector = ogre.Vector3(self.point2.x - self.point1.x, 0, self.point2.z - self.point1.z)
        if normal is not None:
            self.normal = ogre.Vector3(normal[0], 0, normal[1])
        #@todo: if normal == None, calculate it from p1, p2


class BoundingRectangle(BoundingObject):
    def __init__(self, width, height, rotation):
        BoundingObject.__init__(self, "rectangle")
        
        self.width = width
        self.height = height
        self.rotation = math.radians(rotation)
        
        w = width/2
        h = height/2
        
        c = math.sqrt(w*w + h*h)
        self.max_distance = c
        
        # calculate rectangle vertices as relative offsets from center
        
        theta = math.atan2(height, width)

        #DONT CHANGE THIS - order of points is important
        point1 = ogre.Vector3(c * math.cos(self.rotation + theta), 0, c * math.sin(self.rotation + theta))
        point2 = ogre.Vector3(c * math.cos(self.rotation + (math.pi - theta)), 0, c * math.sin(self.rotation + (math.pi - theta)))
        point3 = ogre.Vector3(c * math.cos(self.rotation + (math.pi + theta)), 0, c * math.sin(self.rotation + (math.pi + theta)))
        point4 = ogre.Vector3(c * math.cos(self.rotation + (-theta)), 0, c * math.sin(self.rotation + (-theta)))        
        
        # calculate normals
        mp1 = ogre.Vector3.midPoint(point1, point2)
        mp2 = ogre.Vector3.midPoint(point2, point3)
        mp3 = ogre.Vector3.midPoint(point3, point4)
        mp4 = ogre.Vector3.midPoint(point4, point1)
        
        normalp1p2 = ogre.Vector3(mp1.x, 0, mp1.z).normalisedCopy()
        normalp2p3 = ogre.Vector3(mp2.x, 0, mp2.z).normalisedCopy()
        normalp3p4 = ogre.Vector3(mp3.x, 0, mp3.z).normalisedCopy()
        normalp4p1 = ogre.Vector3(mp4.x, 0, mp4.z).normalisedCopy()

        # create component BoundingLineSegments that make up this BoundingRectangle
        side1 = BoundingLineSegment((point1.x, point1.z), (point2.x, point2.z), (normalp1p2.x, normalp1p2.z))
        side2 = BoundingLineSegment((point2.x, point2.z), (point3.x, point3.z), (normalp2p3.x, normalp2p3.z))
        side3 = BoundingLineSegment((point3.x, point3.z), (point4.x, point4.z), (normalp3p4.x, normalp3p4.z))
        side4 = BoundingLineSegment((point4.x, point4.z), (point1.x, point1.z), (normalp4p1.x, normalp4p1.z))
        
        
        # store the BoundingLineSegments
        self.sides = (side1, side2, side3, side4)
        
        # store axis-aligned bounding box for collision optimization
        # @todo: for optimization for all shapes, we can have all boundingshapes store their axis-aligned bounding boxes
        # the advantage would be most collision checking (when there is no collision) would run MUCH MUCH faster
        # IMPLEMENT THIS AS AN OPTIMIZATION STEP ONLY IF NEEDED
        xCoords = [point1.x, point2.x, point3.x, point4.x]
        zCoords = [point1.z, point2.z, point3.z, point4.z]
        self.max_x = max(xCoords)
        self.min_x = min(xCoords)
        self.max_z = max(zCoords)
        self.min_z = min(zCoords)

class BoundingCone(BoundingObject):
    def __init__(self, radius, orientation):
        BoundingObject__init__(self, "cone")
        self.radius = radius
        self.orientation = orientation


class UnsupportedShapesException(Exception):
    def __init__(self, shape1, shape2):
        self.shape1 = shape1
        self.shape2 = shape2
        
    def __str__(self):
        return "Collision between the following shapes is not supported: %s, %s" % \
            (self.shape1.type, self.shape2.type)


class CollisionDetector(object):
    SPACING = 0.1

    @staticmethod
    def is_between(shape, position, point1, point2):
        """
        Returns True if the given shape at the given position is between the
        two given points (i.e., if it collides with the line segment between
        point1 and point2). Returns False otherwisel.
        Raises an UnsupportedShapesException if the given shape type is not
        supported.
        """
        line = BoundingLineSegment(point1, point2)
        
        # If the line has lenght 0 it cannot possibly collide with anything.
        if(line.vector.x == 0. and line.vector.y == 0.):
            return False;
        
        # convert tuples to ogre.Vector3
        position = ogre.Vector3(position[0], 0, position[1])
        point1 = ogre.Vector3(point1[0], 0, point1[1])
        point2 = ogre.Vector3(point2[0], 0, point2[1])
        
        if shape.type == "circle":
            return CollisionDetector._check_circle_line(shape, position, line, point1) is not False
        elif shape.type == "linesegment":
            return CollisionDetector._check_line_line(shape, position, line, point1) is not False
        elif shape.type == "rectangle":
            #return CollisionDetector._check_line_rect(shape, position, line, point1) is not False
            return False
            
        raise UnsupportedShapesException(shape, line)

    @staticmethod
    def check_collision(shape1, position1, shape2, position2):
        """
        Returns True if the two given shapes (at their respective positions)
        are overlapping. Returns False otherwise.
        Raises an UnsupportedShapesException if collision detection between
        the given shapes is not supported.
        """
        
        # convert tuples to ogre.Vector3
        position1 = ogre.Vector3(position1[0], 0, position1[1])
        position2 = ogre.Vector3(position2[0], 0, position2[1])
        
        if shape1.type == "circle" and shape2.type == "linesegment":
            return CollisionDetector._check_circle_line(shape1, position1, shape2, position2) is not False
        elif shape1.type == "circle" and shape2.type == "circle":
            return CollisionDetector._check_circle_circle(shape1, position1, shape2, position2) is not False
        elif shape1.type == "circle" and shape2.type == "rectangle":
            return CollisionDetector._check_circle_rect(shape1, position1, shape2, position2) is not False
        elif shape1.type == "cone" and shape2.type == "circle":
            return CollisionDetector._check_cone_circle(shape1, position1, shape2, position2) is not False

        raise UnsupportedShapesException(shape1, shape2)
            
    @staticmethod
    def check_collision_and_resolve(shape1, position1, old_position1, shape2, position2):
        """
        Returns False if the two given shapes (at their respective positions)
        are not overlapping. Otherwise a tuple is returned representing the
        vector shape1 would have to move from position1 to no longer be
        overlapping with shape2 at position2.
        """
        # convert tuples to ogre.Vector3
        position1 = ogre.Vector3(position1[0], 0, position1[1])
        position2 = ogre.Vector3(position2[0], 0, position2[1])
        old_position1 = ogre.Vector3(old_position1[0], 0, old_position1[1])
        
        if shape1.type == "circle" and shape2.type == "linesegment":
            return CollisionDetector._resolve_circle_line(shape1, position1, shape2, position2)
        elif shape1.type == "circle" and shape2.type == "circle":
            return CollisionDetector._resolve_circle_circle(shape1, position1, shape2, position2)
        elif shape1.type == "circle" and shape2.type == "rectangle":
            return CollisionDetector._resolve_circle_rectangle(shape1, position1, old_position1, shape2, position2)
            
        raise UnsupportedShapesException(shape1, shape2)

    @staticmethod
    def _check_circle_line(circle, circle_position, line, line_position):
        """
        Checks to see if a BoundingCircle collides with a BoundingLineSegment.
        Returns a tuple containing the 'u' values of intersection points if collision occurred, False if not.
        The resulting tuple can contain either 1 or 2 elements.
        """
        
        # get the absolute position of the line segment vertices
        point1 = line_position
        point2 = line_position + line.vector

        # first transform the segment vertices to coordinates relative to the circle's center
        localP1 = ogre.Vector3(point1.x - circle_position.x, 0, point1.z - circle_position.z)
        localP2 = ogre.Vector3(point2.x - circle_position.x, 0, point2.z - circle_position.z)

        # pre-calculate p1-p2 for easy reference
        p2Minusp1 = ogre.Vector3(point2.x - point1.x, 0, point2.z - point1.z) # same as segment.vector?

        # get quadratic coefficients
        a = (p2Minusp1.x * p2Minusp1.x) + (p2Minusp1.z * p2Minusp1.z)
        b = 2 * ((p2Minusp1.x * localP1.x) + (p2Minusp1.z * localP1.z))
        c = (localP1.x * localP1.x) + (localP1.z * localP1.z) - (circle.radius * circle.radius)

        discrim = b * b - 4 * a * c

        if discrim < 0: # no collision
            return False
        elif discrim == 0: # perfect collision
            # u is the % of the distance from p1 to p2 the intersection point falls at
            u = -b / (2 * a)
            collisionPoint = ogre.Vector3(point1.x + u * p2Minusp1.x, 0, point1.z + u * p2Minusp1.z)
            if u < 0 or u > 1:
                return False   
            else:
                # now we're sure the collision is valid, so we'll return the collision point
                return u,
        elif discrim > 0: # collision with 2 intersection points
            u1 = (-b + math.sqrt(discrim)) / (2 * a)
            u2 = (-b - math.sqrt(discrim)) / (2 * a)

            # check to make sure the collision point falls between point1 and point2 on the line
            avg = (u1 + u2)/2
            if avg < 0 or avg > 1:
                return False
            
            # now we're sure the collision is valid, so we'll return the 2 collision points
            return (u1, u2)
        
    @staticmethod
    def _is_circle_intersecting_line(circle, circle_position, line, line_position):
        """
        Checks to see if a BoundingCircle collides with a BoundingLineSegment.
        Returns a tuple containing the 'u' values of intersection points if collision occurred, False if not.
        The resulting tuple can contain either 1 or 2 elements.
        """
        
        # get the absolute position of the line segment vertices
        point1 = line_position
        point2 = line_position + line.vector

        # first transform the segment vertices to coordinates relative to the circle's center
        localP1 = ogre.Vector3(point1.x - circle_position.x, 0, point1.z - circle_position.z)
        localP2 = ogre.Vector3(point2.x - circle_position.x, 0, point2.z - circle_position.z)

        # pre-calculate p1-p2 for easy reference
        p2Minusp1 = ogre.Vector3(point2.x - point1.x, 0, point2.z - point1.z) # same as segment.vector?

        # get quadratic coefficients
        a = (p2Minusp1.x * p2Minusp1.x) + (p2Minusp1.z * p2Minusp1.z)
        b = 2 * ((p2Minusp1.x * localP1.x) + (p2Minusp1.z * localP1.z))
        c = (localP1.x * localP1.x) + (localP1.z * localP1.z) - (circle.radius * circle.radius)

        discrim = b * b - 4 * a * c

        if discrim < 0: # no collision
            return False
        elif discrim == 0: # perfect collision
            # u is the % of the distance from p1 to p2 the intersection point falls at
            u = -b / (2 * a)
            collisionPoint = ogre.Vector3(point1.x + u * p2Minusp1.x, 0, point1.z + u * p2Minusp1.z)
            if u < 0 or u > 1:
                return False   
            else:
                # now we're sure the collision is valid, so we'll return True
                return True,
        elif discrim > 0: # collision with 2 intersection points
            u1 = (-b + math.sqrt(discrim)) / (2 * a)
            u2 = (-b - math.sqrt(discrim)) / (2 * a)

            if u1 > 0 and u1 < 1:
                return True
            if u2 > 0 and u2 < 1:
                return True
            return False

    @staticmethod
    def _check_circle_circle(circle1, circle1_position, circle2, circle2_position):
        """
        Checks if circle1 centered about circle1_position is overlapping with circle2
        centered about circle2_position. If there is no overlap, False is returned. If
        there is an overlap, True is returned.
        """
        
        # Calculate the distance between the center points of the two circles.
        distance = CollisionDetector._get_xz_distance(circle1_position, circle2_position)
        
        if distance > circle1.radius + circle2.radius:
            # If the distance is greater than the sum of the two circles' radii
            # then the circles are not overlapping and there is no collision.
            return False
        else:
            return True
        
    @staticmethod
    def _check_circle_rect(circle, circle_position_new, circle_position_old, rect, rect_position):
        """
        Checks collision between a circle and a rectangle. If a collision exists, it will return True.
        If a collision does not exist, it returns False.
        """
        # determine if circle is in voroni region or not, and if it is, determine which segment's voroni 
        segments = []       
        for side in rect.sides:
            axis_pos = CollisionDetector._get_position_on_axis(circle_position_old, side.normal, side.point1 + rect_position)
            if axis_pos >= 0:
                segments.append(side)
        if len(segments) == 0:
            raise Exception("Circle moved from inside the rectangle.")
        # if in voroni region...
        elif len(segments) == 1:
            # check for voroni region collision
            distance_to_edge = CollisionDetector._get_position_on_axis(circle_position_new, segments[0].normal, segments[0].point1 + rect_position)
            if distance_to_edge <= circle.radius:
                return True
            else:
                return False
        # else if not in voroni region, check for non-voroni region collision
        elif len(segments) == 2:
            # get the axis
            axis = circle_position_new - rect_position
            axis.normalise()
            
            # get the corner closest to the circle
            point1 = segments[0].point1 + rect_position
            point2 = segments[0].point1 + segments[0].vector + rect_position
            
            dp1 = CollisionDetector._get_position_on_axis(point1, axis, rect_position)
            dp2 = CollisionDetector._get_position_on_axis(point2, axis, rect_position)
            
            if dp1 > dp2:
                corner = point1
            else:
                corner = point2
                
            
            distance = CollisionDetector._get_xz_distance(circle_position_new, corner)
            
            # check for collision
            circle_edge_pos = distance - circle.radius
            if circle_edge_pos <= 0:
                # collision occurred
                return True
            else:
                return False
        
        return False  

    @staticmethod
    def _check_cone_circle(cone, cone_position, circle, circle_position):
        """
        Checks to see if a cone effect (actually represented by a circle sector)
        collides with a circle. Returns True on collision, False on no collision.
        """
        # first check to see if there is a circle collision
        distance = CollisionDetector._get_xz_distance(cone_position, circle_position)
        
        # if it's too far away to collide than we can return before doing any other calculations
        if distance > cone.radius:
            return False
        
        # now we need to check angles... first get the angle from conePos to pointToCheck
        theta = math.atan2(circle_position.z - cone_position.z, circle_position.x - cone_position.x)
        
        # get the max and min values of theta in order for a collision to occur
        min = cone.orientation - cone.width/2
        max = cone.orientation + cone.width/2
        
        # check to see if theta is in that range
        if min < theta and theta < max:
            # if so, collision
            return True
        else:
            # otherwise, no collision
            return False
        
    @staticmethod
    def _check_line_line(line1, line1_position, line2, line2_position):
        """
        Checks to see if the BoundingLineSegments line1 and line2 collide.
        Returns True on collision, False on no collision.
        """
        # a1 and a2 are the endpoints of line1
        a1 = line1_position
        a2 = line1_position + line1.vector

        # b1 and b2 are the endpoints of line2
        b1 = line2_position
        b2 = line2_position + line2.vector

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
    def _check_line_rect(line, line_position, rect, rect_position):
        """
        Determines whether or not a line segment intersects a rectangle.
        Returns True for collision, False for no collision.
        """ 
        # call check_line_line() on each side of rect
        for side in rect.sides:
            res = CollisionDetector._check_line_line(line, line_position, side, side.point1 + rect_position)
            if res == True:
                return True
        return False
    
    @staticmethod
    def _resolve_circle_line(circle, circle_position, line, line_position):
        """
        Returns the Resolution Translation Vector (RTV) that must be applied to the object that owns
        circle in order to resolve the collision, or False if no collision occurred.
        
        NOTE: THE RESOLUTION METHOD IS SLIGHTLY FLAWED, AND IS THE CAUSE OF THE FLICKERING EXPERIENCED
        WHEN RUNNING AGAINST A WALL. IN ORDER TO RESOLVE THIS COLLISION 100% CORRECTLY, THE ANGLE
        OF INCIDENCE MUST BE KNOWN. OTHERWISE, THE CURRENT IMPLEMENTATION MAY BE AN ACCEPTABLE
        APPROXIMATION.
        """
        # data is tuple of 'u' values which can be used to compute intersection points, or False
        data = CollisionDetector._check_circle_line(circle, circle_position, line, line_position)
        
        # no collision if data is False
        if data is False:
            return False
        
        # if there was a collision, so use the 'u' values to compute the RTV
        else:
            # calculate the endpoints of the line segment
            point1 = line_position
            point2 = line_position + line.vector
            
            # pre-calculate point1-point2 for easy reference
            p2Minusp1 = ogre.Vector3(point2.x - point1.x, 0, point2.z - point1.z)
            
            # now we have two cases: one or two points of intersection. For each case we must calculate the collision point.
            collisionPoint = None # initialize this here for scope
            
            # if there is one collision point
            if len(data) == 1:
                u = data[0]
                collisionPoint = ogre.Vector3(point1.x + u * p2Minusp1.x, 0, point1.z + u * p2Minusp1.z)
            # else if there are two collision points
            else:   
                # we calculate the two collision points (where the circle intersects the segment
                u1 = data[0]
                u2 = data[1]
                
                intersectionPoint1 = ogre.Vector3(point1.x + u1 * p2Minusp1.x, 0, point1.z + u1 * p2Minusp1.z)
                intersectionPoint2 = ogre.Vector3(point1.x + u2 * p2Minusp1.x, 0, point1.z + u2 * p2Minusp1.z)
    
                # find the point on the segment where the circle collided initially by taking the midpoint of the intersection points
                collisionPoint = intersectionPoint1.midPoint(intersectionPoint2)
    
            # the distance to place the center of the circle from the point of collision
            distance = circle.radius + CollisionDetector.SPACING

            # translate the circle's position along the segment's normal 'radius' units
            resolvedPosition = ogre.Vector3(collisionPoint.x + distance * line.normal.x, 0, collisionPoint.z + distance * line.normal.z)
            
            # get the relative translation vector to resolve the object's position
            # this vector is what the collider object must be translated by for the collision to be resolved correctly
            resolutionVector = (resolvedPosition.x - circle_position.x, resolvedPosition.z - circle_position.z)

            return resolutionVector
    
    @staticmethod
    def _resolve_circle_circle(circle1, circle1_position, circle2, circle2_position):
        """
        Returns the Resolution Translation Vector (RTV) that must be applied to the object that owns
        circle1 in order to resolve the collision, or False if no collision occurred.
        """
        # data is the RTV tuple or False
        data = CollisionDetector._check_circle_circle(circle1, circle1_position, circle2, circle2_position)
        
        # no collision occurred if data is False
        if data is False:
            return False      
        # if there was a collision, return the RTV tuple
        else:
            # Otherwise the circles are overlapping and we have collision and we
            # must calculate the resolution vector (how much to backtrack to not be
            # in collision).
          
            # Calculate the x and z differences between circle1 and circle2.
            dx = circle1_position.x - circle2_position.x
            dz = circle1_position.z - circle2_position.z
            
            # Calculate circle2's angle relative to circle1.
            theta = math.atan2(-dz, dx)
            
            # Calculate how far away we need to move the center of circle1 from the
            # center of circle2 overlapping with anymore.
            move_distance = circle1.radius + circle2.radius + CollisionDetector.SPACING
            
            # Calculate the point (absolute map coordinates) where we need to be
            # to not be overlapping.
            resolutionPoint = ogre.Vector3(circle2_position.x + move_distance * math.cos(theta),
                                           0,
                                           circle2_position.z + move_distance * -math.sin(theta))
            
            # Calculate the backtrack vector required used to move from our current
            # position to get to our resolution point (where we are no longer
            # overlapping).
            rtv = (resolutionPoint.x - circle1_position.x, resolutionPoint.z - circle1_position.z)
            
            # return our value
            return rtv
    
    @staticmethod
    def _get_position_on_axis(point, axis_vector, axis_vector_pos):
        """
        returns the scalar position of "point" along the axis specified by
        axis_vector originating from position axis_vector_pos
        
        the axis_vector does not need to be normalised before passing it to
        this function
        """
        axis_vector.normalise()
        point_vector = point - axis_vector_pos
        return point_vector.dotProduct(axis_vector)
    
    @staticmethod
    def _is_between_on_axis(point_to_check, endpoint_1, endpoint_2, axis_vector):
        """
        determines whether point_to_check lies between endpoint_1 and endpoint_2
        on an arbitrary axis defined by axis_vector
        """
        res_dp = _get_position_on_axis(point_to_check, axis_vector)
        res_ep1 = _get_position_on_axis(endpoint_1, axis_vector)
        res_ep2 = _get_position_on_axis(endpoint_2, axis_vector)
        
        return (res_dp > res_ep1 and res_dp < res_ep2) or (res_dp < res_ep1 and res_dp > res_ep2)
        
        
    @staticmethod
    def _resolve_circle_rectangle(circle, circle_position_new, circle_position_old, rect, rect_position):
        """
        Checks collision between a circle and a rectangle. If a collision exists, it will return the
        correction vector for the circle. If a collision does not exist, it returns False.
        """
        # determine if circle is in voroni region or not, and if it is, determine which segment's voroni 
        segments = []       
        for side in rect.sides:
            axis_pos = CollisionDetector._get_position_on_axis(circle_position_old, side.normal, side.point1 + rect_position)
            if axis_pos >= 0:
                segments.append(side)
        if len(segments) == 0:
            raise Exception("Circle moved from inside the rectangle.")
        # if in voroni region...
        elif len(segments) == 1:
            # calculate the rtv for this voroni region
            distance_to_edge = CollisionDetector._get_position_on_axis(circle_position_new, segments[0].normal, segments[0].point1 + rect_position)
            if distance_to_edge < circle.radius:
                # return the rtv
                rtv_magnitude = circle.radius - distance_to_edge
                rtv = segments[0].normal * (math.fabs(rtv_magnitude) + CollisionDetector.SPACING)
                res = circle_position_new + rtv            
                return  (rtv.x, rtv.z)
            
        # else if not in voroni region...
        elif len(segments) == 2:
            # get the axis
            axis = circle_position_new - rect_position
            axis.normalise()
            
            # get the corner closest to the circle
            point1 = segments[0].point1 + rect_position
            point2 = segments[0].point1 + segments[0].vector + rect_position
            
            dp1 = CollisionDetector._get_position_on_axis(point1, axis, rect_position)
            dp2 = CollisionDetector._get_position_on_axis(point2, axis, rect_position)
            
            if dp1 > dp2:
                corner = point1
            else:
                corner = point2
                
            
            distance = CollisionDetector._get_xz_distance(circle_position_new, corner)
            
            # check for collision
            circle_edge_pos = distance - circle.radius
            if circle_edge_pos <= 0:
                # collision occurred
                
                # calculate rtv
                rtv_axis = circle_position_new - corner
                rtv_axis.normalise()
                rtv_magnitude = -circle_edge_pos
                rtv_magnitude += CollisionDetector.SPACING
                rtv = rtv_axis * rtv_magnitude
                # return rtv as tuple
                return (rtv.x, rtv.z)
            else:
                return False
        
        return False  

    @staticmethod
    def _get_xz_distance(point1, point2):
        """
        Returns the distance between two ogre.Vector3 objects.
        """
        dx = point2.x - point1.x
        dz = point2.z - point1.z
        return math.sqrt(dx*dx + dz*dz)