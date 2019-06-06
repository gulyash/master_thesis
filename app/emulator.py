from datetime import datetime


class Emulator:

    def __init__(self, thermocouple_count) -> None:
        super().__init__()
        self.thermocouple_count = thermocouple_count

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
        state = {
            label: {
                'status': 0,
                'temperature': 25.2,
            } for label in range(1, self.thermocouple_count + 1)
        }
        state[14] = {
            'status': 0,
            'temperature': 30
        }
        state[15] = {
            'status': 67,
            'temperature': None
        }

        current_time = datetime.now().isoformat()
        result = {'time': current_time,
                  'state': state}
        return result

    def get_mould_side_states(self):
        result = {
            side_name: 'No error'
            for side_name in ['Left', 'Right', 'Fixed', 'Loose']
        }
        return result
