import time
class PIDController(): # these are more p controller than anything
    def __init__(self, P, I = 0, D = 0):
        self.p = P
        self.i = I
        self.d = D
        self.setpoint = None
        
        self.integrator = 0
        self.initialized = False
        self.latest_t = 0
        self.latest_e = 0

    def evaluate(self, measurement, setpoint = None, error = lambda x,y: x - y):
        if setpoint is not None:
            self.setpoint = setpoint
        else:
            print("NO SETPOINT!")
            return
            
        e = error(self.setpoint, measurement) 
        P = self.p * e
        I = 0
        D = 0
        
        current = time.perf_counter()
        if self.initialized and ((self.i != 0) or (self.d != 0)):
            dt = current - self.latest_t
            self.integrator += 0.5 * (e + self.latest_e) * dt
            
            I = self.i * self.integrator
            D = self.d * (e - self.latest_e) / dt
        else:
            self.initialized = True
            
        self.latest_t = current
        self.latest_e = e
            
        return P + I + D

    
    def setSetpoint(self, setpoint):
        self.setpoint = setpoint
        
    def deinit(self):
        self.integrator = 0
        self.initialized = False
        