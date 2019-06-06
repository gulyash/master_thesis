from config import MSDConfig
from emulator import Emulator
from mold_config import MouldConfig, tcs_from_config
from testing import TestSession
# from wlanboxconnector import WLANBoxConnector


def init_app(app):
    app.mold_config = MouldConfig.from_common_config()
    app.tcs = tcs_from_config(app.mold_config)
    app.wlanbox = Emulator(app.mold_config.tc_count)
    # app.wlanbox = WLANBoxConnector(app.mold_config.tc_count)
    app.msd_config = MSDConfig()
    app.test_session = TestSession()
    return app
