import tomli
import tomli_w


class PersistantState(dict):

    def __init__(self, filepath):
        self._filepath = filepath
        with open(self._filepath, "rb") as f:
            state = tomli.load(f)
        super().update(state)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        with open(self._filepath, "wb") as f:
            tomli_w.dump(self, f)
