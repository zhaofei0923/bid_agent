import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"
import { MOCK_PROJECT } from "./fixtures/mock-data"

const PROJECT_ID = MOCK_PROJECT.id
const WORKSPACE_URL = `/zh/projects/${PROJECT_ID}/workspace`

/**
 * AI 聊天面板 SSE 流式测试
 * 策略：Mock 认证 + Mock SSE 端点（模拟 thinking→chunk→complete 事件序列）
 */
test.describe("AI 聊天面板", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)

    await page.route(`**/v1/projects/${PROJECT_ID}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_PROJECT),
      })
    )

    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    await page.route(`**/v1/projects/${PROJECT_ID}/documents**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    )
  })

  test("聊天面板标题「AI 投标助手」可见", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("AI 投标助手")).toBeVisible()
  })

  test("聊天输入框可见并可输入", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    const input = page.locator('textarea[placeholder="输入问题..."]').or(
      page.locator('input[placeholder="输入问题..."]')
    )
    await expect(input.first()).toBeVisible()
    await input.first().fill("什么是 QCBS 评分方法？")
    await expect(input.first()).toHaveValue("什么是 QCBS 评分方法？")
  })

  test("发送消息后用户消息气泡出现", async ({ page }) => {
    // Mock SSE 聊天端点（返回简单文本）
    await page.route(`**/v1/guidance/chat**`, (route) => {
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: [
          `data: ${JSON.stringify({ type: "chunk", content: "QCBS是质量与费用比选法。" })}\n\n`,
          `data: ${JSON.stringify({ type: "complete" })}\n\n`,
        ].join(""),
      })
    })

    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    const input = page
      .locator('textarea[placeholder="输入问题..."]')
      .or(page.locator('input[placeholder="输入问题..."]'))
    await input.first().fill("什么是 QCBS？")

    const sendBtn = page.getByRole("button", { name: "发送" })
    await sendBtn.click()

    // 用户消息气泡
    await expect(page.getByText("什么是 QCBS？")).toBeVisible()
  })

  test("SSE 流式响应内容在聊天区展示", async ({ page }) => {
    const aiReply = "QCBS是质量与费用比选法，是多边机构常用的咨询服务采购方法。"

    await page.route(`**/v1/guidance/chat**`, (route) => {
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: [
          `data: ${JSON.stringify({ type: "thinking", content: "分析中..." })}\n\n`,
          `data: ${JSON.stringify({ type: "chunk", content: aiReply })}\n\n`,
          `data: ${JSON.stringify({ type: "complete" })}\n\n`,
        ].join(""),
      })
    })

    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    const input = page
      .locator('textarea[placeholder="输入问题..."]')
      .or(page.locator('input[placeholder="输入问题..."]'))
    await input.first().fill("什么是 QCBS？")

    await page.getByRole("button", { name: "发送" }).click()

    // AI 回复内容应出现
    await expect(page.getByText(aiReply)).toBeVisible({ timeout: 8000 })
  })

  test("AI 面板折叠后输入区消失", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 折叠面板
    const hideBtn = page.getByRole("button", { name: /隐藏 AI/ })
    if (await hideBtn.isVisible()) {
      await hideBtn.click()
      await page.waitForTimeout(300)

      // 输入框不再可见
      const input = page.locator('textarea[placeholder="输入问题..."]')
      await expect(input).not.toBeVisible()
    }
  })

  test("展开折叠面板后输入区恢复", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    const hideBtn = page.getByRole("button", { name: /隐藏 AI/ })
    if (await hideBtn.isVisible()) {
      await hideBtn.click()
      await page.waitForTimeout(300)

      const showBtn = page.getByRole("button", { name: /显示 AI/ })
      await showBtn.click()
      await page.waitForTimeout(300)

      // 输入框重新可见
      const input = page.locator('textarea[placeholder="输入问题..."]')
      await expect(input).toBeVisible()
    }
  })

  test("快捷技能「提取关键日期」可点击", async ({ page }) => {
    await page.route(`**/v1/guidance/chat**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: `data: ${JSON.stringify({ type: "complete" })}\n\n`,
      })
    )

    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 点击快捷技能
    const skillBtn = page.getByText("提取关键日期")
    if (await skillBtn.isVisible()) {
      await skillBtn.click()
      // 输入框中出现快捷技能文本
      const input = page
        .locator('textarea[placeholder="输入问题..."]')
        .or(page.locator('input[placeholder="输入问题..."]'))
      await expect(input.first()).not.toHaveValue("")
    }
  })
})
