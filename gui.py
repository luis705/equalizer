from kivy.config import Config
from kivy.lang import Builder
from kivymd.app import MDApp

Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', 0)
Config.write()

colors = {
    'Teal': {
        '200': '#212121',
        '500': '#212121',
        '700': '#212121',
    },
    'Red': {
        '200': '#C25554',
        '500': '#C25554',
        '700': '#C25554',
    },
    'Light': {
        'StatusBar': 'E0E0E0',
        'AppBar': '#202020',
        'Background': '#AAAAAA',
        'CardsDialogs': '#FFFFFF',
        'FlatButtonDown': '#CCCCCC',
    },
}

# creating Demo Class(base class)
class Equapyzer(MDApp):
    def build(self):
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.accent_palette = 'Red'
        return Builder.load_file('gui.kv')


if __name__ == '__main__':
    Equapyzer().run()
