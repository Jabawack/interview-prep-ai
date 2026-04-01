"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";

import { API } from "@/lib/api";
import type { ModelInfo } from "@/types";

interface ModelPickerProps {
  value: string;
  onChange: (model: string) => void;
  disabled: boolean;
}

export function ModelPicker({ value, onChange, disabled }: ModelPickerProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    fetch(API.chatModels)
      .then((r) => r.json())
      .then((data) => {
        if (data.models) setModels(data.models);
      })
      .catch(() => {
        // Fallback — show at least the default model
        setModels([{ id: "gpt-4o", input_cost_per_token: 0, output_cost_per_token: 0 }]);
      });
  }, []);

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || models.length === 0}
        className="appearance-none rounded-lg border border-zinc-200 bg-white py-2 pr-7 pl-2.5 text-xs font-medium text-zinc-600 outline-none focus:border-blue-400 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
      >
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.id}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-1.5 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
    </div>
  );
}
