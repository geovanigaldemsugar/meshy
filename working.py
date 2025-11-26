import pygame as pg
from OpenGL.GL import *
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from mesh import *
from line import *
import math

class Renderer:
    
    def __init__(self, obj:Mesh, width:int=800, height:int=700):
        self.scr_width, self.scr_height = width, height
        self.render_distance = 20
        
        # initialize pygame and create window
        pg.init()
        pg.display.set_mode((width, height), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
        self.clock = pg.time.Clock()
      
        # initialize OpenGL
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.051, 0.067, 0.09, 1)
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        glUseProgram(self.shader)

        # initailize Camera and create view matrix
        self.Camera = Camera()
        self.viewMatrixLocation = glGetUniformLocation(self.shader, 'view') # get view mat4 location in gpu mem
        self.__update_camera()

        # initialize and create projection matrix
        self.ProjectionMatrixLocation = glGetUniformLocation(self.shader, "projection")
        self.__update_projection()

        #initialize model and create model matrix 
        self.obj = obj
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        
    def renderLoop(self):
        running = True
        self.obj = self.obj()
        self.__update_model()

        while running:
            #check pygame events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

                self.__camera_ctl(event)
                self.__adjust_ratio(event)
                self.__object_ctl(event)
                self.__draw_ray(event)
            
            # refresh screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Rendering code would go here
            glUseProgram(self.shader)

            #rotate cube
            # self.obj.transform.rotation.move(dz=1)
            # self.obj.transform.position.bounce(dy=0.01)
            self.__update_model()

            # draw the shape
            self.obj.draw()

            # flip the buffers
            pg.display.flip()
        
            # frame rate limit
            self.clock.tick(60)
        
        #exit program
        self.quit() 
        
    def createShader(self, vertexFilepath, fragmentFilepath):
        with open(vertexFilepath, 'r') as f:
            vertex_src = f.readlines()
        
        with open(fragmentFilepath, 'r') as f:
            fragment_src = f.readlines()

        shader = compileProgram(
                  compileShader(vertex_src, GL_VERTEX_SHADER),
                  compileShader(fragment_src, GL_FRAGMENT_SHADER)
       )   
        
        return shader   

    def __adjust_ratio(self, event):
            """on Window Resize event adjust aspect ratio"""
            if event.type == pg.VIDEORESIZE:
                self.scr_width, self.scr_height  = pg.display.get_window_size()
                self.__update_projection()

    def __object_ctl(self, event):
        if event.type == pg.MOUSEMOTION:
            left_mouse, middle_mouse, right_mouse = pg.mouse.get_pressed(num_buttons=3)
            mouse_x, mouse_y = event.rel 
          
            if left_mouse:
                # Get the mouse position from the event object
                self.obj.transform.rotation.move(dy=-mouse_x, dx=-mouse_y)

                mod_keys = pg.key.get_mods()
                if pg.KMOD_CTRL & mod_keys: 
                    self.obj.transform.rotation.move(dz=-mouse_x)
        if event.type == pg.MOUSEBUTTONDOWN:
            left_mouse, middle_mouse, right_mouse = pg.mouse.get_pressed(num_buttons=3)
            if right_mouse:
                self.obj.enable = not self.obj.enable 

    def __camera_ctl(self, event):
        if event.type == pg.MOUSEWHEEL:
            self.Camera.transform.zoom(event.y, zoom_speed=0.2)
            self.__update_camera()
          
        if event.type == pg.MOUSEMOTION:
            left_mouse, middle_mouse, right_mouse = pg.mouse.get_pressed(num_buttons=3)
            mouse_x, mouse_y = event.rel 
       
            modKeys = pg.key.get_mods()
            shiftKey = pg.KMOD_LSHIFT & modKeys

            if middle_mouse and not shiftKey:
                # move camera with blender style orbit
                self.Camera.transform.move(0, mouse_y, mouse_x, sensitivity = 0.2)
                self.__update_camera()
           
            if  middle_mouse and shiftKey:
                # move view/target by panning
                self.Camera.transform.pan_camera(mouse_x, mouse_y, pan_speed=0.002)
                self.__update_camera()

                
    def __update_camera(self):
        # create view matrix with updated camera target
        self.view = pyrr.matrix44.create_look_at(eye= self.Camera.transform.position.vector(), 
        target=self.Camera.transform.target.vector(), up=self.Camera.transform.world_up.vector(), dtype=np.float32)
        #update mat4 in gpu mem
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, self.view)

    def __update_projection(self):
        # create projection matrix and bind data to gpu memory
        self.projection = pyrr.matrix44.create_perspective_projection_matrix(
        fovy=45, aspect=self.scr_width/self.scr_height, 
        near=0.1, far=self.render_distance, dtype=np.float32)
        
        # send the data to gpu variable
        glUniformMatrix4fv(self.ProjectionMatrixLocation, 1, GL_FALSE, self.projection)

    def __update_model(self):
        # create model matrix with T * R * S
        self.model = pyrr.matrix44.create_identity(dtype=np.float32)
        self.model = pyrr.matrix44.multiply(m1=self.model, m2=pyrr.matrix44.create_from_scale(scale=self.obj.transform.scale.vector(), dtype=np.float32))
        self.model = pyrr.matrix44.multiply(m1=self.model, m2=pyrr.matrix44.create_from_eulers(eulers=self.obj.transform.rotation.to_radians(), dtype=np.float32))
        self.model = pyrr.matrix44.multiply(m1=self.model,m2=pyrr.matrix44.create_from_translation(vec=self.obj.transform.position.vector(), dtype=np.float32))
        
        # update model matrix in gpu memory
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, self.model)

    def __draw_ray(self, event):
        if event.type == pg.MOUSEMOTION:
            mouse_x, mouse_y = event.pos

            # 1. Screen space -> Normalized Device Coordinates (NDC)
            x = 2.0 * (mouse_x / self.scr_width) - 1.0
            y = 1.0 - 2.0 * (mouse_y / self.scr_height)

            # 2. Compute ray in camera space using FOV and aspect ratio
            fovy_deg = 45.0  # keep in sync with __update_projection
            fovy_rad = math.radians(fovy_deg)
            tan_fovy = math.tan(fovy_rad / 2.0)
            aspect = self.scr_width / self.scr_height

            x_cam = x * aspect * tan_fovy
            y_cam = y * tan_fovy
            z_cam = -1.0  # camera looks down -Z in its local space

            ray_dir_cam = np.array([x_cam, y_cam, z_cam], dtype=np.float32)
            ray_dir_cam = self.__normalize_vec(ray_dir_cam)

            # 3. Build camera basis in world space
            cam_pos = self.Camera.transform.position.vector()
            target = self.Camera.transform.target.vector()
            world_up = self.Camera.transform.world_up.vector()

            forward = self.__normalize_vec(target - cam_pos)
            right = self.__normalize_vec(np.cross(forward, world_up))
            up = self.__normalize_vec(np.cross(right, forward))

            # Map camera-space ray to world space
            # (-z_cam) because camera looks along -Z in its local space
            ray_dir_world = (
                right * ray_dir_cam[0]
                + up * ray_dir_cam[1]
                + forward * (-ray_dir_cam[2])
            )
            ray_dir_world = self.__normalize_vec(ray_dir_world)

            ray_origin_world = cam_pos

            # 4. Sphere center & radius in world space
            sphere_center_world = self.obj.transform.position.vector()

            # Approximate a radius based on scale (diagonal of scaled box / 2)
            scale_vec = self.obj.transform.scale.vector()
            sphere_radius_world = math.sqrt(
                scale_vec[0] ** 2 + scale_vec[1] ** 2 + scale_vec[2] ** 2
            ) / 2.0

            hit = self.__ray_sphere_intersect(
                ray_origin_world,
                ray_dir_world,
                sphere_center_world,
                sphere_radius_world,
            )

            print("mouse_on_object:", hit)
           
    def __ray_sphere_intersect(self, ray_O: np.ndarray, ray_D: np.ndarray, sphere_C: np.ndarray, sphere_r:float):
        """O - ray origin, D - ray direction, C - sphere center, r - sphere radius"""
        # t = - b +- sqrt(b**2 - c)    decriminant = b**2 - c
        # b = D dot (O - C)
        # c = (O - C) dot (O - C) - r**2


        b = ray_D @ (ray_O - sphere_C)
        c = (ray_O - sphere_C) @ (ray_O - sphere_C) - sphere_r**2
        decriminant = b**2 - c
        
        if decriminant < 0:
            return False
        if decriminant > 0:
            return True
        if decriminant == 0:
            return True
    
     
    def __normalize_vec(self, vector:np.ndarray):
        vec_magnitude =  np.linalg.norm(vector) 
        if vec_magnitude < 1e-6:
            return np.array([0, 0, 0], dtype=np.float32)
        vector = vector / vec_magnitude
        return vector
    def quit(self):
        self.obj.destroy()
        glDeleteProgram(self.shader)    
        pg.quit()
     


if __name__ == "__main__":
    renderer = Renderer(Cube)
    renderer.renderLoop()
