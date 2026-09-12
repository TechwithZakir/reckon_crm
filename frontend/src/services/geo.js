export function currentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('Geolocation is unavailable on this device.'))
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude, accuracy: coords.accuracy }),
      () => reject(new Error('Location could not be obtained. Enable location permission and retry, or explicitly continue without verification.')),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    )
  })
}
