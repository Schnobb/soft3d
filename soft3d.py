import numpy as np
import time
import json
import array

from tkinter import *
from PIL import Image, ImageTk
from math import radians

from soft3dUtils import Matrices, Util

DEFAULT_WIDTH = 200
DEFAULT_HEIGHT = 150
MIN_WAIT = 50 # We need to give some time to Tk or it won't show the canvas window at all (ms)
ROTATION_AXIS = (1.0, 0.0, 1.0)
ROTATION_SPEED = 0.1
CAMERA_POS = (0.0, 0.0, -3.0)

CLEAR_FLAG = True

class renderMode:
    VERTEX = 0
    WIREFRAME = 1
    FACES = 2
    TEXTURE = 3
    
    current = VERTEX
    
    def setDefault(value):
        current = value

class Device:
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        # TODO: c'est stupide, changer ca pour quelque chose de plus low-level qu'une fucking liste
        #self.backBuffer = [(0, 0, 0, 0) for i in range(width*height)]
        self.backBuffer = array.array('B', [0 for i in range(width*height*4)])
        self.width = width
        self.height = height
    
    def clear(self, r=0, g=0, b=0, a=255):
        # TODO: that fucking clear is sooooooooooooooooooooooooooooooo long, fuck that shit
        for i in range(0, len(self.backBuffer), 4):
            self.backBuffer[i+0] = r
            self.backBuffer[i+1] = g
            self.backBuffer[i+2] = b
            self.backBuffer[i+3] = a
        
        #self.backBuffer = array.array('B', [255 if (i+1) % 4 == 0 else 0 for i in range(self.width*self.height*4)])
        #self.backBuffer = [(r, g, b, a)] * len(self.backBuffer)
    
    def getFrameImage(self):
        #im = Image.new('RGBA', (self.width, self.height))
        #im.putdata(self.backBuffer)
        #im.save('asdfmarde.bmp')
        im = Image.frombuffer('RGBA', (self.width, self.height), self.backBuffer, 'raw', 'RGBA', 0, 1)
        return ImageTk.PhotoImage(im)
    
    def putPixel(self, x, y, rgba=(0, 0, 0, 0)):
        index = (x + y * self.width) * 4
        self.backBuffer[index+0] = rgba[0] & 0xFF
        self.backBuffer[index+1] = rgba[1] & 0xFF
        self.backBuffer[index+2] = rgba[2] & 0xFF
        self.backBuffer[index+3] = rgba[3] & 0xFF
    
    def transform(self, coord, transMat):
        x = (coord[0] * transMat[0][0]) + (coord[1] * transMat[1][0]) + (coord[2] * transMat[2][0]) + transMat[3][0]
        y = (coord[0] * transMat[0][1]) + (coord[1] * transMat[1][1]) + (coord[2] * transMat[2][1]) + transMat[3][1]
        z = (coord[0] * transMat[0][2]) + (coord[1] * transMat[1][2]) + (coord[2] * transMat[2][2]) + transMat[3][2]
        w = (coord[0] * transMat[0][3]) + (coord[1] * transMat[1][3]) + (coord[2] * transMat[2][3]) + transMat[3][3]
        
        #print("{}\n{}, {}, {}: {}\n".format(transMat, x, y, z, w))
        
        return (x/w, y/w, z/w)
    
    def project(self, coord, transMat):
        #print("{}\n{}".format(coord, transMat))
        point = self.transform(coord, transMat)
        
        #print(point)
        
        #x = (point[0] + 1.0) * (self.width / 2.0)
        #y = (point[1] + 1.0) * (self.height / 2.0)
        x = point[0] * self.width + self.width/2.0
        y = -point[1] * self.height + self.height/2.0
        
        #print("{} {}".format(x, y))
        
        return np.array([x, y])
    
    def drawPoint(self, point, color=(255, 255, 0, 255)):
        if point[0] >= 0 and point[1] >= 0 and point[0] < self.width and point[1]< self.height:
            self.putPixel(int(point[0]), int(point[1]), color)
    
    def drawLine(self, point0, point1, color=(255, 255, 0, 255)):
        if Util.dist2(point0, point1) < 2:
            return
        
        middlePoint = Util.middlePoint2(point0, point1)
        self.drawPoint(middlePoint, color)
        self.drawLine(point0, middlePoint)
        self.drawLine(middlePoint, point1)
    
    def drawBline(self, point0, point1, color=(255, 255, 0, 255)):
        x0 = int(point0[0])
        y0 = int(point0[1])
        x1 = int(point1[0])
        y1 = int(point1[1])
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            self.drawPoint((x0, y0))
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -=dy
                x0 += sx
            
            if e2 < dx:
                err += dx
                y0 += sy
    
    def render(self, camera, meshes, clear=True):
        if clear:
            self.clear()
            
        viewMatrix = Matrices.lookAtMatrix(camera.pos, camera.target, camera.upVector)
        projectionMatrix = Matrices.projectionMatrix()
        
        for mesh in meshes:
            worldMatrix = np.dot(Matrices.translationMatrix(mesh.pos), Matrices.rotationMatrix(mesh.rotation))
            transformMatrix = np.dot(np.dot(worldMatrix, viewMatrix), projectionMatrix)
            #print("worldMatrix:\n{}\n\nprojectionMatrix:\n{}\n".format(worldMatrix, transformMatrix))
            
            if renderMode.current == renderMode.VERTEX:
                for vertex in mesh.vertices:
                    self.drawPoint(self.project(vertex, transformMatrix))
            elif renderMode.current == renderMode.WIREFRAME:    
                for face in mesh.faces:
                    v1 = mesh.vertices[face[0]]
                    v2 = mesh.vertices[face[1]]
                    v3 = mesh.vertices[face[2]]
                    
                    px1 = self.project(v1, transformMatrix)
                    px2 = self.project(v2, transformMatrix)
                    px3 = self.project(v3, transformMatrix)
                    
                    self.drawBline(px1, px2)
                    self.drawBline(px2, px3)
                    self.drawBline(px3, px1)
    
    def createMeshesFromJSON(self, jsonObject):
        meshes = []
        for mesh in jsonObject['meshes']:
            vertices = mesh['vertices']
            faces = mesh['indices']
            uvCount = mesh['uvCount']
            verticesStep = 1
            
            if uvCount == 0:
                verticesStep = 6
            elif uvCount == 1:
                verticesStep = 8
            elif uvCount == 2:
                verticesStep = 10
            
            verticesCount = int(len(vertices) / verticesStep)
            facesCount = int(len(faces) / 3)
            
            verts = []
            for i in range(verticesCount):
                x = vertices[i * verticesStep]
                y = vertices[i * verticesStep + 1]
                z = vertices[i * verticesStep + 2]
                verts.append((x, y, z))
            
            feces = []
            for i in range(facesCount):
                a = faces[i * 3]
                b = faces[i * 3 + 1]
                c = faces[i * 3 + 2]
                feces.append((a, b, c))
                
            m = Mesh('Monkey', Util.model2np(verts), feces, (mesh['position'][0], mesh['position'][1], mesh['position'][2]))
            meshes.append(m)
        
        return meshes
        
class Camera:
    def __init__(self, pos=(0.0, 0.0, 0.0), target=(0.0, 0.0, 0.0), upVector=(0.0, 1.0, 0.0)):
        self.pos = pos
        self.target=target
        self.upVector=upVector
    
class Mesh:
    def __init__(self, name='', vertices=[], faces=[], pos=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
        self.name = name
        self.vertices = vertices
        self.faces = faces
        self.pos = pos
        self.rotation = rotation

# TODO: Those fucking things (renderLoop() and main()) are fucking atrocious, please refactor that shit        
def renderLoop(frameLen, camera, meshes, device, root, w, canvasImg):
    # Butt fucking ugly, but the GC won't trash it then
    global frame
    
    start = time.time()
    
    newrot = tuple([ROTATION_SPEED * x for x in ROTATION_AXIS])
    
    for mesh in meshes:
        mesh.rotation = (meshes[0].rotation[0] + newrot[0], meshes[0].rotation[1] + newrot[1], meshes[0].rotation[2] + newrot[2])
    
    #meshes[0].rotation = (meshes[0].rotation[0] + newrot[0], meshes[0].rotation[1] + newrot[1], meshes[0].rotation[2] + newrot[2])
    #meshes[1].rotation = (meshes[1].rotation[0] + newrot[1], meshes[1].rotation[1] + newrot[0], meshes[1].rotation[2] + newrot[1])
    
    camera.pos = (camera.pos[0], camera.pos[1], camera.pos[2])
    device.render(camera, meshes, clear=CLEAR_FLAG)
    frame = device.getFrameImage()
    #w.delete(ALL)
    #w.create_image((DEFAULT_WIDTH/2, DEFAULT_HEIGHT/2), image=frame)
    w.itemconfig(canvasImg, image=frame)
    
    endTime = int((time.time() - start) * 1000)
    next = max(MIN_WAIT, frameLen - endTime)
    #next = frameLen
    root.after(next, renderLoop, frameLen, camera, meshes, device, root, w, canvasImg)
        
def main():
    print("Loading meshes...")
    verts = [
        (-1, 1, 1), (1, 1, 1),
        (-1, -1, 1), (1, -1, 1),
        (-1, 1, -1), (1, 1, -1),
        (1, -1, -1), (-1, -1, -1)
    ]
    
    faces = [
        (0, 1, 2), (1, 2, 3), (1, 3, 6), (1, 5, 6),
        (0, 1, 4), (1, 4, 5), (2, 3, 7), (3, 6, 7),
        (0, 2, 7), (0, 4, 7), (4, 5, 6), (4, 6, 7),
    ]
    
    cube = Mesh('Cube', Util.model2np(verts), faces, (0.0, 0.0, 0.0))
    camera = Camera(CAMERA_POS, (0.0, 0.0, 0.0))
    device = Device()
    
    meshes = []
    meshes.extend(device.createMeshesFromJSON(json.loads(open('cul.json', 'r').read())))
    meshes[0].rotation = (radians(-90), 0.0, 0.0)
    #meshes.append(cube)
    
    meshes = [cube]
    
    print("Done!\n")
    
    fps = 60.0
    frameLen = int(1.0/fps * 1000)
    #print(frameLen)
    
    print("Init Tk... ")
    root = Tk()
    root.resizable(False, False)
    root.title('3-DEEEEEEEEEEEEEEEEEEEEEE')
    w = Canvas(root, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)
    w.pack()
    
    device.render(camera, meshes)
    frame = device.getFrameImage()
    canvasImg = w.create_image((DEFAULT_WIDTH/2, DEFAULT_HEIGHT/2), image=frame)
    
    root.after(0, renderLoop, frameLen, camera, meshes, device, root, w, canvasImg)
    print("Done!\n")
    mainloop()
        
if __name__ == "__main__":
    main()