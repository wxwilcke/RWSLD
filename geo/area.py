#!/usr/bin/python3

class Area:
    RD_X_MIN = -7000
    RD_Y_MIN = 289000
    RD_X_MAX = 300000
    RD_Y_MAX = 629000

    def __init__(self, x_min=float("inf"), y_min=float("inf"), x_max=float("inf"), y_max=float("inf")):
        if x_min == float("inf"):
            x_min = self.RD_X_MIN
        if y_min == float("inf"):
            y_min = self.RD_Y_MIN
        if x_max == float("inf"):
            x_max = self.RD_X_MAX
        if y_max == float("inf"):
            y_max = self.RD_Y_MAX

        self.minimum = self.Coordinate(x_min, y_min)
        self.maximum = self.Coordinate(x_max, y_max)

    class Coordinate:
        x = float("inf")
        y = float("inf")

        def __init__(self, x, y):
            self.x = x
            self.y = y

        def get(self):
            return (self.x, self.y)
