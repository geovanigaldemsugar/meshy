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
            # convert viewport(width x height in pixel) to normalized world space 
            x, y, z = 2 * (mouse_x/self.scr_width) -1, 1 - 2 * (mouse_y/self.scr_height), -1
            ray_clip = np.array([x, y, z, 1], dtype=np.float32) # x, y, z, w
            ray_eye = np.linalg.inv(self.projection) @ ray_clip
            ray_eye = np.array([ray_eye[0], ray_eye[1], ray_eye[2], 0], dtype=np.float32)
            # ray_world = (np.linalg.inv(self.view) @ ray_eye)[:3]
            ray_world = (np.linalg.inv(self.view) @ ray_eye)
            ray_local = np.linalg.inv(self.model) @ ray_world
            # ray_world = (np.linalg.inv(self.view) @ np.linalg.inv(self.projection) @ ray_clip)[:3]
            # camera_origin_world = np.array([ray_world[0], ray_world[1], self.Camera.transform.position.vector()[2]], dtype=np.float32)

            # ray_world = (np.linalg.inv(self.view) @ np.linalg.inv(self.projection) @ ray_clip)[:3] # inv(PV) * clip_space and only keep x, y, z
            # ray_world = self.__normalize_vec(ray_world)        
            ray_local = self.__normalize_vec(ray_local)[:3]        

            # convert camera position from view space to world space inv(V) * view_space
            camera_origin_world = self.Camera.transform.position.vector()
            # camera_origin_world = np.array([ray_world[0], ray_world[1], self.Camera.transform.position.vector()[2]], dtype=np.float32)
            camera_origin_world = (np.linalg.inv(self.model) @ np.append(camera_origin_world, 0))[:3] # add w

            #convert Object center to world space, local_space * model_matrix
            sphere_center =  (np.linalg.inv(self.model) @ np.append(self.obj.transform.position.vector(), 0))[:3] # add w

            sphere_radius =  (np.linalg.inv(self.model) @ np.append(self.obj.transform.scale.vector(), 0))[:3] # add w
            sphere_radius = math.sqrt(sphere_radius[0]**2 +sphere_radius[1]**2 + sphere_radius[2]**2)/2


            
            # print(self.__ray_sphere_intersect(camera_origin_world, ray_world, sphere_center, sphere_radius))
            # print('camera_position:', self.Camera.transform.position.vector())
            # print('ray:', ray_world)
            # print('sphere center:', sphere_center)
            # print('sphere_radius', sphere_radius )
            print('mouse_on_object:', self.__ray_sphere_intersect(camera_origin_world, ray_local, sphere_center, sphere_radius))
           
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
