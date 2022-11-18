import json
import os
from time import time
from tkinter.filedialog import askopenfilename, asksaveasfilename

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from kivy.config import Config
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.slider import MDSlider
from kivymd.uix.toolbar import MDTopAppBar

from eq import create_filter, process_signal

Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'fullscreen', 1)
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


class Back(MDBoxLayout):
    pass


class BackButtons(MDFloatLayout):
    pass


class Front(MDBoxLayout):
    pass


class GainLabel(MDLabel):
    pass


class GainSlider(MDSlider):
    pass


class TopBar(MDTopAppBar):
    pass


class Equapyzer(MDApp):
    def __init__(self):
        super().__init__()

        # Build .kv files
        self.kv_dir = 'gui_dir'
        for file in os.listdir(self.kv_dir):
            if file != 'main.kv':
                Builder.load_file(os.path.join(self.kv_dir, file))

        # Screen change time
        self.time = time()

        # Widgets references
        self.main = Builder.load_file(os.path.join(self.kv_dir, 'main.kv'))
        self.front = self.main.ids['gains']
        self.volume = self.front.ids['volume']
        self.back = self.main.ids['graph']
        self.in_menu_button = self.back.ids['back_buttons'].ids['in_menu']
        self.out_menu_button = self.back.ids['back_buttons'].ids['out_menu']
        self.sliders = self.front.ids
        self.sliders.pop('volume')

        # Equalizer values
        self.filter = []
        self.fs = 48000
        self.order = 2**16 + 1
        self.buffer = 8192

        # PyAudio api
        self.pa = pyaudio.PyAudio()
        info = self.pa.get_host_api_info_by_index(0)

        self.devices = [
            self.pa.get_device_info_by_host_api_device_index(0, i)
            for i in range(info.get('deviceCount'))
        ]
        self.input_device = self.pa.get_default_input_device_info()
        self.output_device = self.pa.get_default_output_device_info()
        self.stream = self.pa.open(
            format=pyaudio.paInt32,
            channels=1,
            rate=self.fs,
            input=True,
            output=True,
            stream_callback=self.callback,
            frames_per_buffer=self.buffer,
            input_device_index=self.input_device['index'],
            output_device_index=self.output_device['index'],
        )

        # Frequency response graph
        self.graph = self.back.ids['freq_resp']
        self.update_filter()

        # Dropdown menu config
        output_itens = [
            {
                'text': device.get('name'),
                'viewclass': 'OneLineListItem',
                'on_release': lambda x=device: self.out_menu_callback(x),
            }
            for device in self.devices
            if device.get('maxInputChannels') == 0
            and device.get('maxOutputChannels') > 0
        ]
        input_itens = [
            {
                'text': device.get('name'),
                'viewclass': 'OneLineListItem',
                'on_release': lambda x=device: self.in_menu_callback(x),
            }
            for device in self.devices
            if device.get('maxInputChannels') > 0
            and device.get('maxOutputChannels') == 0
        ]
        self.in_menu = MDDropdownMenu(
            caller=self.in_menu_button,
            items=input_itens,
            width_mult=4,
        )
        self.out_menu = MDDropdownMenu(
            caller=self.out_menu_button,
            items=output_itens,
            width_mult=4,
        )
        self.back.ids['back_buttons'].ids['in_menu'].text = (
            'Input device: ' + self.pa.get_default_input_device_info()['name']
        )
        self.back.ids['back_buttons'].ids['out_menu'].text = (
            'Output device: '
            + self.pa.get_default_output_device_info()['name']
        )

    def build(self):
        # Setup profiles dir
        self.profile_dir = 'profiles'
        if not os.path.exists(self.profile_dir):
            os.mkdir(self.profile_dir)

        # Setup theme
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.accent_palette = 'Red'

        return self.main

    def update_filter(self):
        self.stream.stop_stream()
        for key, value in self.sliders.items():
            if value.active:
                return
        # Adjust sound level
        self.gain = 100 - self.volume.value

        # Get eq gains
        frequencies = list(self.sliders.keys())
        gains = [self.sliders[freq].value for freq in frequencies]
        frequencies = list(
            map(lambda freq: int(freq[: freq.find('Hz')]), frequencies)
        )

        # Add low-pass filter
        frequencies.insert(0, 0)
        frequencies.append(self.fs / 2)
        gains.insert(0, 0)
        gains.append(-100)

        # Calculate filter coeficients
        temp = create_filter(
            np.array(frequencies), np.array(gains), self.fs, self.order
        )
        self.filter = temp
        self.stream.start_stream()

    def plot(self):
        plt.close()
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.patch.set_facecolor('#AAAAAA')
        fig.patch.set_facecolor('#AAAAAA')
        gains = np.abs(np.fft.rfft(self.filter))
        frequencies = np.fft.rfftfreq(len(self.filter)) * self.fs
        magnitude = np.multiply(20, np.log10(gains))
        plt.semilogx(
            frequencies,
            magnitude,
            color='#212121',
        )
        plt.title('Frequency analysis')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude (dB)')
        plt.xlim([20, 20000])
        plt.ylim([-18, 15])
        plt.yticks([-12, -9, -6, -3, 0, 3, 6, 9, 12])
        plt.grid(True, which='both', color='#212121', alpha=0.2)
        plt.xticks(
            [20, 100, 1000, 2000, 10000, 20000],
            ['20', '100', '1K', '2K', '10K', '20K'],
        )

        # Broad ranges
        # Bass
        rect = mpatches.Rectangle(
            (20.4, -18), 225.2, 2, fill=True, facecolor='#357266'
        )
        plt.gca().add_patch(rect)
        plt.text(
            70,
            -17.25,
            'Bass',
            fontsize=10,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Mid
        rect = mpatches.Rectangle(
            (255, -18),
            1710,
            2,
            fill=True,
            facecolor='#357266',
        )
        plt.gca().add_patch(rect)
        plt.text(
            700,
            -17.25,
            'Mid',
            fontsize=10,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Treble
        rect = mpatches.Rectangle(
            (2040, -18),
            17960,
            2,
            fill=True,
            facecolor='#357266',
        )
        plt.gca().add_patch(rect)
        plt.text(
            6000,
            -17.25,
            'Treble',
            fontsize=10,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Specific ranges
        # Low bass
        rect = mpatches.Rectangle(
            (20.4, -15.75),
            38,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            33,
            -15,
            'Low-Bass',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Mid bass
        rect = mpatches.Rectangle(
            (61.2, -15.75),
            55,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            85,
            -15,
            'Mid-Bass',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # High bass
        rect = mpatches.Rectangle(
            (120, -15.75),
            370,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            250,
            -15,
            'High-Bass',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Mid-mid
        rect = mpatches.Rectangle(
            (510, -15.75),
            480,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            710,
            -15,
            'Mid-mid',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # High-mid
        rect = mpatches.Rectangle(
            (1020, -15.75),
            945,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            1420,
            -15,
            'High-mid',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Low-treble
        rect = mpatches.Rectangle(
            (2040, -15.75),
            2920,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            3050,
            -15,
            'Low-treble',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # Mid-treble
        rect = mpatches.Rectangle(
            (5000, -15.75),
            4840,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            7000,
            -15,
            'Mid-treble',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

        # High-treble
        rect = mpatches.Rectangle(
            (10200, -15.75),
            9800,
            2,
            fill=True,
            facecolor='#945600',
        )
        plt.gca().add_patch(rect)
        plt.text(
            14500,
            -15,
            'High-treble',
            fontsize=8,
            color='#212121',
            verticalalignment='center',
            horizontalalignment='center',
        )

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

        self.update_filter()
        self.change_screen()

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

        self.change_screen()

    def change_screen(self):
        if time() - self.time < 0.5:
            return
        if self.root.current == 'graph':
            self.root.current = 'gains'
            self.main.transition.direction = 'up'
        elif self.root.current == 'gains':
            self.root.current = 'graph'
            self.main.transition.direction = 'down'
            self.plot()
        self.time = time()

    def in_menu_callback(self, text_item):
        self.input_device = text_item
        self.stream.stop_stream()
        self.stream = self.pa.open(
            format=pyaudio.paInt32,
            channels=1,
            rate=self.fs,
            input=True,
            output=True,
            stream_callback=self.callback,
            frames_per_buffer=self.buffer,
            input_device_index=self.input_device['index'],
            output_device_index=self.output_device['index'],
        )
        self.back.ids['back_buttons'].ids['in_menu'].text = (
            'Input device: ' + self.input_device['name']
        )
        self.in_menu.dismiss()

    def out_menu_callback(self, text_item):
        self.output_device = text_item
        self.stream.stop_stream()
        self.stream = self.pa.open(
            format=pyaudio.paInt32,
            channels=1,
            rate=self.fs,
            input=True,
            output=True,
            stream_callback=self.callback,
            frames_per_buffer=self.buffer,
            input_device_index=self.input_device['index'],
            output_device_index=self.output_device['index'],
        )
        self.back.ids['back_buttons'].ids['out_menu'].text = (
            'Output device: ' + self.output_device['name']
        )
        self.out_menu.dismiss()

    def callback(self, in_data, frame_count, time_info, status):
        in_data = np.frombuffer(in_data, dtype=np.int32)
        if np.max(np.abs(in_data)) < 35000000:
            return (np.zeros_like(in_data), pyaudio.paContinue)

        out_data = process_signal(
            in_data, self.filter, self.volume.value / 100
        ).astype(np.int32)
        return (out_data, pyaudio.paContinue)
