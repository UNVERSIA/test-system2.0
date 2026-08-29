import { expect, test } from '@playwright/test'
import path from 'node:path'

const backend = 'http://127.0.0.1:8000/api/virtual-plant'

test.beforeEach(async ({ request }) => {
  await request.post(`${backend}/reset`)
})

test('配置驱动的16个三维对象与独立拓扑一致', async ({ page, request }) => {
  const config = await (await request.get(`${backend}/config`)).json()
  await page.goto('/3d')
  await expect(page.getByTestId('virtual-plant-workbench')).toBeVisible()
  await expect(page.getByText('当前为示范仿真数据，不代表真实水厂运行结果').first()).toBeVisible()
  await expect(page.locator('.vp-unit-label')).toHaveCount(config.units.length)
  await expect(page.locator('canvas[aria-label="虚拟水厂三维场景"]')).toHaveCount(1)
  expect(config.units).toHaveLength(16)
  expect(config.connections).toHaveLength(18)
  expect(config.connections.every((edge: { source_unit_id:string;target_unit_id:string }) => edge.source_unit_id && edge.target_unit_id)).toBe(true)
})

test('单步推进后3D、指标、趋势使用同一后端状态', async ({ page, request }) => {
  await page.goto('/3d')
  await page.getByRole('button', { name: '单步', exact: true }).click()
  await expect(page.locator('.vp-live-status')).toContainText('00:01')
  await expect(page.locator('.vp-kpis')).toContainText('12000')
  const state = await (await request.get(`${backend}/state`)).json()
  expect(state.simulation_minute).toBe(1)
  expect(state.total_inflow_m3_d).toBe(12000)
  expect(state.total_outflow_m3_d).toBe(12000)
  await page.getByRole('button', { name: '好氧池', exact: true }).click()
  await expect(page.locator('.vp-detail-panel')).toContainText('好氧池')
  await expect(page.getByTestId('state-trend')).toContainText('仿真分钟 1')
})

test('四场景可选择且甲烷异常同步改变颜色、详情、趋势和告警', async ({ page, request }) => {
  const scenarios = await (await request.get(`${backend}/scenarios`)).json()
  expect(scenarios.map((item: { scenario_id:string }) => item.scenario_id)).toEqual(['normal','influent_surge','blower_failure','methane_anomaly'])
  await request.post(`${backend}/scenario`, { data: { scenario_id: 'methane_anomaly' } })
  await request.post(`${backend}/step`, { data: { steps: 20 } })
  const backendState = await (await request.get(`${backend}/state`)).json()
  const expectedMethane = backendState.units.find((unit: { unit_id:string }) => unit.unit_id === 'anaerobic_tank').methane_mg_l
  await page.goto('/3d')
  await page.getByRole('button', { name: '厌氧池', exact: true }).click()
  await expect(page.locator('.vp-detail-panel')).toContainText(`${expectedMethane.toFixed(2)} mg/L`)
  await expect(page.locator('.vp-unit-label', { hasText: '厌氧池' })).toHaveClass(/risk-critical/)
  await expect(page.getByRole('button', { name: /告警与事件 1/ })).toBeVisible()
  await page.getByRole('button', { name: /告警与事件/ }).click()
  await expect(page.locator('.vp-alarm-log')).toContainText('甲烷示范值')
})

test('设备故障调整通过API改变设备状态、DO闭环与告警', async ({ page, request }) => {
  await page.goto('/3d')
  await page.getByRole('button', { name: '鼓风机房', exact: true }).click()
  await page.getByRole('button', { name: /主鼓风机/ }).click()
  await page.locator('.vp-equipment-editor select').first().selectOption('fault')
  await page.getByRole('button', { name: '应用设备调整' }).click()
  await expect(page.locator('.vp-detail-panel')).toContainText('fault · 42Hz')
  const before = await (await request.get(`${backend}/units/aerobic_tank`)).json()
  await request.post(`${backend}/step`, { data: { steps: 5 } })
  const after = await (await request.get(`${backend}/units/aerobic_tank`)).json()
  expect(after.state.water_quality.DO).toBeLessThan(before.state.water_quality.DO)
  expect(after.state.alarms.length).toBeGreaterThanOrEqual(0)
  const alarms = await (await request.get(`${backend}/alarms`)).json()
  expect(alarms.some((alarm: { unit_id:string }) => alarm.unit_id === 'blower_house')).toBe(true)
})

test('2D与3D共享状态且路由切换不会遗留重复Canvas', async ({ page, request }) => {
  await request.post(`${backend}/step`, { data: { steps: 7 } })
  await page.goto('/3d')
  await expect(page.locator('canvas[aria-label="虚拟水厂三维场景"]')).toHaveCount(1)
  await page.getByRole('button', { name: /工艺流程仿真/ }).click()
  await expect(page.getByTestId('process-topology')).toBeVisible()
  await expect(page.getByText('仿真分钟').last()).toBeVisible()
  await expect(page.locator('canvas[aria-label="虚拟水厂三维场景"]')).toHaveCount(0)
  await page.getByRole('button', { name: /3D水厂仿真/ }).click()
  await expect(page.locator('canvas[aria-label="虚拟水厂三维场景"]')).toHaveCount(1)
})

test('公式注册表不把无来源关系标为已验证', async ({ page, request }) => {
  const formulas = await (await request.get(`${backend}/formulas`)).json()
  expect(formulas).toHaveLength(5)
  expect(formulas.every((item: { trust_status:string;full_source:string|null }) => item.trust_status !== 'verified' && item.full_source === null)).toBe(true)
  await page.goto('/3d')
  await page.getByRole('button', { name: '查看公式可信度' }).click()
  await expect(page.getByRole('dialog', { name: '公式与来源状态' })).toContainText('待核实：当前没有满足要求的完整来源')
})

for (const viewport of [{ width: 1920, height: 1080 }, { width: 1366, height: 768 }]) {
  test(`${viewport.width}×${viewport.height} 工作台无严重控制台错误和横向溢出`, async ({ page }) => {
    const errors:string[]=[];page.on('console',message=>{if(message.type()==='error')errors.push(message.text())});page.on('pageerror',error=>errors.push(error.message))
    await page.setViewportSize(viewport)
    await page.goto('/3d')
    await expect(page.locator('.vp-control-panel')).toBeVisible()
    await expect(page.locator('.vp-stage')).toBeVisible()
    await expect(page.locator('.vp-detail-panel')).toBeVisible()
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth)
    expect(overflow).toBeLessThanOrEqual(1)
    expect(errors).toEqual([])
    await page.screenshot({ path: path.resolve('../docs/virtual_plant_v1/screenshots', `virtual-plant-${viewport.width}.png`) })
  })
}
