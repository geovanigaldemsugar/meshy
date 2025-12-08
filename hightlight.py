import numpy as np
from OpenGL.GL import *
from vector import Transform
from OpenGL.constant import IntConstant



class Mesh:
    """ Base class for Creating Object Meshes using Index Buffer Object(EBO) """

    def __init__(self, vertices:np.ndarray, indices:np.ndarray, mode:IntConstant=GL_TRIANGLES, line:float=1):
        self.transform:Transform = Transform()
        self.vertices = vertices
        self.indices = indices
        self.indices_count = len(self.indices)
        self.mode = mode
        self.line = line

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
    



class Highlight(Mesh):
    def __init__(self, vertices, indices):
        indices = self.__create_outline(indices)
        mode = GL_LINES
        line = 1
        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        super().__init__(self.vertices, self.indices, mode, line)
        self.change_color(1, 0.647, 0)
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
  
