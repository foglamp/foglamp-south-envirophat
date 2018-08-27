# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for EnviroHat 'poll' type plugin """

import copy
import datetime
import uuid
from envirophat import light, weather, motion       # unused: analog

from foglamp.common import logger
from foglamp.plugins.common import utils
from foglamp.services.south import exceptions


__author__ = "Ashwin Gopalakrishnan, Amarendra K Sinha"
__copyright__ = "Copyright (c) 2018 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'Enviro pHAT Poll Plugin',
        'type': 'string',
        'default': 'envirophat',
        'readonly': 'true'
    },
    'pollInterval': {
        'description': 'Interval between calls to the South device poll routine in milliseconds',
        'type': 'integer',
        'default': '1000',
        'order': '1'
    },
    'assetNamePrefix': {
        'description': 'Prefix of asset name',
        'type': 'string',
        'default': 'envirophat/',
        'order': '2'
    },
    'rgbSensor': {
        'description': 'Enable RGB sensor',
        'type': 'boolean',
        'default': 'true',
        'order': '3'
    },
    'rgbSensorName': {
        'description': 'Asset name of RGB sensor',
        'type': 'string',
        'default': 'rgb',
        'order': '4'
    },
    'magnetometerSensor': {
        'description': 'Enable magnetometer sensor',
        'type': 'boolean',
        'default': 'true',
        'order': '5'
    },
    'magnetometerSensorName': {
        'description': 'Asset name of magnetometer sensor',
        'type': 'string',
        'default': 'magnetometer',
        'order': '6'
    },
    'accelerometerSensor': {
        'description': 'Enable accelerometer sensor',
        'type': 'boolean',
        'default': 'true',
        'order': '7'
    },
    'accelerometerSensorName': {
        'description': 'Asset name of accelerometer sensor',
        'type': 'string',
        'default': 'accelerometer',
        'order': '8'
    },
    'weatherSensor': {
        'description': 'Enable weather sensor',
        'type': 'boolean',
        'default': 'true',
        'order': '9'
    },
    'weatherSensorName': {
        'description': 'Asset name of weather sensor',
        'type': 'string',
        'default': 'weather',
        'order': '10'
    },
}

_LOGGER = logger.setup(__name__, level=20)


def plugin_info():
    """ Returns information about the plugin.

    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'Enviro pHAT Poll Plugin',
        'version': '1.0',
        'mode': 'poll',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.

    Args:
        config: JSON configuration document for the South device configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    data = copy.deepcopy(config)
    return data


def plugin_poll(handle):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.

    Available for poll mode only.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document, as a Python dict, if it is available
        None - If no reading is available
    Raises:
        DataRetrievalError
    """

    unit = 'hPa'    # Pressure unit, can be either hPa (hectopascals) or Pa (pascals)
    time_stamp = utils.local_timestamp()
    data = list()
    asset_prefix = handle['assetNamePrefix']['value']

    try:
        if handle['rgbSensor']['value'] == 'true':
            rgb = light.rgb()
            data.append({
                'asset': '{}{}'.format(asset_prefix, handle['rgbSensorName']['value']),
                'timestamp': time_stamp,
                'key': str(uuid.uuid4()),
                'readings': {
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[2]
                }
            })
        if handle['magnetometerSensor']['value'] == 'true':
            magnetometer = motion.magnetometer()
            data.append({
                'asset': '{}{}'.format(asset_prefix, handle['magnetometerSensorName']['value']),
                'timestamp': time_stamp,
                'key': str(uuid.uuid4()),
                'readings': {
                    "x": magnetometer[0],
                    "y": magnetometer[1],
                    "z": magnetometer[2]
                }
            })
        if handle['accelerometerSensor']['value'] == 'true':
            accelerometer = [round(x, 2) for x in motion.accelerometer()]
            data.append({
                'asset': '{}{}'.format(asset_prefix, handle['accelerometerSensorName']['value']),
                'timestamp': time_stamp,
                'key': str(uuid.uuid4()),
                'readings': {
                    "x": accelerometer[0],
                    "y": accelerometer[1],
                    "z": accelerometer[2]
                }
            })
        if handle['weatherSensor']['value'] == 'true':
            altitude = weather.altitude()
            temperature = weather.temperature()
            pressure = weather.pressure(unit=unit)
            data.append({
                'asset': '{}{}'.format(asset_prefix, handle['weatherSensorName']['value']),
                'timestamp': time_stamp,
                'key': str(uuid.uuid4()),
                'readings': {
                    "altitude": altitude,
                    "temperature": temperature,
                    "pressure": pressure,
                }
            })
    except (Exception, RuntimeError) as ex:
        _LOGGER.exception("Enviro pHAT exception: {}".format(str(ex)))
        raise exceptions.DataRetrievalError(ex)

    return data


def plugin_reconfigure(handle, new_config):
    """  Reconfigures the plugin

    it should be called when the configuration of the plugin is changed during the operation of the South device service;
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info("Old config for Enviro pHAT plugin {} \n new config {}".format(handle, new_config))

    # Find diff between old config and new config
    diff = utils.get_diff(handle, new_config)

    # Plugin should re-initialize and restart if key configuration is changed
    if 'pollInterval' in diff:
        plugin_shutdown(handle)
        new_handle = plugin_init(new_config)
        new_handle['restart'] = 'yes'
    else:
        new_handle = copy.deepcopy(new_config)
        new_handle['restart'] = 'no'
    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    _LOGGER.info('Enviro pHAT poll plugin shut down.')
