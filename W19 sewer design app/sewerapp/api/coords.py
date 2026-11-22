"""The one coordinate boundary between a project and the map. A project in a projected CRS is shown on the basemap in
lon/lat; a project in local metres (no CRS) is shown without a basemap, scaled so that one metre is one metre at the
equator. Drawing on the map comes back through the inverse."""
from functools import lru_cache
import numpy as np

M_PER_DEG_LON, M_PER_DEG_LAT = 111319.49, 110574.0


@lru_cache(maxsize=16)
def _tr(crs, inverse):
    from pyproj import Transformer
    return Transformer.from_crs(f"EPSG:{crs}", "EPSG:4326", always_xy=True) if not inverse else \
        Transformer.from_crs("EPSG:4326", f"EPSG:{crs}", always_xy=True)


def to_display(crs, x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if not crs: return x / M_PER_DEG_LON, y / M_PER_DEG_LAT
    return _tr(int(crs), False).transform(x, y)


def from_display(crs, lon, lat):
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    if not crs: return lon * M_PER_DEG_LON, lat * M_PER_DEG_LAT
    return _tr(int(crs), True).transform(lon, lat)
