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
        self.vpos = self.__rm_rgb(self.vertices)

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
        max_xyz =  self.vpos.max(axis=0)
        xmax, ymax, zmax = max_xyz[0], max_xyz[1], max_xyz[2]

        sphere_C =self.transform.position.vector()
        scale_vec = self.transform.scale.vector()
        sphere_r = np.sqrt(
            (xmax * scale_vec[0]) ** 2 + (ymax * scale_vec[1]) ** 2 + (zmax * scale_vec[2]) ** 2
        )
        return sphere_r, sphere_C
    
    
    def __rm_rgb(self, vertices):
        xyz_only = []
        for i in range(0, len(vertices), 2):
            xyz_only.append(vertices[i])
        return np.array(xyz_only)
                

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

        # initialize id generator
        self.gen_id = self._id_generator()
    
    def add_mesh(self, *args:Mesh):
        for arg in args:
            arg.id = next(self.gen_id)
            arg.renderer = self.renderer
            arg.ray = Ray(self.renderer)
            self.meshes.append(arg)

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

    def hit_status(self):
        dtype = ([('id', int), ('hit', bool), ('distance', 'f4')])
        hit_stats = []
        for mesh in self.meshes:
            record = (mesh.id, mesh.hit[0], mesh.hit[1])
            hit_stats.append(record)
        return np.array(hit_stats, dtype=dtype)
    
    def get_hit(self):
        """get the hit object of the mesh the mouse is currently point on returns (mesh.id, hit, distance)"""
        hit_stats = self.hit_status()
        # check first if mouse ray hit multiple objects
        hit_true = hit_stats[hit_stats['hit']]
        multiple_hits = len(hit_true)
        if multiple_hits == 0:
            return False, (None, None, None)
        if multiple_hits > 0:
            hit = self._closest_hit(hit_true)
            hit = hit_true[0]
            return True, hit
        
        hit = hit_true[0]
        return True, hit
        
    def _closest_hit(self, hits):
        """find closest mesh, that mouse picking ray hit"""
        min_distance = np.min(hits['distance'])
        closest = (hits['distance'] == min_distance)
        h = hits[closest]
        return hits[closest]
           
                
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




class Cube(Mesh):
    """Cube Mesh"""

    def __init__(self):
        # Cube has 8 unique vertices 
        vertices = (
            # Position (x,y,z)    Color (r,g,b)
            (-0.5, -0.5,  0.5), (1.0, 0.0, 0.0), #0 - Front-Bottom-Left
            ( 0.5, -0.5,  0.5), (0.0, 1.0, 0.0), #1 - Front-Bottom-Right
            ( 0.5,  0.5,  0.5), (0.0, 0.0, 1.0), #2 - Front-Top-Right
            (-0.5,  0.5,  0.5), (1.0, 1.0, 0.0), #3 - Front-Top-Left
            (-0.5, -0.5, -0.5), (1.0, 0.0, 0.0), #4 - Back-Bottom-Left
            ( 0.5, -0.5, -0.5), (0.0, 1.0, 0.0), #5 - Back-Bottom-Right
            ( 0.5,  0.5, -0.5), (0.0, 0.0, 1.0), #6 - Back-Top-Right
            (-0.5,  0.5, -0.5), (1.0, 1.0, 0.0), #7 - Back-Top-Left
        )

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

        self.wireframe = CubeFrame()
        self.enable = False
        self.transform.position.update(0.0, 0.0, -3.0)
    
    def draw(self):
        self.wireframe.transform = self.transform
        if self.enable:
            self.wireframe.draw()
        else:
            super().draw()

        

    def destroy(self):
        self.wireframe.destroy()
        super().destroy()


class Pyramid(Mesh):
    """Square Pyramid Mesh"""
    def __init__(self):
        vertices = (
              # Position              Color
             (-0.5, -0.5,  0.5),   (1.0, 0.0, 0.0),  #0 - right-bottom-front
             (0.5, -0.5,  0.5),    (0.0, 1.0, 0.0),  #1 - left-bottom-front
             (0,    0.5,    0),    (0.0, 0.0, 1.0),  #2 - apex
             (-0.5, -0.5, -0.5),   (1.0, 0.0, 0.0),  #3 - left-bottom-back
             (0.5, -0.5, -0.5),    (0.0, 1.0, 0.0)  #4 - right-bottom-back
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

        self.transform.position.update(-0.5, 0.0, -3.0)
        


class CubeFrame(Mesh):
    """Cube WireFrame """

    def __init__(self):
        # Cube has 8 unique vertices 
        vertices = (
            # Position             Color
            -0.5, -0.5,  0.5,   1.0, 1.0, 1.0, #0 - Front-Bottom-Left
             0.5, -0.5,  0.5,   1.0, 1.0, 1.0, #1 - Front-Bottom-Right
             0.5,  0.5,  0.5,   1.0, 1.0, 1.0, #2 - Front-Top-Right
            -0.5,  0.5,  0.5,   1.0, 1.0, 1.0, #3 - Front-Top-Left
            -0.5, -0.5, -0.5,   1.0, 1.0, 1.0, #4 - Back-Bottom-Left
             0.5, -0.5, -0.5,   1.0, 1.0, 1.0, #5 - Back-Bottom-Right
             0.5,  0.5, -0.5,   1.0, 1.0, 1.0, #6 - Back-Top-Right
            -0.5,  0.5, -0.5,   1.0, 1.0, 1.0, #7 - Back-Top-Left
        )

        # cube has 12 edges/linesegments, each edge has 2 vertices (2 * 12), cube has 24 vertices, but edges share points
        indices = (
            # Front
            0, 1,  1, 2,  2, 3,  3, 0,

            # Right
            1, 5,  5, 6,   6, 2,

            # Back
            4, 5,  5, 6,  6, 7,  7, 4,

            # Left
            0, 4,   7, 3

        )

        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        mode = GL_LINES
        line = 4
        super().__init__(vertices, indices, mode, line)
  
        self.transform.position.update(0.0, 0.0, -3.0)



class Camera():
    """Camera Object"""
    def __init__(self):
        self.transform = OrbitalTransfrom(r = 1, pitch=1, yaw=0)
        self.transform.update(0, 0, -3)
    

class Sphere(Mesh):
    """Sphere Mesh using UV Sphere generation and EBO"""

    def __init__(self, radius=0.5, stacks=16, slices=16):
        # 1. Generate Vertices and Indices
        vertices, indices = self._generate_uv_sphere(radius, stacks, slices)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        
        # 2. Initialize the Mesh with EBO setup
        super().__init__(self.vertices, self.indices, mode=GL_TRIANGLES)
        
        # 3. Set initial transform
        self.transform.position.update(0.0, 0.0, -3.0)

    def _generate_uv_sphere(self, radius, stacks, slices):
        """Generates UV Sphere vertices and indices (indices for EBO)."""
        vertices = []
        indices = []

        # --- Generate Vertices ---
        # The stack loop iterates over latitude (phi), from pole to pole.
        for i in range(stacks + 1):
            # i/stacks gives 0.0 to 1.0, scaled to pi for latitude (phi).
            phi = (i / stacks) * np.pi 
            sin_phi = np.sin(phi)
            cos_phi = np.cos(phi)

            # The slice loop iterates over longitude (theta).
            for j in range(slices + 1):
                # j/slices gives 0.0 to 1.0, scaled to 2*pi for longitude (theta).
                theta = (j / slices) * 2 * np.pi
                
                # Parametric Sphere Equations (x, y, z)
                x = radius * np.cos(theta) * sin_phi
                y = radius * cos_phi  # Y is typically up/down for UV spheres
                z = radius * np.sin(theta) * sin_phi
                
                # We reuse the position for a simplistic color (R, G, B)
                r = (x + radius) / (2 * radius)  # Normalize x to 0..1 range
                g = (y + radius) / (2 * radius)  # Normalize y to 0..1 range
                b = (z + radius) / (2 * radius)  # Normalize z to 0..1 range
                
                # Vertex data: [Position (x,y,z), Color (r,g,b)] 
                # Total stride is 6 floats (24 bytes) as defined in your Mesh class
                vertices.extend([x, y, z, r, g, b])

        # --- Generate Indices (for EBO) ---
        # Connects vertices to form triangles.
        for i in range(stacks):
            for j in range(slices):
                # v1, v2, v3, v4 are the four corner indices of a quad face
                # The index calculation depends on the nested loop structure
                v1 = i * (slices + 1) + j
                v2 = v1 + 1
                v3 = (i + 1) * (slices + 1) + j
                v4 = v3 + 1
                
                # This quad is divided into two triangles (v1, v3, v4) and (v4, v2, v1)
                # The order ensures consistent winding for back-face culling
                
                # Triangle 1 (Bottom-Left to Top-Right half)
                indices.extend([v1, v3, v4])
                
                # Triangle 2 (Top-Right to Bottom-Right half)
                indices.extend([v4, v2, v1])

        return vertices, indices
    
    def draw(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        super().draw()
    