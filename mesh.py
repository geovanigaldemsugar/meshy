import pyrr
import numpy as np
from ray import *
from OpenGL.GL import *
from OpenGL.constant import IntConstant
from vector import Transform, OrbitalTransfrom
from hightlight import Highlight, Points, WireFrame, WireFrameAndPoints

class Mesh:
    """ Base class for Creating Object Meshes using Index Buffer Object(EBO) """

    def __init__(self, vertices:np.ndarray, indices:np.ndarray, mode:IntConstant=GL_TRIANGLES, line:float=1):
        self.transform:Transform = Transform()
        self.vertices = vertices
        self.indices = indices
        self.indices_count = len(self.indices)
        self.mode = mode
        self.line = line
        self.enable = True
        self.highlight = Highlight(self.vertices, self.indices)
        self.wireframe = WireFrameAndPoints(self.vertices, self.indices)
        self.highlight.enable = False
        self.wireframe.enable = False


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
    
    def create_model_matrix(self):
        """create model matrix with T * R * S
        Returns:
            np.ndarray: model matrix
        """
        model = pyrr.matrix44.create_identity(dtype=np.float32)
        model = pyrr.matrix44.multiply(m1=model, m2=pyrr.matrix44.create_from_scale(scale=self.transform.scale.vector(), dtype=np.float32))
        model = pyrr.matrix44.multiply(m1=model, m2=pyrr.matrix44.create_from_eulers(eulers=self.transform.rotation.to_radians(), dtype=np.float32))
        model = pyrr.matrix44.multiply(m1=model,  m2=pyrr.matrix44.create_from_translation(vec=self.transform.position.vector(), dtype=np.float32))
        
        return model

    def draw(self):
        """ Draw Mesh using glDrawElements """
        if self.enable:
            glBindVertexArray(self.vao)
            glDrawElements(self.mode, self.indices_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))
            
        # update transforms 
        if self.highlight.enable:
            self.highlight.transform = self.transform
            self.highlight.draw()

        if self.wireframe.enable:
            self.wireframe.transform = self.transform
            self.wireframe.draw()

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))
        glDeleteBuffers(1, (self.ebo,))
        self.highlight.destroy()

    

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

    def load_mesh(self, filepath:str):
        vertices, indices = self._load_object(filepath) 
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        mesh = Mesh(vertices, indices)
        self.add_mesh(mesh)

    def _load_object(self, filepath:str):
        vertices = []
        indices = []
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.split(' ')

                if line[0] == 'v':
                    v = self.read_vertex_data(line)
                    v.extend([0.8, 0.8, 0.8])
                    vertices.append(v)

                elif line[0] == 'f':
                    i = self.read_face_data(line)
                    indices.extend(i)
                
                elif line[0] == 'o':
                    name = line[1]
                
        print(f'Loaded /{filepath}: {len(vertices)} vertices, {len(indices)//6} faces')
    
        return vertices, indices
    
    def read_vertex_data(self, vertex_line:list[str]) -> list[float]:
        return [float(vertex_line[1]),
                float(vertex_line[2]),
                float(vertex_line[3])]
    
    def read_face_data(self, face_line:list[str]) -> list[int]:
        # draw each traingle in quad
        # triangles in face 4 points/ 2 triangles
        face_v_index = []
        indices = []
        for corner in face_line[1:]:
            face_v_index.append(self.read_corner(corner, indices))
        
       
        # draw each traingle in quad/face
        t1 = [face_v_index[0], #1st point
                face_v_index[1],#2nd point
                face_v_index[2]#3rd point
                ]
        indices.extend(t1)

        if len(face_v_index) > 3:
            # if its a quad draw second traingle
            t2 = [face_v_index[2],#3st point
                    face_v_index[3],#4th point
                    face_v_index[0]#1st point
                    ]
            indices.extend(t2)

                
        # print(t1, '-', t2)
        # print(face_v_index)

        return indices
        

    def read_corner(self, corner:str, indices:list[list[float]]) -> int:
        corner = corner.split('/')
        v_index = int(corner[0]) - 1
        return v_index
        # indices.append(v_index)
        

        # implement later
        # vt_index = 
        # vn_index =  



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
        super().__init__(self.vertices, self.indices)
        self.transform.position.update(0.0, 0.0, -3.0)
  
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
        super().__init__(self.vertices, self.indices)
        self.transform.position.update(0.0, 0.0, -3.0)
    

class Sphere(Mesh):
    """Sphere Mesh using UV Sphere generation and EBO"""

    def __init__(self, radius=0.5, stacks=40, slices=40):
        # 1. Generate Vertices and Indices
        vertices, indices = self._generate_uv_sphere(radius, stacks, slices)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        
        # 2. Initialize the Mesh with EBO setup
        super().__init__(self.vertices, self.indices, mode=GL_TRIANGLES)
        self.transform.position.update(0.0, 0.0, -3.0)
   

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
  