from OpenGL.GL import *
from OpenGL.constant import IntConstant
import numpy as np
from vector import Transform, OrbitalTransfrom
from app import Renderer
from  ray import *


class Mesh:
    """ Base class for Creating Object Meshes using Index Buffer Object(EBO) """

    def __init__(self, vertices:np.ndarray, indices:np.ndarray, mode:IntConstant=GL_TRIANGLES, line:float=1):
        self.transform:Transform = Transform()
        self.vertices = vertices
        self.indices = indices
        self.indices_count = len(self.indices)
        self.mode = mode
        self.line = line
        self.vpos = None

        # will be initialized by Mesh Manager
        self.id = None
        self.hit = None, None
        self.renderer = None
        self.ray:Ray = None

        #set line thickness if drawing lines
        glLineWidth(self.line)

        # create Vertex Attribute Object (VAO)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # create Vertex Buffer Object (VBO)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # create Element Buffer Object (EBO)
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        #specify the layout of the vertex data for the shader
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        # Unbind - frees Opengl Context
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


    def draw_ray_to_mesh(self, mouse_x:float, mouse_y:float):
        ray_dir, ray_origin = self.ray.gen_ray(mouse_x, mouse_y)
        sphere_r, sphere_center = self.gen_bounding_sphere()
        self.hit = self.ray.ray_sphere_intersect(ray_origin, ray_dir, sphere_center, sphere_r)
        
   
    def gen_bounding_sphere(self) -> tuple[float, np.ndarray]:
        """Generates a bounding sphere for object, returns (radius, sphere_center) """
        # prepare sphere center and radius in world space

        # Calculate xmax, ymax, zmax for axis aligned bounding box sphere
        max_xyz =  self.vertices[:, 0:3].max(axis=0)
        xmax, ymax, zmax = max_xyz[0], max_xyz[1], max_xyz[2]  

        sphere_C =self.transform.position.vector()
        scale_vec = self.transform.scale.vector()
        sphere_r = np.sqrt(
            (xmax * scale_vec[0]) ** 2 + (ymax * scale_vec[1]) ** 2 + (zmax * scale_vec[2]) ** 2
        )
        return sphere_r, sphere_C
    
    def change_color(self, r, g, b):
        # rgb 
        rgb = self.vertices[:,3:6] 
        rgb[:,0] = r
        rgb[:,1] = g
        rgb[:,2] = b
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)


    def draw(self):
        """ Draw Mesh using glDrawElements """
        glBindVertexArray(self.vao)
        # Draw primitive/triangles using indices specified in the EBO
        glDrawElements(self.mode, self.indices_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))


    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))
        glDeleteBuffers(1, (self.ebo,))
    

class MeshManager:
    def __init__(self, renderer):
        self.meshes:list[Mesh] = []
        self.renderer:Renderer = renderer
        self.hit_manager:HitManager = HitManager(self.meshes)
        # initialize id generator
        self.gen_id = self._id_generator()
    
    def add_mesh(self, *args:Mesh):
        for arg in args:
            arg.id = next(self.gen_id)
            arg.renderer = self.renderer
            arg.ray = Ray(self.renderer, arg.id)
            self.meshes.append(arg)
   
        # update hit manager
        self.hit_manager.meshes = self.meshes

    def mesh_ids(self):
        return [mesh.id for mesh in self.meshes]
    
    def destroy_meshes(self):
        for mesh in self.meshes:
            mesh.destroy()

    def get_mesh(self, id) -> Mesh:
        for mesh in self.meshes:
            if id == mesh.id:
                return mesh
        return None
    
    def _id_generator(self):
        id = 0
        while True:
            yield id
            id += 1


class Square(Mesh):
    """Square Mesh"""

    def __init__(self):
        # square has 4 unique vertices
        vertices = (
            # Position (x,y,z)    Color (r,g,b)
            (-0.5, -0.5,  0.5), (1.0, 0.0, 0.0), #0 - Front-Bottom-Left
            ( 0.5, -0.5,  0.5), (0.0, 1.0, 0.0), #1 - Front-Bottom-Right
            ( 0.5,  0.5,  0.5), (0.0, 0.0, 1.0), #2 - Front-Top-Right
            (-0.5,  0.5,  0.5), (1.0, 1.0, 0.0), #3 - Front-Top-Left
            
        )

        # 2 traingles make a square each traingle has 3 vertices, 3 * 2 = 6 indices
        indices = (
            0, 1, 2,  2, 3, 0,
        )

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        super().__init__(self.vertices, self.indices)
  
        self.transform.position.update(0.0, 0.0, -3.0)



class Pyramid(Mesh):
    """Square Pyramid Mesh"""
    def __init__(self):
        vertices = (
              # Position              Color
             (-0.5, -0.5,  0.5,   1.0, 0.0, 0.0),  #0 - right-bottom-front
             (0.5, -0.5,  0.5,    0.0, 1.0, 0.0),  #1 - left-bottom-front
             (0,    0.5,    0,    0.0, 0.0, 1.0),  #2 - apex
             (-0.5, -0.5, -0.5,   1.0, 0.0, 0.0),  #3 - left-bottom-back
             (0.5, -0.5, -0.5,    0.0, 1.0, 0.0)  #4 - right-bottom-back
            )

        indices = (
            # Front
            0, 1, 2,
            # Right
            1, 4, 2,
            # Left
            0, 2, 3,
            # Bottom
            0, 1, 4,  4, 3, 0
        )
        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.enable_highlight =False
        self.highlight = Highlight(self.vertices, self.indices)

        super().__init__(self.vertices, self.indices)
        self.transform.position.update(0.0, 0.0, -3.0)
    
    def draw(self):
        self.highlight.transform = self.transform
        if self.enable_highlight:
            self.highlight.draw()
            
        super().draw()

class Cube(Mesh):
    """Cube Mesh"""
    def __init__(self):

        # Cube has 8 unique vertices 
        vertices = [
            # Position (x,y,z)    Color (r,g,b)
            (-0.5, -0.5,  0.5,   1.0, 0.0, 0.0), #0 - Front-Bottom-Left
            (0.5, -0.5,  0.5,    0.0, 1.0, 0.0), #1 - Front-Bottom-Right
            (0.5,  0.5,  0.5,    0.0, 0.0, 1.0), #2 - Front-Top-Right
            (-0.5,  0.5,  0.5,   1.0, 1.0, 0.0), #3 - Front-Top-Left
            (-0.5, -0.5, -0.5,   1.0, 0.0, 0.0), #4 - Back-Bottom-Left
            (0.5, -0.5, -0.5,    0.0, 1.0, 0.0), #5 - Back-Bottom-Right
            (0.5,  0.5, -0.5,    0.0, 0.0, 1.0), #6 - Back-Top-Right
            (-0.5,  0.5, -0.5,   1.0, 1.0, 0.0) #7 - Back-Top-Left
        ]

        # cube has 6 faces, 6 * 2(traingle per face) = 12 traingles, each traingle has 3 vertex  12 *3 = 36 indicies
        indices = (
            # Front
            0, 1, 2,  2, 3, 0,
            # Right
            1, 5, 6,  6, 2, 1,
            # Back
            7, 6, 5,  5, 4, 7,
            # Left
            4, 0, 3,  3, 7, 4,
            # Top
            3, 2, 6,  6, 7, 3,
            # Bottom
            4, 5, 1,  1, 0, 4
        )

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.enable_highlight =False
        self.highlight = Highlight(self.vertices, self.indices)

        super().__init__(self.vertices, self.indices)
        self.transform.position.update(0.0, 0.0, -3.0)
    
    def draw(self):
        self.highlight.transform = self.transform
        if self.enable_highlight:
            self.highlight.draw()
            
        super().draw()

    def destroy(self):
        self.highlight.destroy()
        super().destroy()



class MeshWireFrame(Mesh):
    def __init__(self, vertices, indices):
        indices = self.__create_outline(indices)
        mode = GL_LINES
        line = 1
        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.change_color(1, 0.647, 0)
        super().__init__(self.vertices, self.indices, mode, line)
        
    def __create_outline(self, indices):
        outline = []
        for i in range(0, len(indices), 3):
            # get every three indices that create a quad for the object
            triangle = indices[i:i+3]  # eg 0,1 2
            # create a pair of perpendicular lines instead of the triangle
            lines = triangle[0], triangle[1], triangle[1], triangle[2]
            outline.extend(lines)
            
        return outline
    


class Highlight(Mesh):
    def __init__(self, vertices, indices):
        indices = self.__create_outline(indices)
        mode = GL_LINES
        line = 1
        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.change_color(1, 0.647, 0)
        super().__init__(self.vertices, self.indices, mode, line)
        self.transform.scale.move(0.5, 0.5, 0.5)

    def __create_outline(self, indices):
        outline = []
        for i in range(0, len(indices), 3):
            # get every three indices that create a quad for the object
            triangle = indices[i:i+3]  # eg 0,1 2
            # create a pair of perpendicular lines instead of the triangle
            lines = triangle[0], triangle[1], triangle[1], triangle[2]
            outline.extend(lines)
            
        return outline
  

    def change_color(self, r, g, b):
        # rgb 
        rgb = self.vertices[:,3:6] 
        rgb[:,0] = r
        rgb[:,1] = g
        rgb[:,2] = b



class Camera():
    """Camera Object"""
    def __init__(self):
        self.transform = OrbitalTransfrom(r = 1, pitch=1, yaw=0)
        self.transform.update(0, 0, -3)
    

class Sphere(Mesh):
    """Sphere Mesh using UV Sphere generation and EBO"""

    def __init__(self, radius=0.5, stacks=40, slices=40):
        # 1. Generate Vertices and Indices
        vertices, indices = self._generate_uv_sphere(radius, stacks, slices)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        
        # 2. Initialize the Mesh with EBO setup
        super().__init__(self.vertices, self.indices, mode=GL_TRIANGLES)
        
        self.highlight = Highlight(self.vertices, self.indices)
        self.enable_highlight = False
        self.transform.position.update(0.0, 0.0, -3.0)
    
    def draw(self):
        self.highlight.transform = self.transform
        if self.enable_highlight:
            self.highlight.draw()
       
        super().draw()

    def gen_uv_sphere(self, radius, stacks, slices):
        vertices = []
        
        # 360 degrees is 2pi radians
        # Angle steps between slices (longitude) and stacks (latitude)
        d_slice = np.pi / stacks  # Phi: 0 to PI (Top to Bottom)
        d_stack = 2 * np.pi / slices  # Theta: 0 to 2*PI (Around the sphere)

        # Iterate over stacks (latitude lines)
        for i in range(stacks + 1):
            # i = 0 (top pole), i = stacks (bottom pole)
            phi = i * d_slice
            y = radius * np.cos(phi)
            
            # Iterate over slices (longitude lines)
            for j in range(slices + 1):
                theta = j * d_stack
                
                # Calculate vertex position (x, z) on the latitude circle
                x = radius * np.sin(phi) * np.cos(theta)
                z = radius * np.sin(phi) * np.sin(theta)

                # Use position as color for visualization (optional)
                r, g, b = x / radius, y / radius, z / radius

                vertices.append((x, y, z ,r, g, b)) # Use white color for simplicity

        return vertices

    def _generate_uv_sphere(self, radius, stacks, slices):
        """Generates UV Sphere vertices and indices (indices for EBO)."""
        vertices = self.gen_uv_sphere(radius, stacks, slices)
        indices = []
        
        # --- Generate Indices ---
        # Vertices are arranged: (s0, l0), (s0, l1), ..., (s1, l0), (s1, l1), ...
        # where s is stack index and l is slice index
        
        # Iterate over quads formed by (stack i, slice j) and (stack i+1, slice j+1)
        for i in range(stacks):
            for j in range(slices):
                # Calculate the 4 vertex indices that form the quad:
                # v1 --- v2
                # |      |
                # v3 --- v4
                
                # Vertex index for current stack (i) and current slice (j)
                v1 = i * (slices + 1) + j
                # Vertex index for next stack (i) and next slice (j+1)
                v2 = v1 + 1
                # Vertex index for next stack (i+1) and current slice (j)
                v3 = (i + 1) * (slices + 1) + j
                # Vertex index for next stack (i+1) and next slice (j+1)
                v4 = v3 + 1
                
                # The quad is split into two triangles: (v1, v3, v4) and (v1, v4, v2)
                # Ensure correct winding order (e.g., counter-clockwise) for front-facing
                
                # Triangle 1 (Bottom-Left)
                indices.extend([v1, v3, v4]) 
                
                # Triangle 2 (Top-Right)
                indices.extend([v1, v4, v2]) 

        return vertices, indices
  