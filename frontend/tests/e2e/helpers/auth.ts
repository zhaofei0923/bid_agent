import type { Page } from "@playwright/test"

/** Mock 用户数据 — 认证测试中使用的固定用户 */
export const MOCK_USER = {
  id: "usr_test_001",
  email: "test@bidagent.com",
  name: "测试用户",
  company: "测试公司",
  credits_balance: 500,
  role: "user",
  created_at: "2025-01-01T00:00:00Z",
}

/** Mock tokens — 登录成功后返回 */
export const MOCK_TOKENS = {
  access_token: "mock_access_token_for_e2e_testing",
  refresh_token: "mock_refresh_token_for_e2e_testing",
  token_type: "Bearer",
}

/**
 * 向 localStorage 注入 Mock Token，跳过 UI 登录流程
 * 同时拦截 /auth/me 确保 loadUser() 成功
 */
export async function injectAuthTokens(page: Page): Promise<void> {
  // 先拦截 /auth/me（loadUser 调用）
  await mockAuthMeRoute(page)

  // 注入 localStorage tokens
  await page.addInitScript(() => {
    localStorage.setItem("access_token", "mock_access_token_for_e2e_testing")
    localStorage.setItem("refresh_token", "mock_refresh_token_for_e2e_testing")
  })
}

/**
 * Mock /auth/me 端点 — 返回固定 mock 用户
 */
export async function mockAuthMeRoute(page: Page): Promise<void> {
  await page.route("**/v1/auth/me", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_USER),
    })
  })
}

/**
 * Mock /auth/login 端点 — 成功登录
 */
export async function mockLoginSuccess(page: Page): Promise<void> {
  await page.route("**/v1/auth/login", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_TOKENS),
    })
  })
  await mockAuthMeRoute(page)
}

/**
 * Mock /auth/login 端点 — 登录失败（401）
 */
export async function mockLoginFailure(page: Page): Promise<void> {
  await page.route("**/v1/auth/login", (route) => {
    route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "邮箱或密码错误" }),
    })
  })
}

/**
 * Mock /auth/register 端点 — 注册成功
 */
export async function mockRegisterSuccess(page: Page): Promise<void> {
  await page.route("**/v1/auth/register", (route) => {
    route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(MOCK_TOKENS),
    })
  })
  await mockAuthMeRoute(page)
}

/**
 * Mock /credits/balance 端点
 */
export async function mockCreditsBalance(
  page: Page,
  balance = 500
): Promise<void> {
  await page.route("**/v1/credits/balance", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ balance }),
    })
  })
}
