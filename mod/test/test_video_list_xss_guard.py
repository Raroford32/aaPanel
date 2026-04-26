import pathlib


def _read(path):
    return pathlib.Path(path).read_text(encoding='utf-8', errors='ignore')


def test_admin_video_list_escapes_html_and_js_contexts():
    text = _read('BTPanel/static/js/files.js')
    assert 'var _escapeHtml = function (str)' in text
    assert 'var _escapeJsString = function (str)' in text
    assert "safe_name = _escapeHtml(rdata[i].name)" in text
    assert "onclick=\"bt_file.play_file(this,\\'" in text and "safe_filename_js" in text


def test_share_video_list_escapes_html_and_js_contexts():
    text = _read('BTPanel/templates/default/down.html')
    assert 'var _escapeHtml = function (str)' in text
    assert 'var _escapeJsString = function (str)' in text
    assert "safe_name = _escapeHtml(rdata[i].name)" in text
    assert "onclick=\"play_file(this,\\'" in text and "safe_filename_js" in text
