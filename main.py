import math


class Rational:
    def __init__(self, x=0, y=1):
        if y == 0:
            raise ValueError('На 0 делить нельзя!')
        if y < 0:
            x = -x
            y = -y
        g = math.gcd(abs(x), y)
        self.x = x // g
        self.y = y // g


    def __add__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        new_x = self.x * smth.y + smth.x * self.y
        new_y = self.y * smth.y
        return Rational(new_x, new_y)


    def __radd__(self, smth):
        return self + smth


    def __sub__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        new_x = self.x * smth.y - smth.x * self.y
        new_y = self.y * smth.y
        return Rational(new_x, new_y)


    def __rsub__(self, other):
        return Rational(other, 1) - self


    def __mul__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        new_x = self.x * smth.x
        new_y = self.y * smth.y
        return Rational(new_x, new_y)


    def __rmul__(self, smth):
        return self * smth


    def __truediv__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        if smth.x == 0:
            raise ValueError('На 0 делить нельзя')
        new_x = self.x * smth.y
        new_y = self.y * smth.x
        return Rational(new_x, new_y)


    def __rtruediv__(self, smth):
        return Rational(smth, 1) / self


    def __eq__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        return self.x == smth.x and self.y == smth.y


    def __lt__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        return self.x * smth.y < smth.x * self.y


    def __le__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        return self.x * smth.y <= smth.x * self.y


    def __gt__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        return self.x * smth.y > smth.x * self.y


    def __ge__(self, smth):
        if isinstance(smth, int):
            smth = Rational(smth, 1)
        return self.x * smth.y >= smth.x * self.y


    def __str__(self):
        if self.y == 1:
            return str(self.x)
        return f"{self.x}/{self.y}"


if __name__ == "__main__":
    primer1 = Rational(1, 3)
    primer2 = Rational(2, 4)
    primer3= Rational(3, 4)

    print(f"r1 = {primer1}")
    print(f"r2 = {primer2}")
    print(f"r3 = {primer3}")

    print(f"r1 == r2: {primer1 == primer2}")
    print(f"r1 == r3: {primer1 == primer3}")
    print(f"r1 < r3: {primer1 < primer3}")

    print(f"r1 + r3 = {primer1 + primer3}")
    print(f"r1 - r3 = {primer1 - primer3}")
    print(f"r1 * r3 = {primer1 * primer3}")
    print(f"r1 / r3 = {primer1 / primer3}")

    print(f"r1 + 1 = {primer1 + 1}")
    print(f"2 * r1 = {2 * primer1}")

    primer4 = Rational(-1, 2)
    primer5 = Rational(1, -2)
    print(f"r4 = {primer4}")
    print(f"r5 = {primer5}")

    primer6 = Rational(0, 5)
    print(f"r6 = {primer6}")