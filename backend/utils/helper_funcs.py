def python_ensure_list(ids):
    return list(map(int, ids.split(','))) if isinstance(ids, str) else (
        [ids] if isinstance(ids, int) else (list(map(int, ids)) if isinstance(ids, list) else None))