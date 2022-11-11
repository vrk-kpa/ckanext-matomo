import pytest


@pytest.mark.usefixtures("clean_db")
def test_script_tag_present(app):
    resp = app.get('/')
    assert 'trackPageView' in resp
