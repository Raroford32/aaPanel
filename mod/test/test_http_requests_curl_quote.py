import pathlib


def test_get_curl_quotes_url_before_execshell():
    text = pathlib.Path('class/http_requests.py').read_text(encoding='utf-8', errors='ignore')
    assert 'import shlex' in text
    assert 'safe_url = shlex.quote(url)' in text
    assert 'timeout, headers_str, safe_url' in text
