"""Level 1 key inventory; later-level collectibles are intentionally absent."""
class Inventory:
    def __init__(self):
        self.clues=[]
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

    def add_clue(self, clue_id: str, title: str = "", text: str = "", clue_type: str = "clue") -> bool:
        """Adds a discovered environmental clue / journal entry to inventory."""
        if any(c["id"] == clue_id for c in self.clues):
            return False
        self.clues.append({
            "id": str(clue_id),
            "title": str(title or clue_id),
            "text": str(text),
            "type": str(clue_type or "clue"),
            "discovered": True,
        })
        return True

    def has_clue(self, clue_id: str) -> bool:
        """Checks if a clue ID has been discovered."""
        return any(c["id"] == clue_id for c in self.clues)

    @property
    def clue_count(self) -> int:
        """Returns the number of discovered clues."""
        return len(self.clues)

    def get_clues(self) -> list[dict]:
        """Returns all discovered clue entries."""
        return list(self.clues)

    def get_clue(self, clue_id: str) -> dict | None:
        """Returns a specific clue entry by ID, or None if not found."""
        return next((c for c in self.clues if c["id"] == clue_id), None)
