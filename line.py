from OpenGL.GL import *
import numpy as np
from vector import Transform, OrbitalTransfrom
from mesh import Mesh




class Line(Mesh):
    def __init__(self):
        vertices = (
        # Position       Color
        -0.5, 0.5, 0.5,  1.0, 0.0, 0.0, #1
         0.5, 0.5, 0.5,  0.0, 1.0, 0.0, #2
                    
        )

        indices = (
            0, 1

        )

        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        mode = GL_LINES

        super().__init__(vertices, indices, mode)
        self.transform.position.update(0.0, 0.0, -3.0)
        