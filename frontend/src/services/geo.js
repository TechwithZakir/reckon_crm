export function currentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('Geolocation is unavailable on this device.'))
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude, accuracy: coords.accuracy }),
      (error) => reject(new Error(error.code === 1
        ? 'Location access is blocked. Open the site permissions beside the browser address, allow Location, then retry. The browser cannot show a new permission prompt while access is blocked.'
        : error.code === 3 ? 'Location request timed out. Check device location services and retry.'
        : 'Location is unavailable. Enable device location services and retry, or explicitly continue without verification.')),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    )
  })
}
