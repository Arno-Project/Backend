from utils.Singleton import Singleton


class ListAdapter(metaclass=Singleton):
    def python_ensure_list(self, ids):
        return list(map(int, ids.split(','))) if isinstance(ids, str) else (
            [ids] if isinstance(ids, int) else (list(map(int, ids)) if isinstance(ids, list) else None))
