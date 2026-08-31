# Natural Earth data for the map

Three 1:10m layers from Natural Earth (naturalearthdata.com), public
domain, as GeoJSON from the nvkelso/natural-earth-vector GitHub mirror
(fetched 2026-08-25):

- `ne_10m_land.geojson`
- `ne_10m_rivers_lake_centerlines.geojson`
- `ne_10m_lakes.geojson`

`tools/build_map.py` reads them from here by default and writes
`art/map.svg`, which `tools/build_print.py` places facing Book 1.
