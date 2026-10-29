from ursina import Entity, Vec3, color, time


class dicionario(Entity):
    def __init__(self, position=Vec3(0, 0, 0), speed=15, direction=Vec3(0, 0, 0)):
        super().__init__(
            model="models/book.glb",
            scale=0.7,
            rotation_z=10,
            position=position,
            collider="box",
        )

        self.direction = Vec3(direction)
        self.velocity = self.direction * speed
        self.gravidade = 6

    def update(self):
        pass