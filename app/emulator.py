from datetime import datetime


class TCEmu:
    def __init__(self, label, status=0) -> None:
        super().__init__()
        self.temperature = 25.2
        self.label = label
        self.status = status


class Heating:
    def __init__(self, tc,
                 heating_degrees=10.2,
                 heating_time=3,
                 cooling_time=10):
        self.tc = tc
        self.start_time = datetime.now()
        self.start_temperature = tc.temperature
        self.heating_degrees = heating_degrees
        self.heating_time = heating_time
        self.cooling_time = cooling_time
        self.total_seconds = self.heating_time + self.cooling_time
        self.heating_speed = self.heating_degrees / self.heating_time
        self.cooling_speed = self.heating_degrees / self.cooling_time

    def update(self):
        if self.time < self.heating_time:
            self.tc.temperature = round(self.start_temperature + self.time * self.heating_speed, 1)
        else:
            self.tc.temperature = round(self.start_temperature + self.heating_degrees - (
                    self.time - self.heating_time) * self.cooling_speed, 1)

    @property
    def time(self):
        return (datetime.now() - self.start_time).total_seconds()

    def is_done(self):
        return self.time > self.total_seconds


class Emulator:

    def __init__(self, thermocouple_count) -> None:
        super().__init__()
        self.thermocouple_count = thermocouple_count
        self.tcs = [TCEmu(label) for label in range(1, thermocouple_count + 1)]
        self.tcs[15].status = 67
        self.start_time = datetime.now()

        heating_modes = {
            'demo': self._get_demo_process(),
            'successful': self._get_successful_process_dummy(),
            'no_heating': {},
            'manual': self._get_manual_test_process(),
        }
        slave_status_modes = {
            'ok': self._get_ok_side_states(),
            'with_errors': self._get_demo_side_states()
        }

        self.heatings = {}
        self.heating_emulation = heating_modes['manual']
        self.slave_statuses = slave_status_modes['ok']

    def _get_successful_process_dummy(self):
        tc_step = 2
        horizontal_rows_num = 3
        wide_side_horz_row_len = 9
        wide_side_tc_count = wide_side_horz_row_len * horizontal_rows_num
        wide_side_time = wide_side_tc_count * tc_step

        narrow_side_horz_row_len = 2
        narrow_side_tc_count = narrow_side_horz_row_len * horizontal_rows_num
        narrow_side_time = narrow_side_tc_count * tc_step

        side_step = 7
        return {
            # fixed horizontal
            **{sec: {'label': label} for sec, label in zip(range(1, wide_side_time + 1, tc_step),
                                                           [
                                                               *list(range(14, 23)),
                                                               *list(range(36, 45)),
                                                               *list(range(58, 67)),
                                                           ])},
            # left vertical
            **{sec: {'label': label} for sec, label in
               zip(range(wide_side_time + side_step, wide_side_time + side_step + narrow_side_time, tc_step),
                   [1, 23, 45, 2, 24, 46])},
            # loose horizontal
            **{sec: {'label': label} for sec, label in
               zip(range(wide_side_time + 2 * side_step + narrow_side_time,
                         2 * wide_side_time + 2 * side_step + narrow_side_time, tc_step),
                   [
                       *list(range(3, 12)),
                       *list(range(25, 34)),
                       *list(range(47, 56)),
                   ])},
            # right vertical
            **{sec: {'label': label} for sec, label in
               zip(range(2 * wide_side_time + 3 * side_step + narrow_side_time,
                         2 * wide_side_time + 3 * side_step + 2 * narrow_side_time, tc_step),
                   [12, 34, 56, 13, 35, 57])},

        }

    def _get_manual_test_process(self):
        return {
            10: {'label': 38},
            20: {'label': 39,
                 'heating_time': 2,
                 'heating_degrees': 4
                 }
        }

    def _get_demo_process(self):
        return {
            1: {'label': 14,
                'heating_time': 2,
                'heating_degrees': 5
                },
            15: {'label': 15},
            35: {'label': 38},
            50: {'label': 17},
            70: {'label': 36},
            77: {'label': 58},
            82: {'label': 37},
            87: {'label': 59},
        }

    @property
    def _seconds_since_start(self):
        return (datetime.now() - self.start_time).total_seconds()

    def _update_fake_data(self):
        # check if a new heating must be started
        for heating_start_moment in self.heating_emulation.copy().keys():
            if self._seconds_since_start >= heating_start_moment:
                heating_info = self.heating_emulation.pop(heating_start_moment)
                label = heating_info.pop('label')
                if not self.heatings.get(label):
                    self.heatings[label] = Heating(self.tcs[label - 1], **heating_info)

        # update every heating
        for heating in self.heatings.copy().values():
            heating.update()
            if heating.is_done():
                self.heatings.pop(heating.tc.label)

    def get_sensor_data(self):
        self._update_fake_data()

        state = {
            tc.label: {
                'status': tc.status,
                'temperature': tc.temperature if tc.status == 0 else None,
            } for tc in self.tcs
        }
        current_time = datetime.now().isoformat()
        result = {'time': current_time,
                  'state': state}
        return result

    def _get_demo_side_states(self):
        return {
            'Fixed': 'No error',
            'Left': 'Station deactivated',
            'Loose': 'Invalid slave response',
            'Right': 'Station not ready'
        }

    def _get_ok_side_states(self):
        return {
            side_name: 'No error'
            for side_name in ['Left', 'Right', 'Fixed', 'Loose']
        }

    def get_mould_side_states(self):
        return self.slave_statuses
