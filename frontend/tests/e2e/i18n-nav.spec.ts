import { test, expect } from "@playwright/test"
import { injectAuthTokens } from "./helpers/auth"

/**
 * 国际化与路由导航测试
 * 覆盖：语言切换、路由重定向、公开页面访问
 */
test.describe("国际化与导航", () => {
  // ── 公开页面（无需认证）─────────────────────────────────────

  test("帮助中心页面无需登录可正常访问", async ({ page }) => {
    // 不注入任何 token
    await page.goto("/zh/help")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("帮助中心").or(page.getByText("BidAgent"))).toBeVisible()
    // 页面不应重定向到登录
    expect(page.url()).not.toContain("/auth/login")
  })

  test("着陆页 /zh 无需登录可正常访问", async ({ page }) => {
    await page.goto("/zh")
    await page.waitForLoadState("networkidle")

    expect(page.url()).toContain("/zh")
    expect(page.url()).not.toContain("/auth/login")
  })

  test("登录页无需认证可访问", async ({ page }) => {
    await page.goto("/zh/auth/login")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("登录 BidAgent")).toBeVisible()
    expect(page.url()).not.toContain("/dashboard")
  })

  test("注册页无需认证可访问", async ({ page }) => {
    await page.goto("/zh/auth/register")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("注册账号")).toBeVisible()
    expect(page.url()).not.toContain("/dashboard")
  })

  // ── 路由重定向 ────────────────────────────────────────────────

  test("根路由 / 自动重定向到带 locale 的路径", async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    await page.goto("/")
    await page.waitForLoadState("networkidle")

    // 最终 URL 应包含 locale 前缀 (/zh/ 或 /en/)
    expect(page.url()).toMatch(/\/(zh|en)\//)
  })

  test("未认证访问 /zh/dashboard 重定向到登录页", async ({ page }) => {
    await page.goto("/zh/dashboard")
    await page.waitForURL("**/auth/login**")

    expect(page.url()).toContain("/auth/login")
  })

  test("redirect 参数在重定向时保留", async ({ page }) => {
    await page.goto("/zh/projects")
    await page.waitForURL("**/auth/login**")

    // URL 中应包含 redirect 参数
    expect(page.url()).toContain("redirect=")
  })

  // ── 语言切换 ──────────────────────────────────────────────────

  test("Header 语言切换按钮：CN→EN", async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // 点击 EN 按钮
    await page.getByText("EN").click()

    // URL 切换到 /en/
    await page.waitForURL("**/en/**")
    expect(page.url()).toContain("/en/")
  })

  test("英文版 Header 显示中文切换按钮", async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    await page.goto("/en/dashboard")
    await page.waitForLoadState("networkidle")

    // 英文页面应显示"中文"切换
    await expect(page.getByText("中文")).toBeVisible()
  })

  // ── Header 导航测试 ──────────────────────────────────────────

  test("Header Logo 点击返回仪表盘", async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )
    await page.route("**/v1/opportunities**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )

    await page.goto("/zh/opportunities")
    await page.waitForLoadState("networkidle")

    // 点击 Logo
    await page.getByText("BidAgent").first().click()
    await page.waitForURL("**/zh/dashboard**")
  })

  test("Header 导航「我的项目」链接跳转正确", async ({ page }) => {
    await injectAuthTokens(page)

    await page.route("**/v1/projects**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, pages: 1 }),
      })
    )
    await page.route("**/v1/credits/balance", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ balance: 500 }),
      })
    )

    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    await page.getByRole("link", { name: "我的项目" }).click()
    await page.waitForURL("**/zh/projects**")
  })
})
