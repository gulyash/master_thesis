"""
this module contains business rules that describe testing process.
"""
from datetime import datetime
from enum import Enum


class GuidedTestingDirection(Enum):
    HORIZONTAL_FIRST = 0
    VERTICAL_FIRST = 1


class TestSession:
    """
    Stores information about current test session:
    test results, test session start time, and current testing configuration.
    """

    def __init__(self) -> None:
        super().__init__()
        self.started_at = datetime.now()
        self.current_test = None
        self.completed_test = None
        self.test_results = []
        self.direction = GuidedTestingDirection.HORIZONTAL_FIRST

    def update(self, tcs, config):
        """
        Performs update on test session:
        Checks if currently tested thermocouple is not disconnected, and if it is, stops current test.
        If no test is currently run, it detects heated thermocouple and start a new test for it.
        Checks if current test is complete and needs to be confirmed (automatically or by user).

        :param tcs: app.tcs - dictionary with TC labels as keys and thermocouple objects as values.
        :param config: current application config
        :return: None
        """
        if self.current_test and not self.current_test.tc.status == 'OK':
            print(f'Autotested {self.current_test.tc.text_label} disconnected.')
            self.current_test = None
        if not self.current_test and not self.completed_test:
            detection_result = self.detect_tested_tc(tcs, config.detection_time, config.detection_degrees)
            if detection_result:
                print('Detected!')
                tc = detection_result['tc']
                test_data = detection_result['test_data']
                self.new_tc_test(tc, test_data, manual=False)
        elif self.current_test:
            self.current_test.update(config.test_time, config.test_degrees)
            if self.current_test.is_complete:
                print(f'Test marked as completed. {self.current_test.tc.text_label}')
                self.completed_test = self.current_test

                map = {
                    'time out': 'fail',
                    'complete': 'success',
                }
                result = map[self.current_test.result]
                # instantly confirm manual test
                if self.current_test.is_manual:
                    self.confirm_test(result)
                # instantly confirm successful tests if they are with correct ordering
                elif result == 'success':
                    mold_side = self.current_test.tc.mold_side
                    mold_side_tcs = [tc for tc in tcs.values() if tc.mold_side == mold_side]
                    ordering = self.get_ordering(mold_side_tcs)
                    expected_tc_label = ordering[0]
                    if self.current_test.tc.label == expected_tc_label:
                        self.confirm_test(result)

                self.current_test = None

    def detect_tested_tc(self, tcs, time_threshold, temperature_threshold):
        """
        Method for detecting heated thermocouple.

        :param tcs: list of all thermocouples
        :param time_threshold: time within which the temperature
        change must happen for thermocouple to be considered heated
        :param temperature_threshold: amount of degrees temperature
        must rise within time limit for the thermocouple to be considered as heated
        :return: detection info (heated tc and information for creating a new TcTest) as a dict or None
        """
        already_tested = list(test.tc for test in self.test_results)
        active_tcs = list(filter(lambda tc: tc.status == 'OK', tcs.values()))
        if active_tcs:
            first_tc = active_tcs[0]
            bound_index = first_tc.find_threshold_index(time_threshold)
            if bound_index:
                for tc in active_tcs:
                    test_info = tc.get_test_status(bound_index, temperature_threshold)
                    is_tested = test_info['is_tested']
                    if is_tested and tc not in already_tested:
                        print(test_info['data'])
                        return {
                            'tc': tc,
                            'test_data': test_info['data']
                        }
        return None

    def new_tc_test(self, tc, test_data, manual):
        self.current_test = TcTest(tc, test_data, manual)

    def confirm_test(self, result):
        """
        Add completed test to test_results with passed result.

        :param result: test result
        :return: None
        """
        self.completed_test.result = result
        self.test_results.append(self.completed_test)
        self.completed_test = None

    def set_guided_testing_direction(self, direction):
        """
        Sets current test session direction.

        :param direction: direction to be set
        :return: None
        """
        if direction.lower() in ('hf', 'horizontal', 'horizontal first', 'horizontal-first', 'horz'):
            self.direction = GuidedTestingDirection.HORIZONTAL_FIRST
        elif direction.lower() in ('vf', 'vertical', 'vertical first', 'vertical-first', 'vert'):
            self.direction = GuidedTestingDirection.VERTICAL_FIRST

    def get_ordering(self, mold_side_tcs):
        """
        Get thermocouple ordering for expected testing according to currently selected guided testing direction.

        :param mold_side_tcs: thermocouples on the mould side for which the ordering is required
        :return: list of tc labels, ordered according to selected direction
        """
        active_tcs = set(tc for tc in mold_side_tcs if tc.status == "OK")
        tested_tcs = set(result.tc for result in self.test_results)

        if self.direction == GuidedTestingDirection.VERTICAL_FIRST:
            tcs = sorted(sorted([tc for tc in active_tcs - tested_tcs], key=lambda tc: tc.y, reverse=True),
                         key=lambda tc: tc.x)
        elif self.direction == GuidedTestingDirection.HORIZONTAL_FIRST:
            tcs = sorted([tc for tc in active_tcs - tested_tcs], key=lambda tc: tc.label)
        else:
            tcs = []
        return [tc.label for tc in tcs]


class TcTest:
    """
    Thermocouple test class
    Each thermocouple test stores the following information:
    thermocouple, for which the test is initiated
    time and temperature at the beginning of a test
    boolean value, defining whether a test is run in manual mode or not
    boolean completion status
    test result
    """

    def __init__(self, tc, test_data, manual) -> None:
        super().__init__()
        self.tc = tc
        self.init_time = test_data['init_time']
        self.start_time = test_data['start_time']
        self.start_temperature = test_data['start_temperature']

        self.is_manual = manual
        self.is_complete = False
        self.result = None

    def update(self, time_threshold, temperature_threshold):
        """
        This method performs update on a thermocouple test.
        it checks if a test is completed, and if yes, sets a completion message as a result.

        :param time_threshold: thermocouple test timeout
        :param temperature_threshold: used for test completion check
        :return: None
        """
        tc = self.tc
        test_info = tc.get_test_completion_status(time_threshold, temperature_threshold, self)
        test_complete = test_info['is_complete']
        message = test_info['message']
        if test_complete:
            print(message)
            self.is_complete = True
            self.result = message

    def to_dict(self):
        tc_dict = self.tc.to_dict()
        tc_dict.update({
            'init_time': self.init_time,
            'start_time': self.start_time,
            'start_temperature': self.start_temperature,
            'is_complete': self.is_complete,
            'result': self.result,
        })
        return tc_dict
