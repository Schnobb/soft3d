from math import sin, cos, tan, sqrt, radians

import numpy as np

DEFAULT_APECT_RATIO = 3.0/4.0

class Util:
    def model2np(model):
        return [np.append(np.array([float(x) for x in vertex]), 1) for vertex in model]
    
    def normalize3(vector):
        norm = sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
        return (vector[0]/norm, vector[1]/norm, vector[2]/norm)
    
    def dist2(point0, point1):
        return sqrt((point1[0]-point0[0])**2 + (point1[1]-point0[1])**2)
    
    def middlePoint2(point0, point1):
        return ((point1[0]-point0[0])/2 + point0[0], (point1[1]-point0[1])/2 + point0[1])
        
class Matrices:
    def identityMatrix():
        return np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]).reshape((4, 4))
    
    def rotationMatrix(rotation):
        x, y, z = rotation
        xcos = cos(x)
        xsin = sin(x)
        ycos = cos(y)
        ysin = sin(y)
        zcos = cos(z)
        zsin = sin(z)
        
        rx = np.array([1, 0, 0, 0, 0, xcos, xsin, 0, 0, -xsin, xcos, 0, 0, 0, 0, 1]).reshape((4, 4))
        ry = np.array([ycos, 0, -ysin, 0, 0, 1, 0, 0, ysin, 0, ycos, 0, 0, 0, 0, 1]).reshape((4, 4))
        rz = np.array([zcos, zsin, 0, 0, -zsin, zcos, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]).reshape((4, 4))
        
        result = np.dot(np.dot(rx, ry), rz)
        #print("rotationMatrix:\n{}\n".format(result))
        return result
    
    def translationMatrix(pos):
        x, y, z = pos
        
        result = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1]).reshape((4, 4))
        #print("translationMatrix:\n{}\n".format(result))
        return result
    
    def scalingMatrix(x, y, z):
        result = np.array(x, 0, 0, 0, 0, y, 0, 0, 0, 0, 0, z, 0, 0, 0, 1).reshape((4, 4))
        #print("scalingMatrix:\n{}\n".format(result))
        return result
    
    def lookAtMatrix(pos, target, upVector):
        """# http://www.cs.virginia.edu/~gfx/Courses/1999/intro.fall99.html/lookat.html
        F = np.array([target[0] - pos[0], target[1] - pos[1], target[2] - pos[2]]).reshape((3, 1))
        
        normF = sqrt(F[0][0]**2 + F[1][0]**2 + F[2][0]**2)
        f = np.array([F[0][0]/normF, F[1][0]/normF, F[2][0]/normF])
        
        normU = sqrt(upVector[0]**2 + upVector[1]**2 + upVector[2]**2)
        u1 = np.array([upVector[0]/normU, upVector[1]/normU, upVector[2]/normU])
        
        s = np.cross(f, u1)
        u2 = np.cross(s, f)
        M = np.array([s[0], s[1], s[2], 0, u2[0], u2[1], u2[2], 0, -f[0], -f[1], -f[2], 0, 0, 0, 0, 1]).reshape((4, 4))
        
        T = np.array([1, 0, 0, -pos[0], 0, 1, 0, -pos[1], 0, 0, 1, -pos[2], 0, 0, 0, 1]).reshape((4, 4))
        
        result = np.dot(M, T)
        print("lookAtMatrix:\n{}\n".format(result))
        return result
        #return Matrices.identityMatrix()"""
        # http://stackoverflow.com/questions/349050/calculating-a-lookat-matrix
        zaxis = Util.normalize3(np.array(target) - np.array(pos))
        xaxis = Util.normalize3(np.cross(upVector, zaxis))
        yaxis = np.cross(zaxis, xaxis)
        
        a = -np.dot(xaxis, pos)
        b = -np.dot(yaxis, pos)
        c = -np.dot(zaxis, pos)
        
        result = np.array([xaxis[0], yaxis[0], zaxis[0], 0, xaxis[1], yaxis[1], zaxis[1], 0, xaxis[2], yaxis[2], zaxis[2], 0, a, b, c, 1]).reshape((4, 4))
        #print("lookAtMatrix:\n{}\n".format(result))
        return result
    
    def projectionMatrix(w=1.0, h=DEFAULT_APECT_RATIO, zn=0.1, zf=1.0):
        """ # TODO: Implement the projection matrix
        #   https://www.opengl.org/sdk/docs/man2/xhtml/gluPerspective.xml
        f = 1/tan(radians(fov)/2)
        a = (far + near) / (near - far)
        b = (2 * far * near) / (near - far)
        
        result = np.array([f/aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, a, b, 0, 0, -1, 0]).reshape((4, 4))
        #print("projectionMatrix:\n{}\n".format(result))
        return result
        #return Matrices.identityMatrix()"""
        a = 2*zn/w
        b = 2*zn/h
        c = zf/(zf-zn)
        d = zn*zf/(zn-zf)
        
        result = np.array([a, 0, 0, 0, 0, b, 0, 0, 0, 0, c, 1, 0, 0, d, 0]).reshape((4, 4))
        #print("projectionMatrix:\n{}\n".format(result))
        return result
    
    def orthographicMatrix(left=-1.0, right=1.0, bottom=1.0, top=-1.0, nearVal=0.01, farVal=10.0):
        a = right-left
        b = top-bottom
        c = farVal-nearVal
        
        tx = - (right+left)/a
        ty = - (top+bottom)/b
        tz = - (farVal+nearVal)/c
        
        result = np.array([2/a, 0, 0, tx, 0, 2/b, 0, ty, 0, 0, -2/c, tz, 0, 0, 0, 1]).reshape((4, 4))
        #print("orthographicMatrix:\n{}\n".format(result))
        return result
