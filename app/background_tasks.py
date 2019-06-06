"""
background_tasks.py describes tasks performed by application in the background.
"""
import asyncio

update_interval_seconds = 0.2
update_task_name = 'box_listener'


async def start_background_tasks(app):
    """Starts periodic background update task for application."""
    app[update_task_name] = asyncio.create_task(update_task(app))


async def cleanup_background_tasks(app):
    """Cancels periodic background update task."""
    app[update_task_name].cancel()
    await app[update_task_name]


async def update_task(app):
    """
    This method performs the periodic update for the application: it updates mold sides connection statuses,
    retrieves data from wlanboxconnector to update thermocouple temperature and status values
    and performs update on a current test session.

    :param app: Application instance
    :return: None
    """
    wlanbox = app.wlanbox
    while True:
        # update mold sides
        app.mold_side_states = wlanbox.get_mould_side_states()

        # update thermocouples
        sensor_data = wlanbox.get_sensor_data()
        state = sensor_data['state']
        time = sensor_data['time']
        if state:
            for label in app.tcs.keys():
                tc = app.tcs.get(label)
                if app.mold_side_states[tc.mold_side] == 'No error':
                    tc.update(state[label]['temperature'], state[label]['status'], time)
                else:
                    tc.update(None, state[label]['status'], time)

        # test session update
        app.test_session.update(app.tcs, app.msd_config)
        await asyncio.sleep(update_interval_seconds)
