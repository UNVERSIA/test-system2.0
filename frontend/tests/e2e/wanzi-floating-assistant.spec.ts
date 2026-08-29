import { expect, test, type Page } from '@playwright/test'
import path from 'node:path'

const routes = ['/3d', '/process', '/footprint', '/account', '/optimization', '/prediction', '/technology', '/factors', '/assistant', '/game']

async function resetAssistant(page: Page) {
  await page.goto('/3d')
  await page.evaluate(() => {
    localStorage.setItem('wanzi-stage-vue', JSON.stringify('orb'))
    localStorage.removeItem('wanzi-position-vue')
    localStorage.removeItem('wanzi-messages-vue')
  })
  await page.reload()
}

test('十个路由均显示同一个全局悬浮光球', async ({ page }) => {
  await resetAssistant(page)
  for (const route of routes) {
    await page.goto(route)
    await expect(page.getByTestId('wanzi-orb')).toBeVisible()
  }
})

test('真实 GLB、三级状态、聊天错误处理和跨路由状态均正常', async ({ page, request }) => {
  const severe: string[] = []
  page.on('console', message => { if (message.type() === 'error') severe.push(message.text()) })
  page.on('pageerror', error => severe.push(error.message))
  await resetAssistant(page)
  await page.route('**/api/chat', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: false, response: '智能体服务尚未配置，请在本地环境变量中配置', error: 'coze_configuration' }),
  }))

  const glb = await request.get('/assets/models/wanzi_web.glb')
  expect(glb.status()).toBe(200)
  expect(Number(glb.headers()['content-length'])).toBeGreaterThan(7_000_000)

  await page.goto('/3d')
  const orbBox = await page.getByTestId('wanzi-orb').boundingBox()
  expect(orbBox).not.toBeNull()
  await page.mouse.move(orbBox!.x + orbBox!.width / 2, orbBox!.y + orbBox!.height / 2)
  await page.mouse.down()
  await page.mouse.move(orbBox!.x - 80, orbBox!.y - 60, { steps: 5 })
  await page.mouse.up()
  await expect(page.getByTestId('wanzi-orb')).toBeVisible()
  expect(await page.evaluate(() => localStorage.getItem('wanzi-position-vue'))).not.toBeNull()
  await page.getByTestId('wanzi-orb').click({ force: true })
  await expect(page.getByTestId('wanzi-pet')).toBeVisible()
  const petCanvas = page.getByTestId('wanzi-pet').locator('canvas')
  await expect(petCanvas).toBeVisible()
  await expect(page.getByTestId('wanzi-pet').locator('.wanzi-pet-model')).toHaveAttribute('data-model-loaded', 'true', { timeout: 20_000 })
  await expect.poll(() => petCanvas.evaluate(canvas => canvas.width * canvas.height)).toBeGreaterThan(10_000)

  await petCanvas.click({ force: true })
  await expect(page.getByTestId('wanzi-chat')).toBeVisible({ timeout: 5_000 })
  await expect(page.getByTestId('wanzi-chat').locator('.wanzi-chat-model')).toHaveAttribute('data-model-loaded', 'true', { timeout: 20_000 })
  const input = page.getByLabel('输入你的问题')
  await input.fill('如何减少甲烷排放？')
  await input.press('Enter')
  await expect(page.getByText('智能体服务尚未配置，请在本地环境变量中配置')).toBeVisible()
  await page.reload()
  await expect(page.getByTestId('wanzi-chat')).toBeVisible()
  await expect(page.getByText('如何减少甲烷排放？')).toBeVisible()

  await page.getByRole('button', { name: '工艺流程仿真' }).click()
  await expect(page).toHaveURL(/\/process$/)
  await expect(page.getByTestId('wanzi-chat')).toBeVisible()

  await page.getByRole('button', { name: '收起聊天' }).click()
  await expect(page.getByTestId('wanzi-pet')).toBeVisible()
  await page.getByRole('button', { name: '收回悬浮球' }).click()
  await expect(page.getByTestId('wanzi-orb')).toBeVisible()
  expect(severe).toEqual([])
})

for (const viewport of [{ width: 1920, height: 1080 }, { width: 1366, height: 768 }]) {
  test(`${viewport.width}×${viewport.height} 下全局布局与助手无明显越界`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await resetAssistant(page)
    await page.goto('/3d')
    await page.getByTestId('wanzi-orb').click({ force: true })
    const box = await page.getByTestId('wanzi-pet').boundingBox()
    expect(box).not.toBeNull()
    expect(box!.x).toBeGreaterThanOrEqual(0)
    expect(box!.y).toBeGreaterThanOrEqual(0)
    expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width)
    expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height)
    await expect(page.locator('.main-sidebar')).toBeVisible()
    await expect(page.locator('.topbar')).toBeVisible()
    await expect(page.locator('.settings-drawer')).toBeVisible()
    await page.getByRole('button', { name: '收回悬浮球' }).click()
    await page.screenshot({
      path: path.resolve('../docs/migration/m1', `new-global-layout-${viewport.width === 1920 ? '1920' : '1366'}.png`),
    })
  })
}
