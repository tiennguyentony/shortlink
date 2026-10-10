import math
from dataclasses import dataclass

MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageRequest:
    """1-based page number and page size."""

    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size

    def pages_for(self, total: int) -> int:
        return max(1, math.ceil(total / self.size))
