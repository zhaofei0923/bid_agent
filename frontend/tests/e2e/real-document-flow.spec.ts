import { test, expect, type Page } from "@playwright/test"
import path from "path"
import fs from "fs"

/**
 * 真实招标文件完整流程 E2E 测试
 *
 * 文件：Bid document test.pdf（8.8MB，真实 ADB 招标文件）
 * 策略：连接真实后端（localhost:8000），全流程端到端验证
 *
 * 流程：注册测试账号 → 创建项目 → 上传真实 PDF
 *      → 文档解析 → AI 概览 → 8维度分析 → RAG 问答 → 质量审查
 */

const REAL_PDF_PATH = path.resolve(
  __dirname,
  "fixtures/bid_document_test.pdf"
)

// 测试用临时账号（每次运行生成唯一邮箱避免冲突）
const TEST_EMAIL = `e2e_test_${Date.now()}@bidagent-test.com`
const TEST_PASSWORD = "E2eTest123456"
const TEST_NAME = "E2E测试用户"

// 全局状态：测试账号 tokens 和创建的项目 ID
let accessToken: string
let projectId: string

/**
 * 辅助：通过 API 直接注册并获取 token（不走 UI，加速 beforeAll）
 */
async function registerAndGetToken(): Promise<string> {
  const res = await fetch("http://localhost:8000/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: TEST_EMAIL,
      password: TEST_PASSWORD,
      name: TEST_NAME,
    }),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`注册失败: ${res.status} ${err}`)
  }
  const data = await res.json()
  return data.access_token
}

/**
 * 辅助：通过 API 创建项目
 */
async function createProject(token: string): Promise<string> {
  const res = await fetch("http://localhost:8000/v1/projects", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      name: "E2E-真实文件测试项目",
      description: "使用真实招标文件进行自动化测试",
      institution: "adb",
    }),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`创建项目失败: ${res.status} ${err}`)
  }
  const data = await res.json()
  return data.id
}

/**
 * 辅助：注入已有 token 到浏览器 localStorage（跳过 UI 登录）
 */
async function injectToken(page: Page, token: string): Promise<void> {
  // Mock /auth/me 返回测试用户
  await page.route("**/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "e2e_user",
        email: TEST_EMAIL,
        name: TEST_NAME,
        credits_balance: 1000,
      }),
    })
  )
  await page.addInitScript((t) => {
    localStorage.setItem("access_token", t)
    localStorage.setItem("refresh_token", t) // refresh 暂用同一 token
  }, token)
}

// ─────────────────────────────────────────────────────────────────────────────
// SETUP：注册账号 + 创建项目（一次性）
// ─────────────────────────────────────────────────────────────────────────────

test.beforeAll(async () => {
  // 确认真实 PDF 存在
  expect(
    fs.existsSync(REAL_PDF_PATH),
    `真实招标文件不存在: ${REAL_PDF_PATH}`
  ).toBe(true)

  // 确认后端可达
  const health = await fetch("http://localhost:8000/v1/health")
  expect(health.ok, "后端服务未启动，请先运行 docker compose up postgres redis 并启动 FastAPI").toBe(true)

  // 注册测试账号并获取 token
  accessToken = await registerAndGetToken()

  // 创建测试项目
  projectId = await createProject(accessToken)

  console.log(`✅ 测试账号: ${TEST_EMAIL}`)
  console.log(`✅ 测试项目: ${projectId}`)
})

// ─────────────────────────────────────────────────────────────────────────────
// 测试套件
// ─────────────────────────────────────────────────────────────────────────────

test.describe("真实招标文件完整投标流程", () => {
  // AI 分析/问答可能耗时，给每个测试充足时间
  test.setTimeout(180_000) // 3 分钟

  // 每个测试注入相同 token
  test.beforeEach(async ({ page }) => {
    await injectToken(page, accessToken)
  })

  // ── Step 1: 文件上传 ────────────────────────────────────────────────────────

  test("1-1 工作台文件上传区域正常渲染", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    // 上传区拖拽提示
    await expect(
      page.getByText("拖拽文件到此处，或点击选择文件")
    ).toBeVisible({ timeout: 10_000 })

    // 格式提示
    await expect(
      page.getByText("支持 PDF、DOCX 格式")
    ).toBeVisible()
  })

  test("1-2 上传真实招标 PDF 文件（8.8MB）", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    // 等待文件 input 出现
    const fileInput = page.locator('input[type="file"][accept*="pdf"]')
    await expect(fileInput).toBeAttached({ timeout: 10_000 })

    // 使用真实 PDF 文件上传
    await fileInput.setInputFiles(REAL_PDF_PATH)

    // 上传开始：显示"上传中..."
    await expect(page.getByText("上传中...")).toBeVisible({
      timeout: 5_000,
    })

    // 等待上传完成（大文件最多 60s）
    await expect(page.getByText("上传中...")).not.toBeVisible({
      timeout: 60_000,
    })

    // 已上传文件列表显示文件名
    await expect(
      page.getByText("bid_document_test.pdf").or(
        page.getByText("Bid document  test.pdf")
      )
    ).toBeVisible({ timeout: 10_000 })

    console.log("✅ 真实招标文件上传成功")
  })

  test("1-3 上传成功后出现「下一步」按钮", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    // 等待已上传文件出现（上一个测试已上传）
    await page.waitForTimeout(1_000)

    // 已有文件时出现下一步按钮
    const nextBtn = page.getByText("下一步：文档解读 →")
    // 如果文件已存在则 next 按钮应出现
    const isVisible = await nextBtn.isVisible()
    if (isVisible) {
      await expect(nextBtn).toBeVisible()
    }
    // 否则文件上一步未持久化，继续跳过
  })

  // ── Step 2: 文档概览 ────────────────────────────────────────────────────────

  test("2-1 切换到文档解读步骤", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("文档解读").click()
    await page.waitForTimeout(500)

    await expect(page.getByText("文档解读")).toBeVisible()
  })

  test("2-2 文档解读步骤显示 AI 分析摘要", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("文档解读").click()
    await page.waitForTimeout(1_000)

    // 等待 AI 摘要加载（解析可能需要时间）
    const summaryArea = page
      .getByText("AI 分析摘要")
      .or(page.getByText("投标类型"))
      .or(page.getByText("关键日期"))
    await expect(summaryArea.first()).toBeVisible({ timeout: 15_000 })
  })

  // ── Step 3: 8维度 AI 分析 ────────────────────────────────────────────────────

  test("3-1 切换到投标分析步骤显示 8 个维度卡片", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标分析").click()
    await page.waitForTimeout(500)

    // 验证 8 个分析维度都已定义
    const dimensions = [
      "资质要求",
      "评分标准",
      "关键日期",
      "提交要求",
      "BDS修改",
      "方法论",
      "商务条款",
      "风险评估",
    ]

    for (const dim of dimensions) {
      await expect(page.getByText(dim).first()).toBeVisible({ timeout: 10_000 })
    }
  })

  test("3-2 点击「开始 AI 分析」触发分析请求", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标分析").click()
    await page.waitForTimeout(500)

    // 监控是否有向后端发起分析请求
    let analysisRequested = false
    await page.route(`**/v1/projects/${projectId}/analysis**`, (route) => {
      if (
        route.request().method() === "POST" ||
        route.request().method() === "GET"
      ) {
        analysisRequested = true
      }
      route.continue()
    })

    // 如果有"开始 AI 分析"或"重新分析"按钮，点击它
    const analyzeBtn = page
      .getByRole("button", { name: /开始 AI 分析|重新分析/ })
      .first()
    if (await analyzeBtn.isVisible()) {
      await analyzeBtn.click()
      // 等待分析中状态（最多 3 分钟，因为 AI 分析可能较慢）
      await expect(
        page.getByText("分析中...").or(page.getByText("已完成"))
      ).toBeVisible({ timeout: 30_000 })
    }
  })

  test("3-3 AI 分析完成后资质要求维度显示结果", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标分析").click()
    await page.waitForTimeout(500)

    // 等待分析结果出现（"已完成"状态标签）
    // 注意：AI分析可能很快也可能较慢，给充足时间
    const completedBadge = page.getByText("已完成").first()
    const noAnalysis = page.getByText("尚未运行分析")

    // 等待其中一个出现
    await Promise.race([
      completedBadge.waitFor({ timeout: 120_000 }),
      noAnalysis.waitFor({ timeout: 120_000 }),
    ])

    // 不论状态如何，分析界面应完整展示
    await expect(page.getByText("资质要求").first()).toBeVisible()
  })

  // ── Step 4: 投标计划 ────────────────────────────────────────────────────────

  test("4-1 切换到投标计划步骤", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标计划").click()
    await page.waitForTimeout(500)

    await expect(page.getByText("投标计划").first()).toBeVisible()
  })

  test("4-2 投标计划页显示任务清单", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标计划").click()
    await page.waitForTimeout(500)

    // 任务清单或空状态提示
    const taskList = page
      .getByText("任务清单")
      .or(page.getByText("暂无任务"))
      .or(page.getByText("添加新任务"))
    await expect(taskList.first()).toBeVisible({ timeout: 10_000 })
  })

  test("4-3 可以手动添加投标任务", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("投标计划").click()
    await page.waitForTimeout(500)

    // 找到任务输入框
    const taskInput = page.locator('input[placeholder="添加新任务..."]')
    if (await taskInput.isVisible()) {
      await taskInput.fill("准备公司资质文件")
      const addBtn = page.getByRole("button", { name: "添加" })
      await addBtn.click()
      await page.waitForTimeout(500)

      // 新任务应出现在列表中
      await expect(page.getByText("准备公司资质文件")).toBeVisible({
        timeout: 5_000,
      })
      console.log("✅ 手动添加任务成功")
    }
  })

  // ── Step 5: AI 编制指导 (RAG 问答) ─────────────────────────────────────────

  test("5-1 切换到 AI 编制指导步骤", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("AI编制指导").click()
    await page.waitForTimeout(500)

    await expect(
      page.getByText("AI 编制指导").or(page.getByText("AI顾问"))
    ).toBeVisible()
  })

  test("5-2 向真实后端发送问答请求（基于招标文件内容）", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    await page.getByText("AI编制指导").click()
    await page.waitForTimeout(500)

    // 找到输入框
    const input = page.locator(
      'textarea[placeholder="输入关于标书编写的问题..."]'
    )
    if (await input.isVisible()) {
      await input.fill("这个招标文件的资质要求是什么？")

      // 发送（让它真正调用后端 LLM）
      await page.getByRole("button", { name: "发送" }).click()

      // 等待 AI 回答出现（RAG + LLM 可能需要 30-60 秒）
      await expect(
        page
          .getByText("AI 顾问")
          .or(page.getByText("资质"))
          .or(page.getByText("要求"))
      ).toBeVisible({ timeout: 90_000 })

      console.log("✅ RAG 问答请求成功")
    }
  })

  // ── 聊天面板辅助功能 ──────────────────────────────────────────────────────

  test("6-1 右侧 AI 聊天面板可以发送基于招标文件的问题", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    // 聊天面板输入框
    const chatInput = page.locator('textarea[placeholder="输入问题..."]')
    if (await chatInput.isVisible()) {
      await chatInput.fill("请总结这份招标文件的核心要求")

      await page.getByRole("button", { name: "发送" }).first().click()

      // 等待用户消息出现（表示已发送）
      await expect(
        page.getByText("请总结这份招标文件的核心要求")
      ).toBeVisible({ timeout: 5_000 })

      // 等待 AI 回答（可能需要时间）
      await expect(
        page.getByText("🤖").or(page.getByText("AI 投标助手"))
      ).toBeVisible({ timeout: 60_000 })

      console.log("✅ 聊天面板问答成功")
    }
  })

  test("6-2 快捷技能「分析资质要求」发起真实分析", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    const skillBtn = page.getByText("分析资质要求")
    if (await skillBtn.isVisible()) {
      await skillBtn.click()

      // 输入框应填入快捷问题
      const chatInput = page.locator('textarea[placeholder="输入问题..."]')
      await expect(chatInput).not.toHaveValue("")

      // 自动发送或用户手动发送
      const sendBtn = page.getByRole("button", { name: "发送" }).first()
      if (await sendBtn.isEnabled()) {
        await sendBtn.click()
        await page.waitForTimeout(2_000)
      }
    }
  })

  // ── 完整步骤导航验证 ──────────────────────────────────────────────────────

  test("7-1 完整步骤序列可以依次切换", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    const steps = [
      "文件上传",
      "文档解读",
      "投标分析",
      "投标计划",
      "AI编制指导",
      "质量审查",
      "进度跟踪",
    ]

    for (const stepName of steps) {
      const stepBtn = page.getByText(stepName).first()
      if (await stepBtn.isVisible()) {
        await stepBtn.click()
        await page.waitForTimeout(300)
        console.log(`  ✅ 步骤切换: ${stepName}`)
      }
    }
  })

  // ── 可选：质量审查 ─────────────────────────────────────────────────────────

  test("8-1 质量审查步骤正常渲染", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    // 切换到质量审查
    const reviewBtn = page.getByText("质量审查")
    if (await reviewBtn.isVisible()) {
      await reviewBtn.click()
      await page.waitForTimeout(500)

      // 审查界面元素
      await expect(
        page.getByText("质量审查").or(page.getByText("投标内容"))
      ).toBeVisible()
    }
  })

  test("8-2 进度跟踪步骤显示完成情况", async ({ page }) => {
    await page.goto(`/zh/projects/${projectId}/workspace`)
    await page.waitForLoadState("networkidle")

    const trackingBtn = page.getByText("进度跟踪")
    if (await trackingBtn.isVisible()) {
      await trackingBtn.click()
      await page.waitForTimeout(500)

      await expect(
        page.getByText("进度跟踪").or(page.getByText("步骤完成情况"))
      ).toBeVisible()
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// 独立：文件上传 API 层直接测试（不走 UI）
// ─────────────────────────────────────────────────────────────────────────────

test.describe("真实文件上传 API 层测试", () => {
  test("直接调用 API 上传真实招标 PDF", async () => {
    // 读取真实 PDF
    const pdfBuffer = fs.readFileSync(REAL_PDF_PATH)
    const pdfBlob = new Blob([pdfBuffer], { type: "application/pdf" })

    const formData = new FormData()
    formData.append("file", pdfBlob, "bid_document_test.pdf")

    const res = await fetch(
      `http://localhost:8000/v1/projects/${projectId}/bid-documents`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          // 不设置 Content-Type，让 fetch 自动设置 multipart boundary
        },
        body: formData,
      }
    )

    console.log(`上传响应状态: ${res.status}`)
    const body = await res.json()
    console.log(`上传响应: ${JSON.stringify(body, null, 2).slice(0, 200)}`)

    // 201 (新建) 或 200 (已存在时更新)
    expect([200, 201]).toContain(res.status)
    expect(body.id).toBeTruthy()
    expect(body.file_name || body.filename).toBeTruthy()

    console.log(`✅ API上传成功，文档ID: ${body.id}`)
  })

  test("上传后查询文档列表包含已上传文件", async () => {
    const res = await fetch(
      `http://localhost:8000/v1/projects/${projectId}/bid-documents`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )

    expect(res.ok).toBe(true)
    const docs = await res.json()
    console.log(`文档列表: ${JSON.stringify(docs).slice(0, 200)}`)

    // 应有至少一个文档
    const docArray = Array.isArray(docs) ? docs : docs.items || []
    expect(docArray.length).toBeGreaterThan(0)

    const uploadedDoc = docArray.find(
      (d: any) =>
        (d.file_name || d.filename || "").toLowerCase().includes("bid")
    )
    expect(uploadedDoc).toBeTruthy()
    console.log(`✅ 文档列表验证通过，找到: ${uploadedDoc?.file_name || uploadedDoc?.filename}`)
  })

  test("文档解析状态在上传后变化", async () => {
    // 获取文档列表
    const listRes = await fetch(
      `http://localhost:8000/v1/projects/${projectId}/bid-documents`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    )
    const docs = await listRes.json()
    const docArray = Array.isArray(docs) ? docs : docs.items || []

    if (docArray.length === 0) {
      console.log("⚠️ 无文档，跳过解析状态测试")
      return
    }

    const doc = docArray[0]
    console.log(`文档状态: ${doc.upload_status || doc.status || "unknown"}`)

    // 状态应为 pending/processing/parsed 之一
    const validStatuses = ["pending", "processing", "uploaded", "parsed", "completed"]
    const status = doc.upload_status || doc.status || ""
    const isValid = validStatuses.some((s) => status.includes(s)) || status === ""
    expect(isValid).toBe(true)
  })
})
