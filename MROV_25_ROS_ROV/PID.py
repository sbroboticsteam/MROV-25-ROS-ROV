class PIDController(): # these are more p controller than anything
    def __init__(self, P, I = 0, D = 0):
        self.p = P
        self.i = I
        self.d = D
        self.setpoint = None

    def evaluate(self, measurement, setpoint = None):
        if setpoint:
            self.setpoint = setpoint
        return self.p * (self.setpoint - measurement)

    
    def setSetpoint(self, setpoint):
        self.setpoint = setpoint