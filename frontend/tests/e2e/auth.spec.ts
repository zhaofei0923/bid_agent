import { test, expect } from "@playwright/test"
import {
  mockLoginSuccess,
  mockLoginFailure,
  mockRegisterSuccess,
  mockAuthMeRoute,
  MOCK_TOKENS,
} from "./helpers/auth"

/**
 * 认证流程测试
 * 策略：全 Mock（拦截 /auth/login、/auth/register、/auth/me）
 */
test.describe("认证流程", () => {
  // ─── 登录页面 ───────────────────────────────────────────────

  test("登录页面正确展示必要元素", async ({ page }) => {
    await page.goto("/zh/auth/login")

    await expect(page.getByText("登录 BidAgent")).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
    // 注册跳转链接
    await expect(page.getByText("注册")).toBeVisible()
  })

  test("登录失败显示错误提示", async ({ page }) => {
    await mockLoginFailure(page)

    await page.goto("/zh/auth/login")

    await page.locator('input[type="email"]').fill("wrong@example.com")
    await page.locator('input[type="password"]').fill("wrongpassword")
    await page.locator('button[type="submit"]').click()

    // 等待错误消息出现
    await expect(
      page.getByText("登录失败，请检查邮箱和密码")
    ).toBeVisible()
  })

  test("登录成功写入 token 并跳转仪表盘", async ({ page }) => {
    await mockLoginSuccess(page)

    await page.goto("/zh/auth/login")
    await page.locator('input[type="email"]').fill("test@bidagent.com")
    await page.locator('input[type="password"]').fill("password123")
    await page.locator('button[type="submit"]').click()

    // 等待跳转到仪表盘
    await page.waitForURL("**/zh/dashboard")

    // 验证 localStorage 已写入 token
    const accessToken = await page.evaluate(() =>
      localStorage.getItem("access_token")
    )
    expect(accessToken).toBe(MOCK_TOKENS.access_token)
  })

  test("登录按钮在提交时禁用防止重复提交", async ({ page }) => {
    // 延迟响应模拟网络慢
    await page.route("**/v1/auth/login", async (route) => {
      await new Promise((r) => setTimeout(r, 1000))
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_TOKENS),
      })
    })
    await mockAuthMeRoute(page)

    await page.goto("/zh/auth/login")
    await page.locator('input[type="email"]').fill("test@bidagent.com")
    await page.locator('input[type="password"]').fill("password123")

    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()

    // 按钮应显示为禁用状态（有 disabled 属性）
    await expect(submitButton).toBeDisabled()
  })

  // ─── 注册页面 ───────────────────────────────────────────────

  test("注册页面展示所有必填字段", async ({ page }) => {
    await page.goto("/zh/auth/register")

    await expect(page.getByText("注册账号")).toBeVisible()
    // 姓名、邮箱、密码
    await expect(page.locator('input[type="text"]').first()).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]').first()).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test("注册成功跳转仪表盘", async ({ page }) => {
    await mockRegisterSuccess(page)

    await page.goto("/zh/auth/register")
    // 填写姓名
    await page.locator('input[type="text"]').first().fill("测试用户")
    await page.locator('input[type="email"]').fill("newuser@bidagent.com")
    await page.locator('input[type="password"]').first().fill("password123")

    await page.locator('button[type="submit"]').click()

    await page.waitForURL("**/zh/dashboard")
  })

  // ─── 认证守卫 ────────────────────────────────────────────────

  test("未认证用户访问受保护页面被重定向到登录页", async ({ page }) => {
    // 不注入 token，不 mock auth/me
    // 让 auth/me 调用失败（实际 localStorage 为空，不会发请求）
    await page.goto("/zh/dashboard")

    // 应重定向到登录页
    await page.waitForURL("**/auth/login**")
    await expect(page.url()).toContain("/auth/login")
  })

  test("登出清空 token 并返回首页", async ({ page }) => {
    await mockAuthMeRoute(page)
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock_access_token_for_e2e_testing")
      localStorage.setItem(
        "refresh_token",
        "mock_refresh_token_for_e2e_testing"
      )
    })

    await page.goto("/zh/dashboard")
    await page.waitForLoadState("networkidle")

    // 点击退出登录按钮
    await page.getByRole("button", { name: "退出登录" }).click()

    // localStorage 应已清空
    const accessToken = await page.evaluate(() =>
      localStorage.getItem("access_token")
    )
    expect(accessToken).toBeNull()
  })

  test("登录页提供到注册页的跳转链接", async ({ page }) => {
    await page.goto("/zh/auth/login")
    const registerLink = page.getByText("注册").first()
    await expect(registerLink).toBeVisible()
    await registerLink.click()
    await page.waitForURL("**/auth/register")
  })

  test("注册页提供到登录页的跳转链接", async ({ page }) => {
    await page.goto("/zh/auth/register")
    const loginLink = page.getByText("已有账号").first()
    await expect(loginLink).toBeVisible()
  })
})
