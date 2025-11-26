import numpy as np
import math

class Vector:
    """ Base class for creating Transformation Obejects """
    def __init__(self, x:float=1.0, y:float=1.0, z:float=1.0):
        self.x = x
        self.y = y
        self.z = z

    def update(self, x:float, y:float, z:float):
        """ Reset Vector to new  (x, y, z)"""
        self.x = x
        self.y = y
        self.z = z
    
    def move(self,dx:float=0.0, dy:float=0.0, dz:float=0.0):
        """ Move Axes by given deltas (dx, dy, dz) """
        self.x += dx
        self.y += dy
        self.z += dz

    def bounce(self, dx:float=0.0, dy:float=0.0, dz:float=0.0, min=-0.5, max=0.5):
        """Move an Object Axes between min and max by given deltas (dx, dy, dz)"""
        if not hasattr(self, "up"):
            self.up = [True, True, True]
            self.d_total = [0, 0, 0]

        if self.up[0]:
            if self.d_total[0] < max:
                self.d_total[0] += dx
                self.move(dx=dx)
        else:
            if self.d_total[0] > min:
                self.d_total[0] -= dx
                self.move(dx=-dx)

        if self.up[1]:
            if self.d_total[1] < max:
                self.d_total[1] += dy
                self.move(dy=dy)
        else:
            if self.d_total[1] > min:
                self.d_total[1] -= dy
                self.move(dy=-dy)
            
        if self.up[2]:
            if self.d_total[2] < max:
                self.d_total[2] += dz
                self.move(dz=dz)
        else:
            if self.d_total[2] > min:
                self.d_total[2] -= dz
                self.move(dz=-dz)
 
        for total, i in zip(self.d_total, range(3)):
            if total >= max:
                self.up[i] = False
            if total <= min:
                self.up[i] = True

    def vector(self):
        """return numpy array"""
        return np.array([self.x, self.y, self.z], dtype=np.float32)
    
    def __clamp(self, value,  min_l, max_l):
        """ clamp value withing specified range"""
        return max(min_l, min(value, max_l))



class Scale(Vector):
    """Defines the size of an object relative to the 3D space"""
    def __init__(self, x:float=1.0, y:float=1.0, z:float=1.0):
        super().__init__(x, y, z)


class Euler(Vector):
    """Defines the orientation of an object in 3D space"""

    def __init__(self, x:float=0.0, y:float=0.0, z:float=0.0):
        super().__init__(x, y, z)
    

    def to_radians(self):
        return np.radians([self.x, self.y, self.z], dtype=np.float32)
    

class Position(Vector):
    """Defines the position of an object relative to the 3D space"""
    def __init__(self, x:float=0.0, y:float=0.0, z:float=0.0):
        super().__init__(x, y, z)

    
    
class Transform:
    """Defines an Object Transformation (Position, Rotation, Scale) in 3D Space"""
    def __init__(self):
        self.position:Position = Position(0.0, 0.0, 0.0)
        self.rotation:Euler = Euler(0.0, 0.0, 0.0)
        self.scale:Scale = Scale(0.2, 0.2, 0.2)



class OrbitalTransfrom:
    """Defines Camera Orbital Transform in 3D Space"""

    def __init__(self, r:float , pitch, yaw):
        self.r = r
        self.pitch = pitch
        self.yaw = yaw

        # Initialize vectors
        self.target = Vector(0, 0, 0)
        self.world_up = Vector(0, 1, 0)
        self.position = Position(0, 0, 0)

        # Set Camera in Orbital Position
        self.__update_orbit()

    def update(self, x, y, z):
        """Set new target vector (changes what camera is viewing)"""
        self.target.update(x, y, z)
        self.__update_orbit()

    def move(self, dr=0, dpitch=0, dyaw=0, sensitivity=0.2):
        """move Camera up and down, left or right, closer or farther by given (dr, dpitch, dyaw)"""
        self.r += dr * sensitivity
        self.pitch += dpitch * sensitivity
        self.yaw += dyaw * sensitivity

        # Set limits for pitch (0-90°) and r(distance), and warp yaw(360 -> 0)
        self.pitch = self.__clamp(self.pitch, 1, 89)
        self.yaw = self.__warp_angle(self.yaw)
        self.r = self.__clamp(self.r, 0.1, 20)

        # recalculate orbit
        self.__update_orbit()
        # print(self.pitch, ' ', self.yaw)
        # print(self.position.vector(), ' ', self.target.vector())
        

    def pan_camera(self, dx=0 ,dy=0, pan_speed=0.005):
        """Move Camera Target by given (dx, dy), this moves the world up or down, left or right"""
        foward = self.__normalize_vec(self.target.vector() - self.position.vector())
        right = self.__normalize_vec(np.cross(foward, self.world_up.vector()))
        up = self.__normalize_vec(np.cross(right, foward))

        translate = (-right * dx + up * dy) * pan_speed * self.r

        self.target.move(translate[0], translate[1])
        self.target.move(translate[0], translate[1])
        self.__update_orbit()

        # dx *= pan_speed
        # dy *= pan_speed

        # self.target.move(dx, dy)
        # self.position.move(dx, dy)

        # self.__update_orbit()

    def zoom(self, dr, zoom_speed):
        """Move camera closer or farther away by given (dr)"""
        self.move(-dr, sensitivity=zoom_speed)
    
    def __update_orbit(self):
        """Calculate and set Camera's Orbital position"""
        pitch, yaw = self.to_rads()

        x = self.target.x + self.r * math.cos(pitch) * math.sin(yaw)
        y = self.target.y + self.r * math.sin(pitch)
        z = self.target.z + self.r * math.cos(pitch) * math.cos(yaw)

        # update position with new spherical coordinate
        self.position.update(x, y, z)
    
    def to_rads(self):
        """Converts pitch and yaw to Radians """
        return math.radians(self.pitch), math.radians(self.yaw)
    
    def __clamp(self, value,  min_l, max_l):
        """ clamp value withing specified range"""
        return max(min_l, min(value, max_l))
    
    def __warp_angle(self, value):
        """Warps angle to between 360 -> 0"""
        return (value % 360 + 360) % 360  
    
    def __normalize_vec(self, vector):
        """strip  a vector of it magnitude and leave only direction"""
        vec_magnitude =  np.linalg.norm(vector) 
        if vec_magnitude < 1e-6:
            return np.array([0, 0, 0], dtype=np.float32)
        vector = vector / vec_magnitude
        return vector






    # calculate Camera postion with target as origin
    # x = self.target.x + math.sin(yaw) * math.sin(pitch) * self.r
    # y = self.target.y + math.cos(pitch) * self.r
    # z = self.target.z + math.cos(yaw) * math.sin(pitch) * self.r
