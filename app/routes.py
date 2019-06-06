"""
This module lists all endpoints of the server
"""
from views import (
    get_tc_data,
    autotest_confirmation,
    get_autotest_config,
    post_autotest_config,
    post_manual_test,
    get_start_page,
    get_mold_side_selection_page,
    get_test_page,
    get_new_test_session,
    get_heatmap_update,
    post_test_direction,
    get_session_info,
    get_report,
    get_reports_page,
)


def setup_routes(app):
    # pages
    app.router.add_get('/', get_start_page)
    app.router.add_get('/test-mould', get_mold_side_selection_page)
    app.router.add_get('/test-mould/side', get_test_page)
    app.router.add_get('/settings', get_autotest_config)
    app.router.add_get('/reports', get_reports_page)
    # regular updates
    app.router.add_get('/heatmap-data', get_heatmap_update)
    app.router.add_get('/tc-data', get_tc_data)
    app.router.add_get('/session-info', get_session_info)
    # queries/operations
    app.router.add_get('/new-test', get_new_test_session)
    app.router.add_post('/test-direction', post_test_direction)
    app.router.add_post('/settings', post_autotest_config)
    app.router.add_post('/autotest-confirmation', autotest_confirmation)
    app.router.add_post('/mantest', post_manual_test)
    app.router.add_get('/report', get_report)
