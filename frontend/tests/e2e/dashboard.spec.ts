import { test, expect } from "@playwright/test"
import {
  injectAuthTokens,
  mockCreditsBalance,
} from "./helpers/auth"
import { MOCK_PROJECT_LIST } from "./fixtures/mock-data"

/**
 * 仪表盘测试
 * 策略：Mock 认证 + Mock 数据
 */
test.describe("仪表盘", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)
    // Mock 项目列表
    await page.route("**/v1/projects**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_PROJECT_LIST),
      })
    })
    await mockCreditsBalance(page, 500)
  })

  test("仪表盘页面标题正常显示", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    await expect(page).toHaveTitle(/BidAgent/)
    await expect(page.getByText("仪表板")).toBeVisible()
  })

  test("Header 导航栏各入口可见", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("招标机会")).toBeVisible()
    await expect(page.getByText("我的项目")).toBeVisible()
    await expect(page.getByText("BidAgent")).toBeVisible()
  })

  test("Header 显示积分余额", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // Header 中积分显示
    await expect(page.getByText("500")).toBeVisible()
  })

  test("项目卡片列表正常渲染", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // 项目名称显示
    await expect(
      page.getByText("E2E测试-水利咨询项目")
    ).toBeVisible()
  })

  test("快捷操作区存在「浏览招标机会」入口", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // 浏览机会 CTA 링크
    const link = page.getByText("浏览招标机会")
    await expect(link).toBeVisible()
  })

  test("点击「浏览招标机会」跳转到机会列表页", async ({ page }) => {
    await page.route("**/v1/opportunities**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    })

    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    await page.getByText("浏览招标机会").first().click()
    await page.waitForURL("**/zh/opportunities**")
  })

  test("语言切换按钮可见并可点击", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    const langSwitch = page.getByText("EN")
    await expect(langSwitch).toBeVisible()
    await langSwitch.click()
    // 切换到英文路径
    await expect(page.url()).toMatch(/\/en\//)
  })
})
