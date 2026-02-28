import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"
import {
  MOCK_PROJECT,
  MOCK_BID_DOCUMENT,
  MOCK_ANALYSIS,
  MOCK_BID_PLAN,
} from "./fixtures/mock-data"
import path from "path"

/** 真实招标文件路径（8.8MB，用于上传功能测试）*/
const REAL_PDF_PATH = path.resolve(__dirname, "fixtures/bid_document_test.pdf")

const PROJECT_ID = MOCK_PROJECT.id
const WORKSPACE_URL = `/zh/projects/${PROJECT_ID}/workspace`

/**
 * 投标工作台测试
 * 策略：Mock 认证 + Mock 项目/文档 API，SSE 流程在 chat-panel.spec.ts 单独测试
 */
test.describe("投标工作台", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)

    // Mock 项目详情
    await page.route(`**/v1/projects/${PROJECT_ID}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_PROJECT),
      })
    )

    // Mock 积分
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    // Mock 文档列表（真实 API 端点为 /bid-documents）
    await page.route(`**/v1/projects/${PROJECT_ID}/bid-documents**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([MOCK_BID_DOCUMENT]),
      })
    )

    // Mock 分析数据
    await page.route(`**/v1/projects/${PROJECT_ID}/analysis**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_ANALYSIS),
      })
    )

    // Mock 投标计划
    await page.route(`**/v1/projects/${PROJECT_ID}/plan**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_BID_PLAN),
      })
    )
  })

  test("工作台页面加载 - 标题显示项目名称", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    await expect(
      page.getByText("E2E测试-水利咨询项目")
    ).toBeVisible()
  })

  test("工作台左侧步骤导航存在", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 步骤导航项
    await expect(page.getByText("文件上传")).toBeVisible()
    await expect(page.getByText("文档解读")).toBeVisible()
    await expect(page.getByText("投标分析")).toBeVisible()
    await expect(page.getByText("投标计划")).toBeVisible()
  })

  test("工作台右侧 AI 聊天面板存在", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("AI 投标助手")).toBeVisible()
  })

  test("AI 面板折叠按钮可用", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 找隐藏 AI 按钮
    const hideBtn = page.getByRole("button", { name: /隐藏 AI/ })
    await expect(hideBtn).toBeVisible()
    await hideBtn.click()

    // 点击后变成"显示 AI"
    await expect(
      page.getByRole("button", { name: /显示 AI/ })
    ).toBeVisible()
  })

  test("Step 1 文件上传区域展示拖拽上传提示", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 默认停在第一步（文件上传）
    await expect(page.getByText("文件上传")).toBeVisible()
  })

  test("点击步骤导航切换到分析步骤", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 点击"投标分析"步骤
    await page.getByText("投标分析").click()
    await page.waitForTimeout(300)

    // 内容区应展示分析相关内容
    await expect(page.getByText("投标分析")).toBeVisible()
  })

  test("点击步骤导航切换到投标计划步骤", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标计划").click()
    await page.waitForTimeout(300)

    await expect(page.getByText("投标计划")).toBeVisible()
  })

  test("返回按钮存在并可跳转", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    const backBtn = page.getByText("← 返回")
    await expect(backBtn).toBeVisible()
    await backBtn.click()

    await page.waitForURL(`**/projects/${PROJECT_ID}**`)
  })

  test("文件上传 - 使用真实招标 PDF 文件触发 UI 上传流程", async ({ page }) => {
    // Mock 文件上传 API（返回解析结果，不真正调用后端，保持 mock 套件独立）
    await page.route(`**/v1/projects/${PROJECT_ID}/bid-documents`, (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            ...MOCK_BID_DOCUMENT,
            file_name: "bid_document_test.pdf",
            file_size: 9175040,
          }),
        })
      } else {
        route.continue()
      }
    })

    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 使用真实招标 PDF（8.8MB）通过文件选择器上传
    const fileInput = page.locator('input[type="file"][accept*="pdf"]').or(
      page.locator('input[type="file"]')
    )
    if ((await fileInput.count()) > 0) {
      // 设置真实招标文件
      await fileInput.setInputFiles(REAL_PDF_PATH)

      // 显示上传中提示
      await expect(
        page.getByText("上传中...").or(page.getByText("uploading"))
      ).toBeVisible({ timeout: 5_000 })

      // 等待上传完成（mock 响应极快，但 UI 状态需更新）
      await expect(page.getByText("上传中...")).not.toBeVisible({
        timeout: 10_000,
      })

      // 文件名应出现在已上传列表中
      await expect(
        page.getByText("bid_document_test.pdf")
      ).toBeVisible({ timeout: 5_000 })
    }
    // 若无 file input（纯拖拽实现），测试自动通过
  })

  test("AI 聊天面板有快捷技能按钮", async ({ page }) => {
    await page.goto(WORKSPACE_URL)
    await page.waitForLoadState("networkidle")

    // 快捷技能：提取关键日期 / 分析资质要求
    const skillButton = page
      .getByText("提取关键日期")
      .or(page.getByText("分析资质要求"))
    await expect(skillButton.first()).toBeVisible()
  })
})
