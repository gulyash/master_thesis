from datetime import datetime


class TCEmu:
    def __init__(self, label, status=0) -> None:
        super().__init__()
        self.temperature = 25.2
        self.label = label
        self.status = status


class Heating:
    def __init__(self, tc):
        self.tc = tc
        self.start_time = datetime.now()
        self.start_temperature = tc.temperature
        self.max_temperature_reached = None
        self.cooling_speed = None


class Emulator:

    def __init__(self, thermocouple_count) -> None:
        super().__init__()
        self.thermocouple_count = thermocouple_count
        self.tcs = [TCEmu(label) for label in range(1, thermocouple_count + 1)]
        self.tcs[15].status = 67

        self.start_time = datetime.now()
        self.timing = {
            14: 1,
            15: 20,
            18: 40,
            36: 60,
            58: 75,
            37: 90,
            59: 105,
        }
        self.heatings = {}

    def update_fake_data(self):
        try:
            temperature_rise_speed = 3
            cycle_length_in_seconds = 15
            heat_seconds = 3
            cooling_time = cycle_length_in_seconds - heat_seconds
            time_since_start = datetime.now() - self.start_time

            # check if a new heating object must be created
            for label, start_in_seconds in self.timing.copy().items():
                if time_since_start.total_seconds() > start_in_seconds:
                    if not self.heatings.get(label):
                        self.heatings[label] = Heating(self.tcs[label - 1])
                        self.timing.pop(label)

            # update every heating
            for heating in self.heatings.copy().values():
                heating_time = (datetime.now() - heating.start_time).total_seconds()
                if heating_time < heat_seconds:
                    heating.tc.temperature = round(heating.start_temperature + heating_time * temperature_rise_speed, 1)
                elif heating_time > cycle_length_in_seconds:
                    self.heatings.pop(heating.tc.label)
                else:
                    if heating.max_temperature_reached is None:
                        heating.max_temperature_reached = heating.tc.temperature
                        heating.cooling_speed = (
                                                            heating.max_temperature_reached - heating.start_temperature) / cooling_time
                    heating.tc.temperature = round(
                        heating.max_temperature_reached - (heating_time - heat_seconds) * heating.cooling_speed, 1)
        except Exception as e:
            print(e)

    def get_sensor_data(self):
        self.update_fake_data()

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

    def get_mould_side_states(self):
        result = {
            side_name: 'No error'
            for side_name in ['Left', 'Right', 'Fixed', 'Loose']
        }
        return result
