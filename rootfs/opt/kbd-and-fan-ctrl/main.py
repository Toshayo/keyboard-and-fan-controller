import json
import os.path

from xdg.BaseDirectory import xdg_config_home

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


BACKLIGHT_MODES = {
    'Static': {
        'id': 0,
        'speed': 0,
        'direction': 0
    },
    'Breathing': {
        'id': 1,
        'direction': 1,
    },
    'Neon': {
        'id': 2,
        'direction': 1,
        'color': 0x000000,
    },
    'Wave': {
        'id': 3,
        'color': 0x000000,
    },
    'Shifting': {
        'id': 4,
    },
    'Zoom': {
        'id': 5,
        'direction': 1,
    },
    'Meteor': {
        'id': 6,
        'direction': 1,
    },
    'Twinkling': {
        'id': 7,
        'direction': 1,
    },
}
ALLOWED_SPEED_VALUES = [1, 3, 5, 7, 9]
DEFAULT_CONFIG = {
    'mode': 0,
    'speed': 0,
    'direction': 0,
    'color': 0xFFFFFF,
    'fanMode': 0,
    'fanSpeed': [50, 50]
}


def get_config() -> dict:
    if os.path.exists(os.path.join(xdg_config_home, 'kbd-and-fan-ctrl-config.json')):
        with open(os.path.join(xdg_config_home, 'kbd-and-fan-ctrl-config.json'), 'r') as file:
            conf = json.load(file)
            for key, value in DEFAULT_CONFIG.items():
                if key not in conf:
                    conf[key] = value
            return conf
    else:
        return DEFAULT_CONFIG


def save_config():
    global config
    with open(os.path.join(xdg_config_home, 'kbd-and-fan-ctrl-config.json'), 'w') as file:
        json.dump(config, file)


def on_backlight_mode_changed(combo: Gtk.ComboBoxText):
    global builder, config
    mode_definition = BACKLIGHT_MODES[combo.get_active_text()]
    builder.get_object('backlightSpeed').set_sensitive('speed' not in mode_definition)
    builder.get_object('backlightColor').set_sensitive('color' not in mode_definition)
    builder.get_object('backlightDirection').set_sensitive('direction' not in mode_definition)


def on_backlight_speed_changed(slider: Gtk.Scale):
    slider.set_value(round(slider.get_value()))


def on_backlight_config_save(button):
    global builder, config

    mode: Gtk.ComboBoxText = builder.get_object('backlightMode')
    mode_definition = BACKLIGHT_MODES[mode.get_active_text()]
    config['mode'] = mode_definition['id']

    slider: Gtk.Scale = builder.get_object('backlightSpeed')
    if 'speed' not in mode_definition:
        config['speed'] = ALLOWED_SPEED_VALUES[int(slider.get_value()) - 1]
    else:
        config['speed'] = mode_definition['speed']

    if 'color' not in mode_definition:
        color_button: Gtk.ColorButton = builder.get_object('backlightColor')
        config['color'] = ((int(color_button.get_rgba().red * 255) << 16) +
                           (int(color_button.get_rgba().green * 255) << 8) +
                           int(color_button.get_rgba().blue * 255))
    else:
        config['color'] = mode_definition['color']

    if 'direction' not in mode_definition:
        direction: Gtk.ComboBoxText = builder.get_object('backlightDirection')
        config['direction'] = direction.get_active() + 1
    else:
        config['direction'] = mode_definition['direction']
    save_config()
    with open('/dev/acer-nitro17_kbd', 'wb') as file:
        file.write(config['mode'].to_bytes(1, byteorder='big'))
        file.write(config['speed'].to_bytes(1, byteorder='big'))
        file.write(b'\x64')
        file.write(config['direction'].to_bytes(1, byteorder='big'))
        file.write(config['color'].to_bytes(3, byteorder='big'))


def on_fan_mode_changed(combo: Gtk.ComboBoxText):
    global builder, config
    is_manual = combo.get_active() == 2
    builder.get_object('fan0Speed').set_sensitive(is_manual)
    builder.get_object('fan1Speed').set_sensitive(is_manual)


def on_fan_config_save(button):
    global builder, config
    config['fanMode'] = builder.get_object('fanMode').get_active()
    config['fanSpeed'][0] = int(builder.get_object('fan0Speed').get_value())
    config['fanSpeed'][1] = int(builder.get_object('fan1Speed').get_value())
    save_config()
    for i in range(2):
        with open('/dev/acer-nitro17_fan', 'wb') as file:
            file.write(config['fanMode'].to_bytes(1, byteorder='big'))
            file.write(i.to_bytes(1, byteorder='big'))
            file.write(config['fanSpeed'][i].to_bytes(1, byteorder='big'))


if __name__ == '__main__':
    config = get_config()

    builder = Gtk.Builder()
    builder.add_from_file('mainwindow.glade')
    builder.connect_signals({
        'onWindowClosed': Gtk.main_quit,
        'onBacklightModeChanged': on_backlight_mode_changed,
        'onBacklightSpeedChanged': on_backlight_speed_changed,
        'onBacklightConfigSave': on_backlight_config_save,
        'onFanModeChanged': on_fan_mode_changed,
        'onFanConfigSave': on_fan_config_save,
    })
    builder.get_object('backlightMode').set_active(config['mode'])
    on_backlight_mode_changed(builder.get_object('backlightMode'))
    builder.get_object('backlightSpeed').set_value(config['speed'])
    color = Gdk.RGBA()
    color.parse('#' + hex(config['color'])[2:].rjust(6, '0'))
    builder.get_object('backlightColor').set_rgba(color)
    builder.get_object('backlightDirection').set_active(max(0, config['direction'] - 1))
    builder.get_object('fanMode').set_active(config['fanMode'])
    for i in range(2):
        builder.get_object('fan' + str(i) + 'Speed').set_value(config['fanSpeed'][i])
    builder.get_object('mainWindow').show_all()
    Gtk.main()
