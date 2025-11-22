import pygame as pg
from OpenGL.GL import *
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from mesh import *
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

        while running:
            #check pygame events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

                self.__camera_ctl(event)
                self.__adjust_ratio(event)
                self.__object_ctl(event)
            
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
          
            if left_mouse == True:
                # Get the mouse position from the event object
                self.obj.transform.rotation.move(dy=-mouse_x, dx=-mouse_y)

                mod_keys = pg.key.get_mods()
                if pg.KMOD_CTRL & mod_keys: 
                    self.obj.transform.rotation.move(dz=-mouse_x)


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
        view = pyrr.matrix44.create_look_at(eye= self.Camera.transform.position.vector(), 
        target=self.Camera.transform.target.vector(), up=self.Camera.transform.world_up.vector(), dtype=np.float32)
        #update mat4 in gpu mem
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view)

    def __update_projection(self):
        # create projection matrix and bind data to gpu memory
        projection = pyrr.matrix44.create_perspective_projection_matrix(
        fovy=45, aspect=self.scr_width/self.scr_height, 
        near=0.1, far=self.render_distance, dtype=np.float32)
        
        # send the data to gpu variable
        glUniformMatrix4fv(self.ProjectionMatrixLocation, 1, GL_FALSE, projection)

    def __update_model(self):
        # create model matrix with T * R * S
        model = pyrr.matrix44.create_identity(dtype=np.float32)
        model = pyrr.matrix44.multiply(m1=model, m2=pyrr.matrix44.create_from_scale(scale=self.obj.transform.scale.vector(), dtype=np.float32))
        model = pyrr.matrix44.multiply(m1=model, m2=pyrr.matrix44.create_from_eulers(eulers=self.obj.transform.rotation.to_radians(), dtype=np.float32))
        model = pyrr.matrix44.multiply(m1=model,m2=pyrr.matrix44.create_from_translation(vec=self.obj.transform.position.vector(), dtype=np.float32))
        
        # update model matrix in gpu memory
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model)


    def quit(self):
        self.obj.destroy()
        glDeleteProgram(self.shader)    
        pg.quit()
     


if __name__ == "__main__":
    renderer = Renderer(Cube)
    renderer.renderLoop()
