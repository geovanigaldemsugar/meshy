from OpenGL.GL import *
import numpy as np
from vector import Transform, OrbitalTransfrom

class Mesh:
    """ Base class for Creating Object Meshes using Index Buffer Object(EBO) """

    def __init__(self, vertices:np.ndarray, indices:np.ndarray):
        self.transform:Transform = Transform()
        self.vertices = vertices
        self.indices = indices
        self.indices_count = len(self.indices)
        self.vertex_count = len(self.vertices) // 6

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

    def draw(self):
        """ Draw Mesh using glDrawElements """
        glBindVertexArray(self.vao)
        # Draw primitive/triangles using indices specified in the EBO
        glDrawElements(GL_TRIANGLES, self.indices_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))
        glDeleteBuffers(1, (self.ebo,))

        
class Square(Mesh):
    """Square Mesh"""

    def __init__(self):
        # square has 4 unique vertices
        vertices = (
            # Position             Color
            -0.5, -0.5,  0.5,   1.0, 0.0, 0.0, #0 - Front-Bottom-Left
             0.5, -0.5,  0.5,   0.0, 1.0, 0.0, #1 - Front-Bottom-Right
             0.5,  0.5,  0.5,   0.0, 0.0, 1.0, #2 - Front-Top-Right
            -0.5,  0.5,  0.5,   1.0, 1.0, 0.0, #3 - Front-Top-Left
            
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
            # Position             Color
            -0.5, -0.5,  0.5,   1.0, 0.0, 0.0, #0 - Front-Bottom-Left
             0.5, -0.5,  0.5,   0.0, 1.0, 0.0, #1 - Front-Bottom-Right
             0.5,  0.5,  0.5,   0.0, 0.0, 1.0, #2 - Front-Top-Right
            -0.5,  0.5,  0.5,   1.0, 1.0, 0.0, #3 - Front-Top-Left
            -0.5, -0.5, -0.5,   1.0, 0.0, 0.0, #4 - Back-Bottom-Left
             0.5, -0.5, -0.5,   0.0, 1.0, 0.0, #5 - Back-Bottom-Right
             0.5,  0.5, -0.5,   0.0, 0.0, 1.0, #6 - Back-Top-Right
            -0.5,  0.5, -0.5,   1.0, 1.0, 0.0, #7 - Back-Top-Left
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
  
        self.transform.position.update(0.0, 0.0, -3.0)


class Pyramid(Mesh):
    """Square Pyramid Mesh"""
    def __init__(self):
        vertices = (
              # Position              Color
            -0.5, -0.5,  0.5,    1.0, 0.0, 0.0,  #0 - right-bottom-front
             0.5, -0.5,  0.5,    0.0, 1.0, 0.0,  #1 - left-bottom-front
             0,    0.5,    0,    0.0, 0.0, 1.0,  #2 - apex
            -0.5, -0.5, -0.5,    1.0, 0.0, 0.0,  #3 - left-bottom-back
             0.5, -0.5, -0.5,    0.0, 1.0, 0.0,  #4 - right-bottom-back
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


class Camera():
    """Camera Object"""
    def __init__(self):
        self.transform = OrbitalTransfrom(r = 1, pitch=1, yaw=0)
        self.transform.update(0, 0, -3)
    