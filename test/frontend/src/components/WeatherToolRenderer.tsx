"use client";

import { useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { COPILOT_AGENT_ID } from "@/lib/config";

const weatherSchema = z.object({
  location: z.string().describe("City or location name"),
});

type WeatherResult = {
  city: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  conditions: string;
};

function parseWeatherResult(result: string | undefined): WeatherResult | null {
  if (!result) return null;
  try {
    return JSON.parse(result) as WeatherResult;
  } catch {
    // Agno may serialize dict results as Python repr with single quotes
    try {
      const jsonish = result
        .replace(/'/g, '"')
        .replace(/\bNone\b/g, "null")
        .replace(/\bTrue\b/g, "true")
        .replace(/\bFalse\b/g, "false");
      return JSON.parse(jsonish) as WeatherResult;
    } catch {
      return null;
    }
  }
}

function WeatherCard({ data }: { data: WeatherResult }) {
  return (
    <div className="weather-card">
      <div className="weather-card-city">{data.city}</div>
      <div className="weather-card-temp">{data.temperature}°C</div>
      <div className="muted">{data.conditions}</div>
      <div className="weather-card-meta">
        <span>湿度 {data.humidity}%</span>
        <span>风速 {data.wind_speed} km/h</span>
      </div>
    </div>
  );
}

/**
 * Tool Rendering for backend get_weather.
 * @see https://docs.copilotkit.ai/agno/generative-ui/tool-rendering
 */
export function WeatherToolRenderer() {
  useRenderTool({
    name: "get_weather",
    agentId: COPILOT_AGENT_ID,
    parameters: weatherSchema,
    render: ({ status, parameters, result }) => {
      const weather = parseWeatherResult(result);

      if (status !== "complete") {
        return (
          <p className="muted">
            正在查询 {parameters.location ?? "..."} 的天气...
          </p>
        );
      }

      if (weather) {
        return <WeatherCard data={weather} />;
      }

      return (
        <p className="muted">
          已查询 {parameters.location} 的天气
          {result ? `: ${result}` : ""}
        </p>
      );
    },
  });

  return null;
}
