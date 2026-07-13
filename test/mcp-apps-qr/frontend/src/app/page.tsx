"use client";

import { CopilotSidebar } from "@copilotkit/react-core/v2";

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">CopilotKit + MCP Apps</p>
        <h1>MCP Apps Demo</h1>
        <p className="lede">
          Agent 调用带 <code>ui/resourceUri</code> 的工具后，聊天里会渲染 MCP App iframe。
          含二维码，以及表单确认（对标 CopilotKit showcase 预订向导）。
        </p>
        <ul className="hints">
          <li>帮我生成 https://docs.agno.com 的二维码</li>
          <li>打开设备借用表单，预填姓名 Alice</li>
          <li>我想申请一台显示器，用表单提交</li>
        </ul>
      </section>
      <CopilotSidebar
        defaultOpen
        labels={{
          modalHeaderTitle: "MCP Apps Assistant",
          welcomeMessageText: "试试：打开设备借用表单，或生成 agno.com 二维码",
          chatInputPlaceholder: "二维码 / 表单确认...",
          chatDisclaimerText: "UI 由 MCP Apps Server 提供；表单确认经 Host 代理 tools/call。",
        }}
      />
    </main>
  );
}
