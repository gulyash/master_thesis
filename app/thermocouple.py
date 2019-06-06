import datetime
from bisect import bisect_left
from collections import deque


class Thermocouple:
    """
    Each thermocouple stores its own x and y coordinates, label, mold side name,
    current status and temperature and temperature history
    """
    history_size = 500

    def __init__(self, x, y, label, side):
        self.x = x
        self.y = y
        self.label = label
        self.text_label = f'TC {label}'
        self.mold_side = side
        self.status = ''
        self.temperature = None
        self.history = deque(maxlen=self.history_size)

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'label': self.label,
            'text_label': self.text_label,
            'mold_side': self.mold_side,
            'status': self.status,
            'temperature': self.temperature,
        }

    def update(self, temperature, status, time):
        """
        Update thermocouple temperature and status.

        :param temperature: new temperature value
        :param status: new status value
        :param time: current time value
        :return: None
        """
        self.temperature = temperature
        self.history.append({
            'temperature': temperature,
            'time': time
        })
        if status == 67:
            self.status = 'Disconnected'
        elif status == 0:
            self.status = 'OK'

    def find_threshold_index(self, time_threshold):
        """
        Each thermocouple has a deck that stores temperature and the time the reading was performed.
        This method returns the index of the element so that the difference between
        the time of that element and the current time is bigger than passed time threshold value.

        :param time_threshold: used for comparison of difference between current time and the time of the reading
        :return: bound index or None if the history is too short for such index
        """
        current_datetime_str = self.history[-1]['time']
        current_datetime = datetime.datetime.fromisoformat(current_datetime_str)
        bound_datetime = current_datetime - time_threshold
        dts = [record['time'] for record in self.history]
        dts = list(map(datetime.datetime.fromisoformat, dts))

        bound_index = bisect_left(dts, bound_datetime) - 1

        datestr = self.history[bound_index]['time']
        date = datetime.datetime.fromisoformat(datestr)
        if current_datetime - date > time_threshold:
            return bound_index
        return None

    def get_test_status(self, time_threshold_index, temperature_threshold):
        """
        Check if thermocouple is tested.

        :param time_threshold_index: used for checking if thermocouple is heated
        :param temperature_threshold: used for checking if thermocouple is heated
        :return: dictionary with boolean check result and data for creating a tc test if thermocouple is heated
        """
        result = {
            'is_tested': False,
            'data': None
        }
        current_temp = self.history[-1]['temperature']
        init_temp = self.history[time_threshold_index]['temperature']
        if init_temp and current_temp and current_temp - init_temp > temperature_threshold:
            data = {
                'init_time': self.history[time_threshold_index]['time'],
                'start_time': self.history[-1]['time'],
                'start_temperature': self.history[-1]['temperature'],
            }
            result = {
                'is_tested': True,
                'data': data
            }
        return result

    def get_test_completion_status(self, time_threshold, temperature_threshold, test):
        """

        :param time_threshold: used for checking if thermocouple test is successful
        :param temperature_threshold: used for checking for thermocouple test timeout
        :param test: TcTest instance
        :return: test completion info - boolean is_complete value and test completion message
        """
        current_time_str = self.history[-1]['time']
        current_time = datetime.datetime.fromisoformat(current_time_str)
        test_start_time = datetime.datetime.fromisoformat(test.start_time)

        current_temp = self.history[-1]['temperature']
        if current_time - test_start_time > time_threshold:
            return {
                'is_complete': True,
                'message': 'time out',
            }
        elif current_temp - test.start_temperature > temperature_threshold:
            return {
                'is_complete': True,
                'message': 'complete',
            }
        else:
            return {
                'is_complete': False,
                'message': 'testing'
            }
