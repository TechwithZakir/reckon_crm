export function locationMap(latitude, longitude) {
  if ([latitude, longitude].some(value => value == null || String(value).trim() === '')) return null
  const lat = Number(latitude), lon = Number(longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null
  const bbox = [Math.max(-180, lon - 0.006), Math.max(-90, lat - 0.004), Math.min(180, lon + 0.006), Math.min(90, lat + 0.004)]
  const params = new URLSearchParams({ bbox: bbox.join(','), layer: 'mapnik', marker: `${lat},${lon}` })
  return {
    embed: `https://www.openstreetmap.org/export/embed.html?${params}`,
    link: `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=16/${lat}/${lon}`,
  }
}
