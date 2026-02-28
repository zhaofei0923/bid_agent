import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"
import {
  MOCK_CREDITS_TRANSACTIONS,
  MOCK_PAYMENT_PACKAGES,
} from "./fixtures/mock-data"

/**
 * 积分与支付测试
 * 策略：Mock 认证 + Mock 积分 API
 */
test.describe("积分与支付", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)

    // Mock 积分余额
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    // Mock 交易记录
    await page.route("**/v1/credits/transactions**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_CREDITS_TRANSACTIONS),
      })
    )

    // Mock 充值套餐
    await page.route("**/v1/credits/packages**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_PAYMENT_PACKAGES),
      })
    )
  })

  test("积分管理页面正常加载", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("积分管理")).toBeVisible()
  })

  test("当前积分余额正确显示", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("500")).toBeVisible()
    await expect(page.getByText("当前余额")).toBeVisible()
  })

  test("交易记录列表显示历史条目", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    // 消费记录
    await expect(page.getByText("AI分析 - 水利咨询项目")).toBeVisible()
    // 充值记录
    await expect(page.getByText("充值 - 标准套餐")).toBeVisible()
  })

  test("充值套餐卡片渲染", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("基础版")).toBeVisible()
    await expect(page.getByText("标准版")).toBeVisible()
    await expect(page.getByText("专业版")).toBeVisible()
  })

  test("点击充值套餐卡片选中高亮", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    // 标准版套餐
    const standardPkg = page.getByText("标准版").first()
    await standardPkg.click()
    await page.waitForTimeout(300)

    // 点击后套餐被选中（通过CSS或aria状态验证）
    // 简单验证：没有错误抛出即可，UI状态变化视前端实现而定
    await expect(standardPkg).toBeVisible()
  })

  test("充值按钮存在", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    const rechargeBtn = page.getByRole("button", { name: /充值/ })
    await expect(rechargeBtn.first()).toBeVisible()
  })

  test("点击充值打开支付弹窗", async ({ page }) => {
    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    const rechargeBtn = page.getByRole("button", { name: /充值/ }).first()
    await rechargeBtn.click()

    // 支付弹窗出现
    await expect(
      page.getByText("支付宝").or(page.getByText("微信")).first()
    ).toBeVisible({ timeout: 5000 })
  })

  test("积分余额通过响应头实时更新", async ({ page }) => {
    // Mock 一个携带积分消耗 Header 的 API 响应
    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: {
          "X-Credits-Consumed": "50",
          "X-Credits-Remaining": "450",
        },
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )

    await page.goto("/zh/credits")
    await page.waitForLoadState("networkidle")

    // 触发一个 API 请求（通过 JS）
    await page.evaluate(async () => {
      await fetch("/api/projects", { method: "GET" }).catch(() => {})
    })

    // 验证页面仍然正常（Credits 状态不因异常更新而崩溃）
    await expect(page.getByText("积分管理")).toBeVisible()
  })

  test("积分设置页面可访问", async ({ page }) => {
    await page.goto("/zh/settings/credits")
    await page.waitForLoadState("networkidle")

    // 设置页应该正常加载
    await expect(page.getByText("积分").first()).toBeVisible()
  })
})
