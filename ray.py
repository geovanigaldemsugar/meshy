from app import Renderer
import numpy as np
import math


class Ray:
    def __init__(self, renderer:Renderer):
        self.renderer = renderer
        
    def gen_ray(self, mouse_x:float, mouse_y:float):
        """generates a ray direction towards target  from screen given (mouse_x, mouse_y)"""
        # convert viewport(width x height in pixel) to normalized device coordinates
        x, y = 2 * (mouse_x/self.renderer.scr_width) -1, 1 - 2 * (mouse_y/self.renderer.scr_height)
        # calculate ray x, y in view/cam space 
        # Tan(fov/2) defines y component of the ray that streches off course due to perspective and hit z =-1
        # if 1 * Tan(fov/2) = full height of screen
        # aspect = is the relation bewteen x and y a = x/y,  a = width/height, eg a =1.77 so x is 1.77 * greater than y
        
        #calculate ray direction in camera space (where where will land in camera/view space after applying perspective)
        stretch = math.tan(math.radians(self.renderer.fov)/2)
        aspect_ratio =  self.renderer.scr_width/self.renderer.scr_height
        x_view = x * aspect_ratio * stretch
        y_view = y * stretch
        z_view = -1 # camera looks towards -z in local space
        ray_dir_view = np.array([x_view, y_view, z_view], dtype=np.float32)
        ray_dir_view = self.normalize_vec(ray_dir_view) #because of stretching the once nornmialized coordinated become unnormalized
        
        cam_pos = self.renderer.camera.transform.position.vector()
        target = self.renderer.camera.transform.target.vector()
        world_up = self.renderer.camera.transform.world_up.vector()

        #build camera basis vectors in world space
        #camera is look at ray_dir, = T - C
        forward = self.normalize_vec(target - cam_pos) 
        right = self.normalize_vec(np.cross(forward, world_up))
        up = self.normalize_vec(np.cross(right, forward))

        # map camera space ray (ray_view) to world_space
        #we account for camera oreintation/rotation in space since it changes
        #ray no longer shoot to directly z = -1, its the same as were creating a look at ray
        #where R(t) = O + Dt, where D = (T - C)<basis vector-x> * ray_view<x> + (basis vector-y) * ray_view-y...
        ray_dir_world = (right * ray_dir_view[0] + up * ray_dir_view[1] + forward * (-ray_dir_view[2]))
        ray_dir_world = self.normalize_vec(ray_dir_world)

        #ray origin is the camera
        ray_origin = cam_pos

        return ray_dir_world, ray_origin



    def ray_sphere_intersect(self, ray_O: np.ndarray, ray_D: np.ndarray, sphere_C: np.ndarray, sphere_r:float):
        """O - ray origin, D - ray direction, C - sphere center, r - sphere radius"""
        # t = - b +- sqrt(b**2 - c)    decriminant = b**2 - c
        # b = D dot (O - C)
        # c = (O - C) dot (O - C) - r**2
        # ray origin is the camera

        b = ray_D @ (ray_O - sphere_C)
        c = (ray_O - sphere_C) @ (ray_O - sphere_C) - sphere_r**2
        decriminant = b**2 - c
        
        if decriminant < 0:
            return False, float('inf')
        if decriminant == 0:
            t = -b + np.sqrt(decriminant)
            return True, t
        if decriminant > 0:
            t1 = -b + np.sqrt(decriminant)
            return True, t1
        

        
    def normalize_vec(self, vector:np.ndarray):
        vec_magnitude =  np.linalg.norm(vector) 
        if vec_magnitude < 1e-6:
            return np.array([0, 0, 0], dtype=np.float32)
        vector = vector / vec_magnitude
        return vector


