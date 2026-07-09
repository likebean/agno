"use client";

import { useAgentContext } from "@copilotkit/react-core/v2";
import { useMemo, useState } from "react";

/**
 * Pushes a mock flag into every agent run via AG-UI context.
 * Agno maps context → dependencies; tools read run_context.dependencies["mock"].
 */
export function MockContextToggle() {
  const [mock, setMock] = useState(false);
  const value = useMemo(() => mock, [mock]);

  useAgentContext({ description: "mock", value });

  return (
    <label className="mock-toggle">
      <input
        type="checkbox"
        checked={mock}
        onChange={(event) => setMock(event.target.checked)}
      />
      <span>Mock</span>
    </label>
  );
}
