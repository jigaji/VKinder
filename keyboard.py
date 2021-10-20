

class Keyboards:
    def __init__(self):
        pass
    def get_keyboard(self, path):
        with open(f'Keyboards/{path}.json', 'r', encoding='UTF-8') as kb:
            return kb.read()
