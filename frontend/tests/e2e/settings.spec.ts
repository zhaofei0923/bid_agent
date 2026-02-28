import { test, expect } from "@playwright/test"
import { injectAuthTokens, MOCK_USER } from "./helpers/auth"

/**
 * 个人设置测试
 * 策略：Mock 认证 + Mock 设置相关 API
 */
test.describe("个人设置", () => {
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

  // ── 设置首页 ──────────────────────────────────────────────────

  test("设置页面正常加载", async ({ page }) => {
    await page.goto("/zh/settings")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("设置")).toBeVisible()
  })

  test("设置侧边导航显示所有分区", async ({ page }) => {
    await page.goto("/zh/settings")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("个人资料")).toBeVisible()
    await expect(page.getByText("安全设置")).toBeVisible()
    await expect(page.getByText("通知偏好")).toBeVisible()
  })

  test("侧边导航「积分设置」可见", async ({ page }) => {
    await page.goto("/zh/settings")
    await page.waitForLoadState("networkidle")

    // 积分相关链接
    await expect(page.getByRole("link", { name: /积分/ }).first()).toBeVisible()
  })

  // ── 个人资料页 ───────────────────────────────────────────────

  test("个人资料页展示当前用户信息", async ({ page }) => {
    await page.goto("/zh/settings/profile")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("个人资料")).toBeVisible()
    // 邮箱显示为只读
    await expect(page.getByText(MOCK_USER.email)).toBeVisible()
  })

  test("个人资料表单可以修改姓名", async ({ page }) => {
    // Mock PATCH /auth/me
    await page.route("**/v1/auth/me", (route) => {
      if (route.request().method() === "PUT" || route.request().method() === "PATCH") {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ...MOCK_USER, name: "新姓名" }),
        })
      } else {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_USER),
        })
      }
    })

    await page.goto("/zh/settings/profile")
    await page.waitForLoadState("networkidle")

    // 找姓名输入框
    const nameInput = page.locator('input[type="text"]').first()
    await nameInput.clear()
    await nameInput.fill("新姓名")

    // 提交
    const saveBtn = page.getByRole("button", { name: /保存/ })
    await saveBtn.click()

    // 出现保存成功提示
    await expect(
      page.getByText("保存成功").or(page.getByText("保存中"))
    ).toBeVisible({ timeout: 5000 })
  })

  // ── 安全设置页 ───────────────────────────────────────────────

  test("安全设置页展示修改密码表单", async ({ page }) => {
    await page.goto("/zh/settings/security")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("修改密码")).toBeVisible()
    await expect(page.getByText("当前密码")).toBeVisible()
    await expect(page.getByText("新密码")).toBeVisible()
  })

  test("新密码不一致时提交被阻止", async ({ page }) => {
    await page.goto("/zh/settings/security")
    await page.waitForLoadState("networkidle")

    const passwordInputs = page.locator('input[type="password"]')
    // 当前密码
    await passwordInputs.nth(0).fill("currentpassword123")
    // 新密码
    await passwordInputs.nth(1).fill("newpassword123")
    // 确认新密码（不一致）
    await passwordInputs.nth(2).fill("differentpassword456")

    const submitBtn = page.getByRole("button", { name: /修改密码/ })
    await submitBtn.click()

    // 应显示密码不一致错误
    await expect(
      page.getByText("两次输入的密码不一致")
    ).toBeVisible()
  })

  test("安全设置页显示两步验证 (2FA) 模块", async ({ page }) => {
    await page.goto("/zh/settings/security")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("两步验证")).toBeVisible()
  })

  // ── 通知偏好页 ──────────────────────────────────────────────

  test("通知偏好页正常加载", async ({ page }) => {
    await page.goto("/zh/settings/notifications")
    await page.waitForLoadState("networkidle")

    await expect(page.getByText("通知偏好")).toBeVisible()
  })

  // ── 导航链接测试 ─────────────────────────────────────────────

  test("设置侧边导航点击安全设置跳转", async ({ page }) => {
    await page.goto("/zh/settings")
    await page.waitForLoadState("networkidle")

    await page.getByRole("link", { name: "安全设置" }).first().click()
    await page.waitForURL("**/settings/security**")
  })

  test("设置侧边导航点击通知偏好跳转", async ({ page }) => {
    await page.goto("/zh/settings")
    await page.waitForLoadState("networkidle")

    await page.getByRole("link", { name: "通知偏好" }).first().click()
    await page.waitForURL("**/settings/notifications**")
  })
})
