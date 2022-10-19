import numpy as np
from kivy.config import Config
from kivy.lang import Builder
from kivymd.app import MDApp

from eq import create_filter

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

KV = """
BoxLayout:
    Button:
        id: my_button
        text: "let's try !"
"""


class Equapyzer(MDApp):
    def build(self):
        # Theme
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.accent_palette = 'Red'
        self.screen = Builder.load_file('gui.kv')

        # Eq values
        self.filter = []
        self.fs = 98000
        self.order = 2**10 + 1

        # Create first filter
        self.update_filter()

        return self.screen

    def update_filter(self):
        # Adjust sound level
        try:
            gain = 0.01 / self.screen.ids['volume'].value
        except ZeroDivisionError:
            gain = -10000000000

        # Get eq gains
        frequencies = list(
            filter(lambda id: 'Hz' in id, list(self.screen.ids.keys()))
        )
        gains = [
            self.screen.ids[frequencies[i]].value - gain
            for i, _ in enumerate(frequencies)
        ]
        frequencies = list(
            map(lambda freq: int(freq[: freq.find('Hz')]), frequencies)
        )

        # Add passband filter
        frequencies.insert(0, 0)
        frequencies.append(self.fs / 2)
        gains.insert(0, -100)
        gains.append(-100)

        # Create filter
        self.filter = create_filter(
            np.array(frequencies), np.array(gains), self.fs, self.order
        )
        print(self.filter)


if __name__ == '__main__':
    Equapyzer().run()
