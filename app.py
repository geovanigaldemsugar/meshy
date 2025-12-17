import pygame as pg
import numpy as np
import pyrr
import pygame as pg
import pygame_gui as pg_gui
from mesh import *
from OpenGL.GL import *
from camera import Camera
from OpenGL.GL.shaders import compileProgram, compileShader
from gui_test import UIInputStepper


class Renderer:
    
    def __init__(self, width:int=800, height:int=700):
        self.scr_width, self.scr_height = width, height
        self.render_distance = 20
        self.fov = 45
        self.mesh_mouse_hover = None
        self.mesh_focus = None
        self.ray = Ray(self, 0)
        self.gui_surface = pg.Surface((width, height), pg.SRCALPHA)
        

        #load objects
        # self._load_object("models/cube.obj")

        # initialize pygame and create window
        pg.init()
        self.win_surface = pg.display.set_mode((width, height), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
        self.clock = pg.time.Clock()
        self.pg_gui_manager = pg_gui.UIManager((self.scr_width, self.scr_height))
        self.time_delta = 0
        self.gui_surface = pg.Surface((width, height), pg.SRCALPHA)
        UIInputStepper(relative_rect=pg.Rect(50, 50, 200, 40), manager=self.pg_gui_manager, value=0)

      
        # initialize OpenGL
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.051, 0.067, 0.09, 1)
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        glUseProgram(self.shader)

        # initailize Camera and create view matrix
        self.camera = Camera()
        self.viewMatrixLocation = glGetUniformLocation(self.shader, 'view') # get view mat4 location in gpu mem
        self.__update_camera()

        # initialize and create projection matrix
        self.ProjectionMatrixLocation = glGetUniformLocation(self.shader, "projection")
        self.__update_projection()

        #initialize model and create model matrix 
        self.mesh_manager = MeshManager(self)
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        
    def renderLoop(self):
        running = True
        # self.mesh_manager.add_mesh(Sphere())
        self.mesh_manager.load_mesh("models/teapot.obj")
        mesh = self.mesh_manager.get_mesh(0) 
        mesh.transform.position.move(dx=0.0, dy=0.0, dz=-3)
        mesh.transform.rotation.move(dy=180, dx=90)
        
        # mesh.change_color(0.024, 0.969, 0.953)
        # (0.969, 0.573, 0.024) orange
        # mesh_2 = self.mesh_manager.get_mesh(1)
        # mesh_2.transform.position.move(dx=-0.34,dy=0.0, dz=-3)
        # mesh_2.change_color(0.549, 0.024, 0.969)
        
        self.__update_model()

        while running:
            #check pygame events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                self.__camera_ctl(event)
                self.__adjust_ratio(event)
                self.__mouse_picking(event)
                self.__object_ctl(event)
                self.pg_gui_manager.process_events(event)
            
            # refresh screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Rendering code would go here
            glUseProgram(self.shader)

            #rotate cube
            # self.obj.transform.rotation.move(dz=1)
            # self.obj.transform.position.bounce(dy=0.01)
            # self.obj.transform.scale.bounce(dx=0.001)
            
            #update model matrices and draw meshes
            self.__update_model()

            self.pg_gui_manager.update(self.time_delta)
            self.win_surface.blit(self.gui_surface, (0, 0))

            self.pg_gui_manager.draw_ui(self.win_surface)
            # self.gui_surface.fill((0, 0, 0, 0)) 
            # self.pg_gui_manager.draw_ui(self.gui_surface)
            # flip the buffers
            pg.display.flip()
        
            # frame rate limit
            self.time_delta = self.clock.tick(60)/1000

            
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
        """control objects on screen"""

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.mesh_mouse_hover != None:
                    if self.mesh_focus != self.mesh_mouse_hover and self.mesh_focus != None:
                        self.mesh_focus.highlight.enable = False
                        
                    self.mesh_focus = self.mesh_mouse_hover
                    self.mesh_focus.highlight.enable = True

        if event.type == pg.MOUSEMOTION and self.mesh_focus != None:
            left, middle, right = event.buttons

            # Get the mouse position from the event object
            mouse_x, mouse_y = event.rel
            self.mesh_focus.transform.rotation.move(dy=-mouse_x, dx=-mouse_y)
            modKeys = pg.key.get_mods()
            shiftKey = pg.KMOD_LSHIFT & modKeys
            # self.camera.transform.move(0, mouse_y, mouse_x, sensitivity = 0.45)
            # self.__update_camera()

            if shiftKey:
                mouse_x_abs, mouse_y_abs = event.pos
                z = self.mesh_focus.transform.position.z
                x_pos = self.mesh_focus.transform.position.x
                x, y = 2 * (mouse_x_abs/self.scr_width)-1, 1 - 2 * (mouse_y_abs/self.scr_height)
                clip = np.linalg.inv(self.projection) @ np.array([x,y,-1, 1], dtype=np.float32)
                world = np.linalg.inv(self.view) @ clip
                # if world[3] != 0:
                #     world = world / world[3]
                
                self.mesh_focus.transform.position.update(x=world[0], y=world[1], z=z)

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_w:
                for mesh in self.mesh_manager.meshes:
                    mesh.wireframe.enable = not mesh.wireframe.enable
                    mesh.enable = not mesh.enable
        
            if event.key == pg.K_ESCAPE and self.mesh_focus != None:
                self.mesh_focus.highlight.enable = False
                self.mesh_focus = None

    def __camera_ctl(self, event):
        if event.type == pg.MOUSEWHEEL:
            self.camera.transform.zoom(event.y, zoom_speed=0.2)
            self.__update_camera()
          
        if event.type == pg.MOUSEMOTION:
            left, middle, right = event.buttons
            mouse_x, mouse_y = event.rel 
       
            modKeys = pg.key.get_mods()
            shiftKey = pg.KMOD_LSHIFT & modKeys
            

            if middle and not shiftKey:
                # move camera with blender style orbit
                self.camera.transform.move(0, mouse_y, mouse_x, sensitivity = 0.2)
                self.__update_camera()
           
            if middle and shiftKey:
                # move view/target by panning
                self.camera.transform.pan_camera(mouse_x, mouse_y, pan_speed=0.002)
                self.__update_camera()

                
    def __update_camera(self):
        # create view matrix with updated camera target
        view = self.camera.view_matrix()

        #update view matrix in gpu mem
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view)

    def __update_projection(self):
        # create projection matrix and bind data to gpu memory
        self.projection = pyrr.matrix44.create_perspective_projection_matrix(
        fovy=self.fov, aspect=self.scr_width/self.scr_height, 
        near=0.1, far=self.render_distance, dtype=np.float32)
        
        # send the data to gpu variable
        glUniformMatrix4fv(self.ProjectionMatrixLocation, 1, GL_FALSE, self.projection)

    def __update_model(self):
        """update model matrix for all meshes and draw them"""
        for mesh in self.mesh_manager.meshes:
            model = mesh.create_model_matrix()
            # update model matrix in gpu memory
            glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model)
            mesh.draw()

       
    def __mouse_picking(self, event):
        if not event.type == pg.MOUSEMOTION:
            return None

        mouse_x, mouse_y = event.pos
        self.mesh_manager.hit_manager.draw_rays(mouse_x, mouse_y)

        id, hit, dist = self.mesh_manager.hit_manager.get_hit()
        self.mesh_mouse_hover = self.mesh_manager.get_mesh(id)
       
    
    def quit(self):
        self.mesh_manager.destroy_meshes()
        glDeleteProgram(self.shader)    
        pg.quit()
     


if __name__ == "__main__":
    renderer = Renderer()
    renderer.renderLoop()