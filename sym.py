import bpy
import code
import sys
sys.path.append(r'.')
import globals as g


"""
### Show the mesh in 3-d view
mesh = bpy.data.meshes.new("Buttefly")
g.bm.to_mesh(mesh)
ob_new = bpy.data.objects.new("Butterfly", mesh)     
g.scene.objects.link(ob_new)
"""

import signatures as si
si.mksigs()

import transformations as tr
tr.mktransfs()  # make/fill transformation space
tr.plotr()      # plotting the transformation space for refletions

import clustering

import verification
