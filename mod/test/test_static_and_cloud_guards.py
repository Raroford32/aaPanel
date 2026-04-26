import pathlib


def _read(path):
    return pathlib.Path(path).read_text(encoding='utf-8', errors='ignore')


def test_static_path_safe_check_precedes_send_file_fast_path():
    text = _read('BTPanel/__init__.py')
    block_start = text.index("if request.path.startswith('/static/'):")
    block_end = text.index("if request.method == 'GET' and request.path.startswith('/static/img/soft_ico/'):")
    block = text[block_start:block_end]

    assert 'if not public.path_safe_check(request.path): return abort(404)' in block
    assert block.index('if not public.path_safe_check(request.path): return abort(404)') < block.index('if os.path.exists(static_file):')


def test_cloud_toserver_requires_post_and_safe_paths_all_routes():
    required = [
        "if request.method != 'POST':",
        'if not public.path_safe_check(get.name):',
        'if not public.path_safe_check(download_dir):',
        'local_file = os.path.join(download_dir, os.path.basename(get.name))',
    ]
    for target in ('BTPanel/__init__.py', 'BTPanel/routes/v1.py', 'BTPanel/routes/v2.py'):
        text = _read(target)
        assert 'if "toserver" in get and get.toserver == "true":' in text
        for snippet in required:
            assert snippet in text
