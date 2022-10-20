import os

import matplotlib.pyplot as plt
import numpy as np
from kivy.config import Config
from kivy.core.window import Window
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.backdrop.backdrop import (
    MDBackdropBackLayer,
    MDBackdropFrontLayer,
)

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
        'A700': '#C25554',
    },
    'Light': {
        'StatusBar': '#E0E0E0',
        'AppBar': '#AAAAAA',
        'Background': '#AAAAAA',  # Fundo da tela
        'CardsDialogs': '#FFFFFF',
        'FlatButtonDown': '#CCCCCC',
    },
}


class Front(MDBackdropFrontLayer):
    pass


class Back(MDBackdropBackLayer):
    pass


class Create(MDBackdropBackLayer):
    pass


class Equapyzer(MDApp):
    def build(self):
        # Initialization
        self.kv_dir = 'gui_dir'
        for file in os.listdir(self.kv_dir):
            if file != 'main.kv':
                Builder.load_file(os.path.join(self.kv_dir, file))
        self.profile_dir = 'profiles'

        if not os.path.exists(self.profile_dir):
            os.mkdir(self.profile_dir)

        # Theme
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.accent_palette = 'Red'

        # Screen sizes
        self.main_size = (1280, 720)
        self.create_size = (400, 600)

        # Widget references
        self.main = Builder.load_file(os.path.join(self.kv_dir, 'main.kv'))
        self.front = self.main.ids['front']
        self.back = self.main.ids['back']

        # Eq values
        self.filter = []
        self.fs = 98000
        self.order = 2**10 + 1

        # Frequency response graph
        self.graph = self.back.ids['freq_resp']

        # Create first filter
        self.update_filter()

        return self.main

    def update_filter(self):
        # Adjust sound level
        try:
            gain = 0.01 / self.front.ids['volume'].value
        except ZeroDivisionError:
            gain = -10000000000

        # Get eq gains
        frequencies = list(
            filter(lambda id: 'Hz' in id, list(self.front.ids.keys()))
        )
        gains = [
            self.front.ids[frequencies[i]].value - gain
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
        self.plot()

    def plot(self):
        plt.close()
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.patch.set_facecolor('#AAAAAA')
        fig.patch.set_facecolor('#AAAAAA')

        plt.plot(
            np.fft.rfftfreq(len(self.filter)) * self.fs,
            10 * np.log10(abs(np.fft.rfft(self.filter))),
            color='#212121',
        )
        plt.title('Frequency analysis')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Filter Magnitude Response (dB)')
        plt.xlim([20, 20000])

        # plt.grid(True, which='both', color="#212121")

        while len(self.graph.children) != 0:
            self.graph.remove_widget(self.graph.children[0])
        self.graph.add_widget(FigureCanvasKivyAgg(plt.gcf()))

    def load_profile(self):
        ...

    def save_profile(self):
        try:
            gain = 0.01 / self.front.ids['volume'].value
        except ZeroDivisionError:
            gain = -10000000000
        # Get eq gains
        frequencies = list(
            filter(lambda id: 'Hz' in id, list(self.front.ids.keys()))
        )
        gains = [
            self.front.ids[frequencies[i]].value - gain
            for i, _ in enumerate(frequencies)
        ]
        frequencies = list(
            map(lambda freq: int(freq[: freq.find('Hz')]), frequencies)
        )

        to_save = {
            frequency: gain for frequency, gain in zip(frequencies, gains)
        }

    def change_screen(self):
        if self.root.current == 'create':
            self.root.current = 'main'
            self.main.ids['create'].manager.transition.direction = 'left'
            Window.size = self.main_size
        else:
            self.root.current = 'create'
            Window.size = self.create_size


if __name__ == '__main__':
    Equapyzer().run()
