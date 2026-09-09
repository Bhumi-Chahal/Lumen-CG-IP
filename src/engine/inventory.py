"""Tracks keys, journal clues, and Level 2 mirrors across the shared run."""


class Inventory:
    """Manages player progression inventory."""

    def __init__(self):
        self.keys: list[str] = []
        self.mirrors: list[str] = []
        self.clues: list[dict] = []
        self.selected_mirror_id: str | None = None
        self.selected_key_id: str | None = None

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

    def add_mirror(self, mirror_item):
        """Adds a collectible player mirror to inventory.

        Trial mirrors are environmental teaching objects and cannot be added.
        """
        if hasattr(mirror_item, "is_trial") and mirror_item.is_trial:
            return False
        if hasattr(mirror_item, "is_collectible") and not mirror_item.is_collectible:
            return False

        mirror_id = str(getattr(mirror_item, "id", mirror_item))
        if "trial" in mirror_id.lower():
            return False

        if mirror_id not in self.mirrors:
            self.mirrors.append(mirror_id)
        return True

    def has_mirror(self, mirror_id: str) -> bool:
        return mirror_id in self.mirrors

    def select_mirror(self, mirror_id: str) -> bool:
        """Selects a collected mirror for installation."""
        if self.has_mirror(mirror_id):
            self.selected_mirror_id = mirror_id
            return True
        return False

    def get_selected_mirror(self) -> str | None:
        """Returns the currently selected mirror ID, if any."""
        return self.selected_mirror_id

    def clear_selected_mirror(self):
        """Clears the currently selected mirror."""
        self.selected_mirror_id = None

    @property
    def mirror_count(self) -> int:
        return len(self.mirrors)

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

    def clear(self):
        self.keys.clear()
        self.mirrors.clear()
        self.clues.clear()
