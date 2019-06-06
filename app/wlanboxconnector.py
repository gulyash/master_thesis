import configparser
import datetime
import json
import os
from ctypes import Array, c_uint8

import pyads
from pyads import ADSError
from typing import Type

from pyCommonlySharedCode.generalFunctions import get_mould_config_dir, \
    get_plantdatadir_and_plantconfig


def PLCTYPE_ARR_USINT(n):
    # type: (int) -> Type[Array[c_uint8]]
    # Return an array with n usint values.
    return c_uint8 * n


class TwinCatConfigError(Exception):
    pass


class TwinCatConnectionInfo:
    def __init__(self, ams_net_id, first_offset, slave_status_offset, slaves_order) -> None:
        super().__init__()
        self.ams_net_id = ams_net_id
        # 0xF020 - process image of the physical inputs
        self.index_group = 0xF020
        self.first_offset = first_offset
        self.slave_status_offset = slave_status_offset
        self.slaves_order = slaves_order

    @classmethod
    def from_twincat_config(cls):
        plant_data_db_dir, mould_config = get_plantdatadir_and_plantconfig()
        mould_cfg_dir = get_mould_config_dir(plant_data_db_dir, mould_config)

        cfg_path = os.path.join(mould_cfg_dir, 'MSD', 'TwinCat_Config.ini')
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)

        if cfg.has_section('twincat'):
            section = 'twincat'
        else:
            raise KeyError(f'Can not find section [twincat] in {cfg_path}.')

        d = {}
        if cfg.has_option(section, 'ams_net_id'):
            d['ams_net_id'] = cfg.get(section, 'ams_net_id')
        else:
            raise KeyError(
                f'{cfg_path} did not contain key ams_net_id in section [{section}]')
        for key in ['first_offset', 'slave_status_offset']:
            if cfg.has_option(section, key):
                d[key] = int(cfg.get(section, key), 16)
            else:
                raise KeyError(
                    f'{cfg_path} did not contain key {key} in section [{section}]')
        if cfg.has_option(section, 'slaves_order'):
            slaves_order = json.loads(cfg.get(section, 'slaves_order'))
            if not len(slaves_order) == 4:
                raise TwinCatConfigError(
                    f'4 sides must present in the slaves_order param in TwinCat_Config, '
                    f'{len(slaves_order)} were specified.')
            correct_mold_side_names = ('fixed', 'loose', 'right', 'left')
            for mold_side in slaves_order:
                if mold_side.lower() not in correct_mold_side_names:
                    raise TwinCatConfigError(f'{mold_side} is not a valid side name.')
            d['slaves_order'] = [slave.capitalize() for slave in slaves_order]
        else:
            raise KeyError(
                f'{cfg_path} did not contain key slaves_order in section [{section}]')
        return cls(d['ams_net_id'], d['first_offset'], d['slave_status_offset'], d['slaves_order'])


class WLANBoxConnector:
    slave_status_meaning = {
        0: 'No error',
        1: 'Station deactivated',
        2: 'Station not exists',
        3: 'Master lock',
        4: 'Invalid slave response',
        5: 'Parameter fault',
        6: 'Not supported',
        7: 'Config fault',
        8: 'Station not ready',
        9: 'Static diagnosis',
        10: 'Diagnosis overflow',
        11: 'Physical fault',
        12: 'Data - Exchange left',
        13: 'Severe bus fault',
        14: 'Telegram fault',
        15: 'Station has no resources',
        16: 'Service not activated',
        17: 'Unexpected telegram',
        18: 'Station ready',
        128: 'slave, waiting for data transfer',
        129: 'slave, waiting for configuration',
        130: 'slave, waiting for parameter'
    }

    def __init__(self, thermocouples_count) -> None:
        super().__init__()
        self.twincat_info = TwinCatConnectionInfo.from_twincat_config()
        self.plc = pyads.Connection(self.twincat_info.ams_net_id, pyads.PORT_SPECIALTASK1)
        self.thermocouples_count = thermocouples_count
        self.status_datatype = pyads.PLCTYPE_USINT
        self.value_datatype = pyads.PLCTYPE_UINT
        self.channel_size = 3

    def get_sensor_data(self):
        """
        Get values and statuses returned by all thermocouples whether they are connected or not.

        :return:
        {
            "time": time when measure is taken
            "state": {
                "tc_label": {
                    "status": status of a thermocouple
                    "temperature": temperature value
                    }
                }
        }
        """
        twincat = self.twincat_info
        try:
            # get array
            with self.plc as plc:
                array = plc.read(twincat.index_group, twincat.first_offset,
                                 PLCTYPE_ARR_USINT(self.thermocouples_count * self.channel_size))
                # parse array
                state = self.parse_sensor_data_array(array)
        except ADSError as e:
            print("Looks like you're disconnected. :(\nPlease, run TwinCAT. Error msg: ", e.msg)
            state = {}
        current_time = datetime.datetime.now().isoformat()
        result = {'time': current_time,
                  'state': state}
        return result

    def parse_sensor_data_array(self, array):
        state = {}
        for i in [num * self.channel_size for num in range(0, self.thermocouples_count)]:
            status = array[i]
            # little endian :(
            thermocouple_value = array[i + 1] + array[i + 2] * 256
            temperature = thermocouple_value / 10

            if status != 0:
                temperature = None
            label = i // 3 + 1
            data = {
                'status': status,
                'temperature': temperature,
            }
            state[label] = data
        return state

    def get_mould_side_states(self):
        twincat = self.twincat_info
        slaves_count = len(self.twincat_info.slaves_order)
        try:
            with self.plc as plc:
                array = plc.read(twincat.index_group, twincat.slave_status_offset,
                                 PLCTYPE_ARR_USINT(slaves_count))
            result = {}
            for index in range(slaves_count):
                value = array[index]
                status = self.slave_status_meaning[value]
                side_name = twincat.slaves_order[index]
                result[side_name] = status
        except ADSError as e:
            print("Looks like you're disconnected. :(\nPlease, run TwinCAT. Error msg: ", e.msg)
            result = {
                side_name: self.slave_status_meaning[1]
                for side_name in twincat.slaves_order
            }
        return result
