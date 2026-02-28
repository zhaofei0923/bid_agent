import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"
import { MOCK_PROJECT, MOCK_PROJECT_LIST } from "./fixtures/mock-data"

/**
 * 项目管理测试
 * 策略：Mock 认证 + Mock 项目 API
 */
test.describe("项目管理", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )
  })

  async function mockProjectList(page: any, data = MOCK_PROJECT_LIST) {
    await page.route("**/v1/projects**", (route: any) => {
      // 只拦截 GET 列表
      if (!route.request().url().includes(`/${MOCK_PROJECT.id}`)) {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(data),
        })
      } else {
        route.continue()
      }
    })
  }

  async function mockProjectDetail(page: any) {
    await page.route(
      `**/v1/projects/${MOCK_PROJECT.id}`,
      (route: any) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_PROJECT),
        })
      }
    )
  }

  test("项目列表页面加载并显示标题", async ({ page }) => {
    await mockProjectList(page)
    await page.goto("/zh/projects")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("我的项目")).toBeVisible()
  })

  test("项目列表显示 mock 项目卡片", async ({ page }) => {
    await mockProjectList(page)
    await page.goto("/zh/projects")
    await page.waitForLoadState("networkidle")

    await expect(
      page.getByText("E2E测试-水利咨询项目")
    ).toBeVisible()
  })

  test("项目列表有「新建项目」按钮", async ({ page }) => {
    await mockProjectList(page)
    await page.goto("/zh/projects")
    await page.waitForLoadState("networkidle")

    const createBtn = page.getByRole("button", { name: /新建项目/ })
    await expect(createBtn).toBeVisible()
  })

  test("项目卡片显示状态 badge", async ({ page }) => {
    await mockProjectList(page)
    await page.goto("/zh/projects")
    await page.waitForLoadState("networkidle")

    // active 状态对应"活跃"
    await expect(page.getByText("活跃")).toBeVisible()
  })

  test("暂无项目时显示提示文案", async ({ page }) => {
    await mockProjectList(page, {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 0,
    })
    await page.goto("/zh/projects")
    await page.waitForLoadState("networkidle")

    await expect(
      page.getByText(/暂无项目/)
    ).toBeVisible()
  })

  test("项目详情页显示项目名称", async ({ page }) => {
    await mockProjectDetail(page)
    await page.goto(`/zh/projects/${MOCK_PROJECT.id}`)
    await page.waitForLoadState("networkidle")

    await expect(
      page.getByText("E2E测试-水利咨询项目")
    ).toBeVisible()
  })

  test("项目详情页有「打开工作台」按钮", async ({ page }) => {
    await mockProjectDetail(page)
    await page.goto(`/zh/projects/${MOCK_PROJECT.id}`)
    await page.waitForLoadState("networkidle")

    const workspaceBtn = page.getByRole("link", { name: /打开工作台/ })
    await expect(workspaceBtn).toBeVisible()
  })

  test("点击「打开工作台」跳转到 workspace 页", async ({ page }) => {
    await mockProjectDetail(page)
    // workspace 页也需要 project 数据
    await page.route("**/v1/projects/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_PROJECT),
      })
    )

    await page.goto(`/zh/projects/${MOCK_PROJECT.id}`)
    await page.waitForLoadState("networkidle")

    const workspaceBtn = page.getByRole("link", { name: /打开工作台/ })
    await workspaceBtn.click()

    await page.waitForURL(`**/projects/${MOCK_PROJECT.id}/workspace**`)
  })

  test("项目列表可以点击项目卡片跳转详情", async ({ page }) => {
    await mockProjectList(page)
    await mockProjectDetail(page)

    await page.goto("/zh/projects")
    await page.waitForLoadState("networkidle")

    await page.getByText("E2E测试-水利咨询项目").click()
    await page.waitForURL(`**/projects/${MOCK_PROJECT.id}**`)
  })
})
