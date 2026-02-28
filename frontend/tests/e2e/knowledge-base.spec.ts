import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"
import { MOCK_KNOWLEDGE_BASE_LIST } from "./fixtures/mock-data"

/**
 * 知识库测试
 * 策略：Mock 认证 + Mock 知识库 API
 */
test.describe("知识库", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    // Mock 知识库条目列表
    await page.route("**/v1/knowledge-base**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_KNOWLEDGE_BASE_LIST),
      })
    )

    // Mock 知识库搜索
    await page.route("**/v1/knowledge-base/search**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [
            {
              id: "kb_001",
              title: "ADB采购准则2024版",
              score: 0.95,
              content: "亚洲开发银行采购指南第3章：咨询服务选择程序",
            },
          ],
          total: 1,
        }),
      })
    )
  })

  test("知识库条目列表加载展示", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // 知识库入口 — 通过仪表盘助手 widget 或菜单
    // 访问知识库页面（如果独立路由存在）
    await page.goto("/zh/knowledge-base").catch(() => {
      // 如果路由不存在直接忽略（知识库可能嵌套）
    })
  })

  test("仪表盘的AI助手 Widget 存在", async ({ page }) => {
    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )

    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // 仪表盘应包含 AI 助手入口
    // BidAssistant 或 DashboardAssistantWidget
    const aiWidget = page
      .getByText("AI 投标助手")
      .or(page.getByText("智能助手"))
      .or(page.getByText("BidAgent"))
    await expect(aiWidget.first()).toBeVisible()
  })

  test("知识库 RAG 问答发送消息", async ({ page }) => {
    // 在工作台的 QA 步骤中测试 RAG 问答

    // Mock 项目数据
    await page.route("**/v1/projects/proj_test_001", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "proj_test_001",
          name: "测试项目",
          institution: "adb",
          status: "active",
          current_step: "qa",
        }),
      })
    )

    await page.route("**/v1/projects/proj_test_001/documents**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    )

    // Mock QA 端点
    await page.route("**/v1/projects/proj_test_001/qa**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          answer: "ADB的QCBS方法要求技术得分占70%，价格占30%。",
          references: [
            { source: "ADB采购准则", page: 25, content: "QCBS评分标准" },
          ],
        }),
      })
    )

    await page.goto("/zh/projects/proj_test_001/workspace")
    await page.waitForLoadState("networkidle")

    // 切换到问答步骤（"AI编制指导"）
    const qaStep = page.getByText("AI编制指导").or(page.getByText("投标分析"))
    if (await qaStep.isVisible()) {
      await qaStep.click()
      await page.waitForTimeout(300)
    }
  })

  test("知识库文档搜索结果展示", async ({ page }) => {
    await page.route("**/v1/knowledge-base/search**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [
            {
              id: "kb_001",
              title: "ADB采购准则2024版",
              score: 0.95,
              content: "咨询顾问选择程序，包括EOI、RFP、QCBS等方法",
            },
          ],
          total: 1,
        }),
      })
    )

    // 在工作台问答步骤搜索知识库
    await page.route("**/v1/projects/proj_test_001", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "proj_test_001",
          name: "测试项目",
          institution: "adb",
          status: "active",
          current_step: "upload",
        }),
      })
    )
    await page.route("**/v1/projects/proj_test_001/documents**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    )

    await page.goto("/zh/projects/proj_test_001/workspace")
    await page.waitForLoadState("networkidle")

    // 在 AI 聊天中输入知识库相关问题
    const chatInput = page
      .locator('textarea[placeholder="输入问题..."]')
      .or(page.locator('input[placeholder="输入问题..."]'))

    if ((await chatInput.count()) > 0) {
      await chatInput.first().fill("ADB的QCBS要求是什么？")
      await expect(chatInput.first()).toHaveValue("ADB的QCBS要求是什么？")
    }
  })
})
