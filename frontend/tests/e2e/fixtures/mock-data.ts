/**
 * 测试固定 Mock 数据
 * 供各 spec 文件复用，保证数据一致性
 */

export const MOCK_OPPORTUNITY = {
  id: "opp_test_001",
  title: "E2E测试-水利工程技术咨询服务",
  source: "adb",
  institution: "ADB",
  country: "CN",
  country_name: "中国",
  sector: "水利",
  status: "open",
  deadline: "2026-06-30T23:59:59Z",
  published_at: "2026-01-01T00:00:00Z",
  budget: 500000,
  currency: "USD",
  description: "亚洲开发银行水利工程技术咨询服务采购项目，用于E2E测试。",
  url: "https://adb.org/test-opp",
  reference_number: "ADB-2026-TEST-001",
}

export const MOCK_OPPORTUNITY_LIST = {
  items: [
    MOCK_OPPORTUNITY,
    {
      id: "opp_test_002",
      title: "E2E测试-世界银行教育项目评估",
      source: "wb",
      institution: "WB",
      country: "IN",
      country_name: "印度",
      sector: "教育",
      status: "open",
      deadline: "2026-07-15T23:59:59Z",
      published_at: "2026-01-10T00:00:00Z",
      budget: 300000,
      currency: "USD",
      description: "世界银行教育项目评估咨询服务，用于E2E测试。",
      url: "https://wb.org/test-opp",
      reference_number: "WB-2026-TEST-002",
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1,
}

export const MOCK_PROJECT = {
  id: "proj_test_001",
  name: "E2E测试-水利咨询项目",
  description: "E2E自动化测试用项目",
  opportunity_id: "opp_test_001",
  institution: "adb",
  status: "active",
  current_step: "upload",
  created_at: "2026-01-15T00:00:00Z",
  updated_at: "2026-02-01T00:00:00Z",
}

export const MOCK_PROJECT_LIST = {
  items: [MOCK_PROJECT],
  total: 1,
  page: 1,
  page_size: 20,
  pages: 1,
}

export const MOCK_BID_DOCUMENT = {
  id: "doc_test_001",
  project_id: "proj_test_001",
  filename: "test_rfp.pdf",
  file_size: 1024,
  status: "parsed",
  created_at: "2026-01-16T00:00:00Z",
  sections: [
    { title: "项目背景", page_start: 1, page_end: 5 },
    { title: "服务范围", page_start: 6, page_end: 15 },
    { title: "资质要求", page_start: 16, page_end: 20 },
  ],
}

export const MOCK_ANALYSIS = {
  id: "analysis_test_001",
  project_id: "proj_test_001",
  status: "completed",
  qualification: {
    score: 85,
    summary: "需要具备10年以上水利工程咨询经验",
    requirements: ["注册工程师资质", "同类项目业绩", "财务实力证明"],
  },
  scoring_criteria: {
    technical_weight: 70,
    financial_weight: 30,
    evaluation_method: "QCBS",
  },
  key_dates: {
    clarification_deadline: "2026-05-01",
    submission_deadline: "2026-06-30",
    opening_date: "2026-07-05",
  },
  risks: ["汇率风险", "环境许可延迟", "当地配合不足"],
}

export const MOCK_BID_PLAN = {
  id: "plan_test_001",
  project_id: "proj_test_001",
  tasks: [
    {
      id: "task_001",
      title: "准备公司资质文件",
      priority: "high",
      due_date: "2026-04-01",
      assignee: "测试负责人",
      status: "pending",
    },
    {
      id: "task_002",
      title: "编写技术方案",
      priority: "high",
      due_date: "2026-05-15",
      assignee: "技术组",
      status: "in_progress",
    },
    {
      id: "task_003",
      title: "财务报表准备",
      priority: "medium",
      due_date: "2026-06-01",
      assignee: "财务组",
      status: "pending",
    },
  ],
}

export const MOCK_CREDITS_TRANSACTIONS = {
  items: [
    {
      id: "tx_001",
      type: "consume",
      amount: -50,
      description: "AI分析 - 水利咨询项目",
      created_at: "2026-02-01T10:00:00Z",
    },
    {
      id: "tx_002",
      type: "recharge",
      amount: 500,
      description: "充值 - 标准套餐",
      created_at: "2026-01-15T09:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1,
}

export const MOCK_PAYMENT_PACKAGES = [
  { id: "pkg_100", credits: 100, price: 99, currency: "CNY", label: "基础版" },
  { id: "pkg_500", credits: 500, price: 399, currency: "CNY", label: "标准版" },
  {
    id: "pkg_1000",
    credits: 1000,
    price: 699,
    currency: "CNY",
    label: "专业版",
    is_popular: true,
  },
]

export const MOCK_KNOWLEDGE_BASE_LIST = {
  items: [
    {
      id: "kb_001",
      title: "ADB采购准则2024版",
      institution: "adb",
      category: "procurement_guidelines",
      description: "亚洲开发银行最新采购政策和程序",
    },
    {
      id: "kb_002",
      title: "WB咨询服务选择方法",
      institution: "wb",
      category: "consultant_selection",
      description: "世界银行咨询服务选择和雇用方法",
    },
  ],
  total: 2,
  page: 1,
  pages: 1,
}
