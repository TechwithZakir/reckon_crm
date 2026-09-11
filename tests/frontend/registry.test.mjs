import assert from 'node:assert/strict'
import test from 'node:test'
import { registerCRMTab, getCRMTabs } from '../../frontend/src/extensions/registry/tabs.js'
import { registerCRMRoute, getCRMRoutes } from '../../frontend/src/extensions/registry/routes.js'
import { registerCRMSidebarItem, getCRMSidebarItems } from '../../frontend/src/extensions/registry/sidebar.js'
import { registerCRMAction, getCRMActions } from '../../frontend/src/extensions/registry/actions.js'

test('tabs are scoped to native records and desktop/mobile surfaces', () => {
  const remove = registerCRMTab({ name: 'Visits', doctype: 'CRM Lead', component: {} })
  assert.equal(getCRMTabs('CRM Lead', 'desktop').length, 1)
  assert.equal(getCRMTabs('CRM Lead', 'mobile').length, 1)
  assert.equal(getCRMTabs('CRM Deal').length, 0)
  assert.throws(() => registerCRMTab({ name: 'Visits', doctype: 'CRM Lead', component: {} }), /Duplicate/)
  assert.throws(() => registerCRMTab({ name: 'Visits', doctype: 'Lead', component: {} }), /Unsupported/)
  assert.ok(Object.isFrozen(getCRMTabs('CRM Lead')[0]))
  remove()
  const removeDesktop = registerCRMTab({ name: 'Desktop', doctype: 'CRM Deal', component: {}, surfaces: ['desktop'] })
  assert.equal(getCRMTabs('CRM Deal', 'mobile').length, 0)
  removeDesktop()
})

test('routes reject invalid paths and conflicting names/paths', () => {
  const remove = registerCRMRoute({ name: 'Visits', path: '/visits', component: {} })
  assert.equal(getCRMRoutes()[0].path, '/visits')
  assert.throws(() => registerCRMRoute({ name: 'Other', path: '/visits', component: {} }), /Duplicate/)
  for (const routePath of ['/crm/visits', 'https://example.com', '//outside', '/visits?x=1']) {
    assert.throws(() => registerCRMRoute({ name: 'Bad', path: routePath, component: {} }))
  }
  remove()
})

test('sidebar and action APIs validate registration and support disposal', () => {
  const remove = registerCRMSidebarItem({ name: 'Visits', section: 'FIELD SALES', label: 'Field Visits', routeName: 'Visits' })
  assert.equal(getCRMSidebarItems()[0].section, 'FIELD SALES')
  remove()
  const removeAction = registerCRMAction({ name: 'Schedule', doctype: 'CRM Lead', handler: () => 'scheduled' })
  assert.equal(getCRMActions('CRM Lead')[0].handler(), 'scheduled')
  assert.equal(getCRMActions('CRM Deal').length, 0)
  assert.throws(() => registerCRMAction({ name: 'Broken', doctype: 'CRM Lead' }), /handler/)
  removeAction()
})
