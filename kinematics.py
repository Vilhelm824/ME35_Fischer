import math

class TwoDofArm:
    # two-joint arm with joint 1 at origin, arm lengths l1 & l2
    # r1 = angle from x-axis to arm 1
    # r2 = angle formed by arm 1 to arm 2
    def __init__(self, l1, l2):
        self.l1 = l1
        self.l2 = l2
        self.r1 = 180
        self.r2 = 180
        
    # convert given joint angles(deg) to (x,y) position    
    def forward(self, d1, d2):
        self.r1 = d1*math.pi/180
        self.r2 = d2*math.pi/180
        b = self.r1+self.r2-math.pi
        x = self.l1*math.cos(r1) + self.l2*math.cos(b)
        y = self.l1*math.sin(r1) + self.l2*math.sin(b)
        return(x,y)
    
    # convert given (x,y) position to joint angles(deg)
    def inverse(x, y):
        a = math.acos((self.l1^2-self.l2^2+x^2+y^2)/(2*self.l1*math.sqrt(x^2+y^2)))
        self.r1 = math.atan2(y,x) + a
        self.r2 = math.acos((self.l1^2+self.l2^2-x^2-y^2)/(2*self.l1*self.l2))
        d1 = self.r1*180/math.pi
        d2 = self.r2*180/math.pi
        return(d1, d2)
    