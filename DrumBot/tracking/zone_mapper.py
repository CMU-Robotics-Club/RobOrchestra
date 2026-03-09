"""Map normalized x coordinates to drum zones."""

from __future__ import annotations

from typing import Sequence


class ZoneMapper:
    """Converts horizontal hand position to discrete drum zones."""

    def __init__(
        self,
        zone_edges: Sequence[float],
        zone_labels: Sequence[str] = ("HIHAT", "SNARE", "TOM", "CRASH"),
    ) -> None:
        if len(zone_labels) != len(zone_edges) + 1:
            raise ValueError("zone_labels must contain exactly len(zone_edges) + 1 items")
        if any(edge <= 0.0 or edge >= 1.0 for edge in zone_edges):
            raise ValueError("zone_edges must be within (0, 1)")
        if any(left >= right for left, right in zip(zone_edges, zone_edges[1:])):
            raise ValueError("zone_edges must be strictly increasing")

        self._zone_edges = tuple(zone_edges)
        self._zone_labels = tuple(zone_labels)

    def zone_for_x(self, x: float) -> str:
        """Return zone label for a normalized x coordinate."""

        clamped_x = min(max(x, 0.0), 1.0)
        for index, edge in enumerate(self._zone_edges):
            if clamped_x < edge:
                return self._zone_labels[index]
        return self._zone_labels[-1]
