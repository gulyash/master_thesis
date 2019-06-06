import datetime
import json

import aiohttp_jinja2
from aiohttp import web

from breadcrumb import get_breadcrumb_data
from config import MSDConfig
from reporter import generate_report
from testing import TestSession


async def get_tc_data(request):
    tc = request.app.tcs[int(request.query['tc'])]
    hist_list = list(tc.history)
    result = {
        'time': [record['time'] for record in hist_list],
        'temperature': [record['temperature'] for record in hist_list],
        'name': tc.text_label,
    }
    return web.Response(text=json.dumps(result))


@aiohttp_jinja2.template('start.html')
async def get_start_page(request):
    return {}


@aiohttp_jinja2.template('reports.html')
async def get_reports_page(request):
    return {}


@aiohttp_jinja2.template('test-mould.html')
async def get_mold_side_selection_page(request):
    breadcrumb = get_breadcrumb_data(request)
    breadcrumb.append('Mold Side Selection')
    return {
        'breadcrumb': breadcrumb,
        'mold_no': request.app.mold_config.mold_no
    }


@aiohttp_jinja2.template('test-mould-side.html')
async def get_test_page(request):
    mold_side = request.query['mold_side']
    breadcrumb = get_breadcrumb_data(request)
    breadcrumb.append(mold_side)
    selected_tc = next(
        tc for tc in request.app.tcs.values() if str(tc.mold_side).lower() == str(mold_side).lower()).label
    return {
        'mold_side': mold_side,
        'selected_tc': selected_tc,
        'breadcrumb': breadcrumb,
        'heatmap_info': json.dumps({
            'graphTitle': mold_side + " Side",
            'moldSide': mold_side,
        }),
        'min_temperature': request.app.msd_config.min_graph_temperature,
        'max_temperature': request.app.msd_config.max_graph_temperature,
    }


async def get_new_test_session(request):
    request.app.test_session = TestSession()
    print(datetime.datetime.now(), ': Test restarted.')
    raise web.HTTPFound('/test-mould')


async def get_session_info(request):
    app = request.app
    mold_side = request.query['mold_side']
    mold_side_tcs = [tc for tc in app.tcs.values() if tc.mold_side == mold_side]
    test_session = app.test_session
    ordering = test_session.get_ordering(mold_side_tcs)
    completed_info = test_session.completed_test.to_dict() if test_session.completed_test else None
    current_direction = test_session.direction.name.lower()
    if test_session.current_test and test_session.current_test.is_manual:
        current_direction = 'manual'
    return web.Response(text=json.dumps({
        'completed': completed_info,
        'ordering': ordering,
        'current_mode': current_direction,
    }))


async def post_test_direction(request):
    if request.body_exists:
        params = await request.post()
        direction = params['direction']
        request.app.test_session.set_guided_testing_direction(direction)
        print('Test direction changed to', direction)
    return web.Response()


@aiohttp_jinja2.template('settings.html')
async def get_autotest_config(request):
    mould_name = request.app.mold_config.name
    config = request.app.msd_config
    result = {
        'detection_time': config.detection_time.seconds,
        'detection_degrees': config.detection_degrees,
        'test_time': config.test_time.seconds,
        'test_degrees': config.test_degrees,
        'test_session_start_time': request.app.test_session.started_at.isoformat(),
        'mold_layout': mould_name,
        'tester_name': request.app.msd_config.tester_name,
        'min_graph_temperature': request.app.msd_config.min_graph_temperature,
        'max_graph_temperature': request.app.msd_config.max_graph_temperature,
    }
    return result


async def post_autotest_config(request):
    if request.body_exists:
        params = await request.post()
        request.app.msd_config = MSDConfig.fromdict(params)
        print('Config updated.')
        # request.app.test_session = TestSession()
        # print('Test session restarted.')
        raise web.HTTPFound('/settings')
    return {}


async def get_heatmap_update(request):
    request_mold_side = request.query['mold_side']
    app = request.app
    slave_state = app.mold_side_states[request_mold_side]
    if slave_state != 'No error':
        errors = slave_state
        heatmap_data = {}
    else:
        errors = None
        mold_side_tcs = [tc for tc in app.tcs.values() if tc.mold_side == request_mold_side]
        test_session = app.test_session
        test_results = test_session.test_results
        statuses = [tc.status for tc in mold_side_tcs]
        successful_tests = [test.tc.label for test in test_results if test.result == "success"]
        failed_tests = [test.tc.label for test in test_results if test.result == "fail"]
        if test_session.completed_test:
            current_test = test_session.completed_test.tc.label
        elif test_session.current_test:
            current_test = test_session.current_test.tc.label
        else:
            current_test = None
        heatmap_data = {
            'x': [tc.x for tc in mold_side_tcs],
            'y': [tc.y for tc in mold_side_tcs],
            'temperature': [tc.temperature for tc in mold_side_tcs],
            'label': [tc.label for tc in mold_side_tcs],
            'status': statuses,
            'test': {
                'successful': successful_tests,
                'failed': failed_tests,
                'current': current_test,
            }
        }
    result = {
        'error': errors,
        'data': heatmap_data,
    }
    text = json.dumps(result)
    return web.Response(text=text)


async def autotest_confirmation(request):
    test_session = request.app.test_session
    print("Test result received!")
    if request.body_exists:
        body = json.loads(await request.read())
        print(body)
        test_session.confirm_test(body['result'])
    return web.Response(text=json.dumps({'msg': 'autotest confirmed', }))


async def post_manual_test(request):
    test_session = request.app.test_session
    if test_session.current_test:
        result = {
            'msg': "You can't start new manual test during another test."
        }
    elif request.body_exists:
        params = await request.post()
        tc_num = int(params['tc'])
        tc = request.app.tcs[tc_num]
        already_tested_tcs = [result.tc for result in test_session.test_results]
        if tc in already_tested_tcs:
            result = {
                'msg': "This TC is already tested."
            }
        else:
            if tc.status == 'OK':
                test_data = {
                    'init_time': tc.history[-1]['time'],
                    'start_time': tc.history[-1]['time'],
                    'start_temperature': tc.history[-1]['temperature'],
                }
                test_session.new_tc_test(tc, test_data, manual=True)
                result = {
                    'msg': "OK"
                }
            else:
                result = {
                    'msg': f"Thermocouple status {tc.status}"
                }
    else:
        result = {
            'msg': "Please, specify TC num."
        }
    text = json.dumps(result)
    return web.Response(text=text)


async def get_report(request):
    app = request.app
    data = {}
    for mold_side in [mold_side.name for mold_side in app.mold_config.mold_sides]:
        mold_side_tcs = [tc for tc in app.tcs.values() if tc.mold_side == mold_side]
        test_session = app.test_session
        test_results = test_session.test_results
        successful_tests = [test.tc.label for test in test_results if test.result == "success"]
        failed_tests = [test.tc.label for test in test_results if test.result == "fail"]
        statuses = []
        for tc in mold_side_tcs:
            if tc.label in successful_tests:
                statuses.append("success")
            elif tc.label in failed_tests:
                statuses.append("fail")
            else:
                statuses.append(tc.status)
        data[mold_side] = {
            'x': [tc.x for tc in mold_side_tcs],
            'y': [tc.y for tc in mold_side_tcs],
            'label': [tc.label for tc in mold_side_tcs],
            'status': statuses,
        }
    filename = "report"
    tester_name = request.app.msd_config.tester_name
    mold_type = request.app.mold_config.name
    mold_no = request.app.mold_config.mold_no
    generate_report(filename, data, mold_no, mold_type, tester_name)
    return web.FileResponse(f"static/reports/{filename}.pdf")
