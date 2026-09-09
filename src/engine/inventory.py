"""Level 1 key inventory; later-level collectibles are intentionally absent."""
class Inventory:
    def __init__(self):
        self.keys=[]
        self.selected_key_id=None

    def add_key(self, key_id: str):
        if key_id not in self.keys:
            self.keys.append(key_id)

    def has_key(self, key_id: str) -> bool:
        return key_id in self.keys

    def select_key(self, key_id: str) -> bool:
        """Selects a collected key for testing on doors."""
        if self.has_key(key_id):
            self.selected_key_id = key_id
            return True
        return False

    def get_selected_key(self) -> str | None:
        """Returns currently selected key ID."""
        return self.selected_key_id

    def clear_selected_key(self):
        """Clears the currently selected key."""
        self.selected_key_id = None

    @property
    def key_count(self) -> int:
        return len(self.keys)
