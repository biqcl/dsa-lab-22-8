class IncorrectTriangleSides(Exception):
    pass

class Triangle:
    def __init__(self, a, b, c):
        """
        Инициализирует треугольник с заданными сторонами.
        
        Аргументы:
            a, b, c (int или float): длины сторон треугольника
            
        Выбрасывает:
            IncorrectTriangleSides: если стороны некорректны
        """
        if not (a > 0 and b > 0 and c > 0):
            raise IncorrectTriangleSides("Стороны должны быть положительными")
        if not (a + b > c and a + c > b and b + c > a):
            raise IncorrectTriangleSides("Сумма любых двух сторон должна быть больше третьей")
        
        self.a = a
        self.b = b
        self.c = c
    
    def triangle_type(self):
        """
        Возвращает тип треугольника.
        
        Возвращает:
            str: "equilateral", "isosceles" или "nonequilateral"
        """
        if self.a == self.b == self.c:
            return "equilateral"
        elif self.a == self.b or self.a == self.c or self.b == self.c:
            return "isosceles"
        else:
            return "nonequilateral"
    
    def perimeter(self):
        """
        Вычисляет периметр треугольника.
        
        Возвращает:
            int или float: периметр треугольника
        """
        return self.a + self.b + self.c
    