import React from "react";
import { RiskItem } from "../api/client";

interface Props {
  risks: RiskItem[];
}

const SEVERITY_CONFIG: Record<string, { classes: string; icon: string }> = {
  critical: { classes: "bg-red-100 border-red-300 text-red-900", icon: "🚨" },
  high: { classes: "bg-orange-50 border-orange-300 text-orange-900", icon: "⚠️" },
  medium: { classes: "bg-yellow-50 border-yellow-300 text-yellow-900", icon: "⚡" },
  low: { classes: "bg-green-50 border-green-300 text-green-900", icon: "ℹ️" },
};

export default function RiskPanel({ risks }: Props) {
  if (risks.length === 0)
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-400">
        No risks identified yet.
      </div>
    );

  const sorted = [...risks].sort((a, b) => {
    const order = ["critical", "high", "medium", "low"];
    return order.indexOf(a.severity) - order.indexOf(b.severity);
  });

  return (
    <div className="space-y-3">
      {sorted.map((risk) => {
        const cfg = SEVERITY_CONFIG[risk.severity] ?? {
          classes: "bg-gray-50 border-gray-300 text-gray-900",
          icon: "•",
        };
        return (
          <div
            key={risk.id}
            className={`rounded-lg border p-4 ${cfg.classes} ${risk.is_resolved ? "opacity-50" : ""}`}
          >
            <div className="flex items-start gap-2">
              <span>{cfg.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-sm">{risk.title}</h3>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-white bg-opacity-60 capitalize">
                    {risk.category}
                  </span>
                  {risk.is_resolved && (
                    <span className="text-xs text-green-600 font-medium">✓ Resolved</span>
                  )}
                </div>
                {risk.description && (
                  <p className="text-sm mt-1 opacity-90">{risk.description}</p>
                )}
                {risk.mitigation && (
                  <div className="mt-2 text-xs opacity-80">
                    <span className="font-medium">Mitigation:</span> {risk.mitigation}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
