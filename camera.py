from pyrr import matrix44
from vector import OrbitalTransfrom
import numpy as np

class Camera():
    """Camera Object"""
    def __init__(self):
        self.transform = OrbitalTransfrom(r = 1, pitch=1, yaw=0)
        self.transform.update(0, 0, 0)
    
    def view_matrix(self):
        """return view matrix"""
        # create view matrix with updated camera target
        view = matrix44.create_look_at(
        eye=self.transform.position.vector(), 
        target=self.transform.target.vector(),
        up=self.transform.world_up.vector(),
        dtype=np.float32)


        return view