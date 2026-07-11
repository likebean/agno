"use client";

import { CopilotSidebar } from "@copilotkit/react-core/v2";

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">CopilotKit + MCP Apps</p>
        <h1>二维码生成 Demo</h1>
        <p className="lede">
          Agent 调用 MCP Server 的 <code>generate_qr</code> 工具后，聊天里会自动渲染交互式二维码 UI，前端无需手写渲染组件。
        </p>
        <ul className="hints">
          <li>帮我生成 https://docs.agno.com 的二维码</li>
          <li>生成一个深色风格的 Hello World 二维码</li>
          <li>做一个 WiFi 二维码：网络 MyWifi，密码 secret123</li>
        </ul>
      </section>
      <CopilotSidebar
        defaultOpen
        labels={{
          modalHeaderTitle: "QR Assistant",
          welcomeMessageText: "试试说：帮我生成 agno.com 的二维码",
          chatInputPlaceholder: "输入要编码的文字或 URL...",
          chatDisclaimerText: "二维码 UI 由 MCP Apps Server 提供，聊天内自动渲染。",
        }}
      />
    </main>
  );
}
