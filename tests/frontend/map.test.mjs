import test from 'node:test'
import assert from 'node:assert/strict'
import { locationMap } from '../../frontend/src/services/map.js'

test('map previews reject missing and invalid coordinates but accept zero', () => {
  for (const values of [['', ''], [null, 1], [NaN, 1], [91, 0], [0, 181], ['javascript:1', 0]]) {
    assert.equal(locationMap(...values), null)
  }
  const url = new URL(locationMap(0, 0).embed)
  assert.equal(url.origin, 'https://www.openstreetmap.org')
  assert.equal(url.searchParams.get('marker'), '0,0')
  for (const values of [[90, 180], [-90, -180]]) {
    const bounds = new URL(locationMap(...values).embed).searchParams.get('bbox').split(',').map(Number)
    assert.ok(bounds[0] >= -180 && bounds[2] <= 180 && bounds[1] >= -90 && bounds[3] <= 90)
    assert.ok(bounds[0] < bounds[2] && bounds[1] < bounds[3])
  }
})
