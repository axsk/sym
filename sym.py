import bpy
import bmesh
import math
from mathutils import Vector

pc = 1.5    # Pruning limit for curvature
mrad = 0.1  # relative radius for mean shift (1 is the whoe space)
mres = 2000 # resolution for Mean Shift

scene = bpy.context.scene   # for visualisation

bmesh.types.BMesh.free

bm=bmesh.new()
bm.from_mesh(bpy.data.meshes["Suzanne"]) # get mesh data from model

"""
### Show the mesh in 3-d view
mesh = bpy.data.meshes.new("Buttefly")
bm.to_mesh(mesh)
ob_new = bpy.data.objects.new("Butterfly", mesh)     
scene.objects.link(ob_new)
"""

### ANALYSIS -> SIGNATURES ###

class signature:
    id = 0
    co = 0
    normal = 0
    curv = 0
    
sigs = []       # representation of signature space Omega
pruned = []     # Point sorted out by pruning

for vert in bm.verts:
    sig = signature()
    sig.id=vert.index
    sig.co=vert.co
    sig.normal=vert.normal # unfortunately not working (at least in 2d) :(
    sig.curv = vert.calc_shell_factor() # "sharpness of the vertex"
    
    if sig.curv > pc:      # Pruning
        sigs.append(sig)
    else:
        pruned.append(sig)
    
sigs.sort(key=lambda x: x.curv, reverse=False) # sort by curvature
laenge = len(sigs) # length of the array

### PAIRING -> TRANSFORMATIONS ###

class transf:
    scal = 1                # scaling
    (rx,ry,rz) = (0,0,0)    # rotation arround this vector
    rr = 0                  # rotation angle
    (tx,ty,tz) = (0,0,0)    # translation vector
    rnor=Vector()           # reflection normal
    roff=Vector()           # reflection offset in normal direction
    p=0                     # Vertex 1
    q=0                     # Vertex 2
    
transfs = [] # representation of transformation space Gamma

for i,p in enumerate(sigs):
    k=i+1
    while (k < laenge) and (abs( 1 - (sigs[k].curv / p.curv) )) < 0.3 and (p.co-sigs[k].co).length != 0 : # only pair similar curvatures
        this = transf()
        this.p=p
        this.q=sigs[k]
        
        (this.tx,this.ty,this.tz)           = p.co - this.q.co  # translation
        (this.ry,this.ry,this.rz,this.rr)   = p.normal.rotation_difference(this.q.normal) # rotation
        
        # normal calculation
        this.rnor=p.co-this.q.co 
        this.rnor.normalize()
        # offset calculation in the normal direction
        hypertenuse     = (p.co + this.q.co) / 2
        if hypertenuse.length == 0:
            this.off = 0
        else:
            alpha           = abs(hypertenuse.angle(this.rnor) - (math.pi/2))
            this.roff       = math.sin(alpha) * hypertenuse.length
        
        transfs.append(this)
        k=k+1

        
    
### CLUSTERING ###

# for reflection

# even point grid on the sphere for clustering of reflection normal direction
# https://perswww.kuleuven.be/~u0017946/publications/Papers97/art97a-Saff-Kuijlaars-MI/Saff-Kuijlaars-MathIntel97.pdf
class svector(Vector):  # add density parameter to Vector()
    dens=0
Nu = mres # resolution / number of directions to analyse weight
grid = []
N=Nu*2
for k in range(Nu,N):   # just halfe shpere since parallel normals are equivalent
    h = -1 + (2*(k-1)/(N-1))
    theta=math.acos(h)
    if k==Nu or k==N:
        phi=0
    else:
        phi=(phi + (3.6/math.sqrt(N*(1-h**2)))) % (2*math.pi) 
    v=svector()
    v.xyz = (math.cos(theta), math.cos(phi)*math.sin(theta), math.sin(phi)*math.sin(theta))
    grid.append(v)


## show grid in 3-d view and get faces of surface for later visualisation ##

# detour over mesh to create bmesh from a list of vertecis
me = bpy.data.meshes.new("grid")        # create a new mesh  
ob = bpy.data.objects.new("grid", me)   # create an object with that mesh
me.from_pydata(grid,[],[])              # Fill the mesh with verts, edges, faces 
sphere=bmesh.new()
sphere.from_mesh(me)
bmesh.ops.convex_hull(sphere,input=sphere.verts,use_existing_faces=False) # generate faces

# get faces for later visualization
sfaces = []
for f in sphere.faces:
    points=[]
    for v in f.verts:
        points.append(v.index)
    sfaces.append(points)

"""
# show sphere
sphere.to_mesh(me)
bpy.context.scene.objects.link(ob)      # Link object to scene 
me.update() 
"""




# calculate density for each point of the grid
ntrans = len(transfs)
for v in grid:
    for t in transfs:
        diff = math.pi - abs(math.pi - v.angle(t.rnor)) # angle between the normals ignoring sign
        # linear weight looks like __/\__ where mrad*math.pi is the maximal distance
        v.dens += max( 0 , (mrad*math.pi - diff)/mrad*math.pi )
    v.dens = v.dens/ntrans  # normalazation

# show density by hight on the half sphere in 3-d view
model = []
for v in grid:
    m = Vector()
    m.xyz = v.xyz*v.dens*10
    model.append(m)    
me = bpy.data.meshes.new("model")   # create a new mesh  
ob = bpy.data.objects.new("model", me)          # create an object with that mesh
#ob.location = bpy.context.scene.cursor_location   # position object at 3d-cursor
bpy.context.scene.objects.link(ob)                # Link object to scene 
# Fill the mesh with verts, edges, faces 
me.from_pydata(model,[],sfaces)   # edges or faces should be [], or you ask for problems
me.update()  


### VERIFICATION ###