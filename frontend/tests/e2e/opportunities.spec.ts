import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"
import {
  MOCK_OPPORTUNITY_LIST,
  MOCK_OPPORTUNITY,
  MOCK_PROJECT,
} from "./fixtures/mock-data"

/**
 * 招标机会测试
 * 策略：Mock 认证 + Mock 机会 API
 */
test.describe("招标机会", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthTokens(page)

    // Mock 积分
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )
  })

  /** 注册机会列表 Mock */
  async function mockOpportunityList(page: any, data = MOCK_OPPORTUNITY_LIST) {
    await page.route("**/v1/opportunities**", (route: any) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(data),
      })
    )
  }

  /** 注册机会详情 Mock */
  async function mockOpportunityDetail(page: any) {
    await page.route(`**/v1/opportunities/${MOCK_OPPORTUNITY.id}`, (route: any) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_OPPORTUNITY),
      })
    )
  }

  test("机会列表页面加载并渲染标题", async ({ page }) => {
    await mockOpportunityList(page)
    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("招标机会")).toBeVisible()
  })

  test("机会列表显示 mock 机会卡片", async ({ page }) => {
    await mockOpportunityList(page)
    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    await expect(
      page.getByText("E2E测试-水利工程技术咨询服务")
    ).toBeVisible()
    await expect(
      page.getByText("E2E测试-世界银行教育项目评估")
    ).toBeVisible()
  })

  test("搜索框存在并可输入", async ({ page }) => {
    await mockOpportunityList(page)
    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    const searchInput = page.locator('input[type="text"]').first()
    await expect(searchInput).toBeVisible()
    await searchInput.fill("水利")
    await expect(searchInput).toHaveValue("水利")
  })

  test("按回车触发搜索并携带参数", async ({ page }) => {
    let searchCalled = false
    await page.route("**/v1/opportunities**", (route) => {
      const url = route.request().url()
      if (url.includes("search=")) searchCalled = true
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    })

    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    const searchInput = page.locator('input[type="text"]').first()
    await searchInput.fill("水利")
    await searchInput.press("Enter")

    await page.waitForTimeout(500)
    expect(searchCalled).toBe(true)
  })

  test("机会列表显示来源 badge（ADB/WB）", async ({ page }) => {
    await mockOpportunityList(page)
    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    // 来源标签
    await expect(page.getByText("ADB").first()).toBeVisible()
    await expect(page.getByText("WB").first()).toBeVisible()
  })

  test("点击机会卡片跳转到详情页", async ({ page }) => {
    await mockOpportunityList(page)
    await mockOpportunityDetail(page)

    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    // 点击第一条机会
    await page.getByText("E2E测试-水利工程技术咨询服务").click()
    await page.waitForURL(`**/opportunities/${MOCK_OPPORTUNITY.id}**`)
  })

  test("机会详情页展示核心信息", async ({ page }) => {
    await mockOpportunityDetail(page)

    await page.goto(`/zh/opportunities/${MOCK_OPPORTUNITY.id}`)
    await page.waitForLoadState("networkidle")

    await expect(
      page.getByText("E2E测试-水利工程技术咨询服务")
    ).toBeVisible()
    await expect(page.getByText("中国")).toBeVisible()
  })

  test("机会详情页有「创建项目」按钮", async ({ page }) => {
    await mockOpportunityDetail(page)

    await page.goto(`/zh/opportunities/${MOCK_OPPORTUNITY.id}`)
    await page.waitForLoadState("networkidle")

    // 寻找创建项目按钮
    const createBtn = page.getByRole("button", { name: /创建项目/ })
    await expect(createBtn).toBeVisible()
  })

  test("从机会详情创建项目并跳转", async ({ page }) => {
    await mockOpportunityDetail(page)

    // Mock 创建项目 API
    await page.route("**/v1/projects", (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify(MOCK_PROJECT),
        })
      } else {
        route.continue()
      }
    })

    await page.goto(`/zh/opportunities/${MOCK_OPPORTUNITY.id}`)
    await page.waitForLoadState("networkidle")

    const createBtn = page.getByRole("button", { name: /创建项目/ })
    await createBtn.click()

    // 等待跳转到项目详情
    await page.waitForURL(`**/projects/${MOCK_PROJECT.id}**`)
  })

  test("分页控件显示（多页时）", async ({ page }) => {
    const multiPageData = {
      ...MOCK_OPPORTUNITY_LIST,
      total: 50,
      page: 1,
      pages: 3,
    }
    await mockOpportunityList(page, multiPageData)

    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    // 应有分页控件
    const nextPage = page.getByText("下一页").or(page.getByText("›")).first()
    await expect(nextPage).toBeVisible()
  })
})
