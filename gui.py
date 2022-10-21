import json
import os
from tkinter.filedialog import askopenfilename, asksaveasfilename

import matplotlib.pyplot as plt
import numpy as np
from kivy.config import Config
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout

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


class Front(MDBoxLayout):
    pass


class Back(MDBoxLayout):
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

        # Widget references
        self.main = Builder.load_file(os.path.join(self.kv_dir, 'main.kv'))
        self.front = self.main.ids['gains']
        self.back = self.main.ids['graph']

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
        # Get eq gains
        frequencies = list(
            filter(lambda id: 'Hz' in id, list(self.front.ids.keys()))
        )
        gains = [self.front.ids[freq].value for freq in frequencies]
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
        path = askopenfilename(
            title='Select profile',
            initialdir=self.profile_dir,
            filetypes=[['json file', '.json']],
        )
        if not path:
            return

        with open(path, 'r') as f:
            gains = json.loads(f.read())

        for freq, gain in gains.items():
            self.front.ids[freq + 'Hz'].value = gain

        self.go_to_main()

    def save_profile(self):
        # Get eq gains
        frequencies = list(
            filter(lambda id: 'Hz' in id, list(self.front.ids.keys()))
        )
        gains = [
            self.front.ids[frequencies[i]].value
            for i, _ in enumerate(frequencies)
        ]
        frequencies = list(
            map(lambda freq: int(freq[: freq.find('Hz')]), frequencies)
        )

        to_save = {
            frequency: gain for frequency, gain in zip(frequencies, gains)
        }

        path = asksaveasfilename(
            initialdir=self.profile_dir,
            title='Select File',
            filetypes=[['json file', '.json']],
        )
        if not path:
            return
        with open(path, 'w') as f:
            f.write(json.dumps(to_save))

    def go_to_graph(self):
        # Select direction
        match self.root.current:
            case 'gains':
                dir = 'down'
            case 'create':
                dir = 'right'

        self.root.current = 'graph'
        self.main.transition.direction = dir

    def go_to_main(self):
        self.root.current = 'gains'
        self.main.transition.direction = 'up'
