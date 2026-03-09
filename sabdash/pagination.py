"""Pagination utility for list views (guilds, commands, etc.)."""

import math


class Pagination:
    """Simple pagination wrapper for lists or pre-paginated RPC results."""

    def __init__(self, items, total, page, per_page):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = math.ceil(total / per_page) if per_page > 0 else 1

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_page(self):
        return self.page - 1 if self.has_prev else None

    @property
    def next_page(self):
        return self.page + 1 if self.has_next else None

    @property
    def page_range(self):
        """Return a range of page numbers to display."""
        start = max(1, self.page - 2)
        end = min(self.pages, self.page + 2)
        return range(start, end + 1)

    @classmethod
    def from_list(cls, items, page=1, per_page=20):
        """Create pagination from a full list (client-side pagination)."""
        page = max(1, int(page))
        per_page = max(1, min(100, int(per_page)))
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return cls(items[start:end], total, page, per_page)

    @classmethod
    def from_rpc(cls, result):
        """Create pagination from RPC response that includes pagination metadata."""
        return cls(
            items=result.get("items", []),
            total=result.get("total", 0),
            page=result.get("page", 1),
            per_page=result.get("per_page", 20),
        )
