from datetime import timedelta


class MSDConfig:
    """
    Test configuration class.
    Stores threshold values of temperature and time for detection of a heated thermocouple
    or for checking thermocouple test completion status
    """
    def __init__(self,
                 detection_time=timedelta(seconds=1),
                 detection_degrees=1,
                 test_time=timedelta(seconds=10),
                 test_degrees=4,
                 tester_name="unknown",
                 min_graph_temperature=24,
                 max_graph_temperature=38) -> None:
        super().__init__()
        self.detection_time = detection_time
        self.detection_degrees = detection_degrees
        self.test_time = test_time
        self.test_degrees = test_degrees
        self.tester_name = tester_name
        self.min_graph_temperature = min_graph_temperature
        self.max_graph_temperature = max_graph_temperature


    @classmethod
    def fromdict(cls, d):
        params = [
            timedelta(seconds=int(d['detection_time'])),
            int(d['detection_degrees']),
            timedelta(seconds=int(d['test_time'])),
            int(d['test_degrees']),
            d['tester_name'],
            int(d['min_graph_temperature']),
            int(d['max_graph_temperature']),
        ]
        result = cls(*params)
        return result
