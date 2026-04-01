"use client";

import { useCallback, useRef, useState } from "react";
import {
  EventStreamContentType,
  fetchEventSource,
} from "@microsoft/fetch-event-source";

import { API } from "@/lib/api";
import type { AgentOutput, AgentStep, ChatMessage, StepType } from "@/types";

interface UseAgentStreamReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  sendMessage: (content: string) => void;
  reset: () => void;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
}

let stepCounter = 0;
let messageCounter = 0;

export function useAgentStream(): UseAgentStreamReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState("gpt-4o");
  const abortRef = useRef<AbortController | null>(null);
  const stepsRef = useRef<AgentStep[]>([]);

  const addStep = useCallback(
    (type: StepType, content: string, extra?: Partial<AgentStep>) => {
      const incomingTaskId = extra?.taskId;
      // Mark previous active steps in same stream as complete
      stepsRef.current = stepsRef.current.map((s) => {
        if (s.status !== "active") return s;
        const sameStream =
          s.taskId === incomingTaskId ||
          (s.taskId == null && incomingTaskId == null);
        return sameStream ? { ...s, status: "complete" as const } : s;
      });

      const newStep: AgentStep = {
        id: ++stepCounter,
        type,
        status: "active" as const,
        content,
        ...extra,
      };
      stepsRef.current = [...stepsRef.current, newStep];

      // Update the assistant message with current steps
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.role === "assistant") {
          return [
            ...prev.slice(0, -1),
            { ...last, steps: [...stepsRef.current] },
          ];
        }
        return prev;
      });
    },
    [],
  );

  const sendMessage = useCallback(
    (content: string) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;

      // Add user message
      const userMsg: ChatMessage = {
        id: `msg-${++messageCounter}`,
        role: "user",
        content,
      };

      // Add placeholder assistant message
      stepsRef.current = [];
      const assistantMsg: ChatMessage = {
        id: `msg-${++messageCounter}`,
        role: "assistant",
        content: "",
        steps: [],
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setError(null);
      setIsStreaming(true);

      fetchEventSource(API.chatStream, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, model: selectedModel }),
        signal: ctrl.signal,

        async onopen(response) {
          if (
            response.ok &&
            response.headers
              .get("content-type")
              ?.includes(EventStreamContentType)
          ) {
            return;
          }
          throw new Error(`Unexpected response: ${response.status}`);
        },

        onmessage(event) {
          if (!event.data) return;
          const data = JSON.parse(event.data);
          const taskId = data.task_id as string | undefined;

          switch (event.event) {
            case "parse":
              addStep("parse", `Intent: ${data.intent ?? "unknown"}`, {
                output: JSON.stringify(data.entities ?? {}),
              });
              break;
            case "thought":
              addStep("thought", data.content, { taskId });
              break;
            case "action":
              addStep("action", `Calling ${data.tool}`, {
                tool: data.tool,
                input: data.input,
                taskId,
              });
              break;
            case "observation": {
              const isToolError =
                data.status === "error" ||
                data.output?.startsWith("Error invoking tool");
              addStep(
                "observation",
                isToolError
                  ? `${data.tool} failed`
                  : `${data.tool} returned`,
                {
                  tool: data.tool,
                  output: data.output,
                  isError: isToolError,
                  taskId,
                },
              );
              break;
            }
            case "agent_start":
              addStep("agent_start", data.label, {
                agentKey: data.agent,
                agentLabel: data.label,
                taskId: data.task_id,
              });
              break;
            case "step":
              addStep("step", `Step ${data.current}: ${data.description}`, {
                taskId,
              });
              break;
            case "response": {
              // Update assistant message with final content + structured output
              const output = data.output as AgentOutput | undefined;
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.role === "assistant") {
                  const completedSteps = stepsRef.current.map((s) => ({
                    ...s,
                    status: "complete" as const,
                  }));
                  return [
                    ...prev.slice(0, -1),
                    {
                      ...last,
                      content: data.content,
                      output,
                      steps: completedSteps,
                      isStreaming: false,
                    },
                  ];
                }
                return prev;
              });
              break;
            }
            case "usage":
              // Attach usage data to the last assistant message
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.role === "assistant") {
                  return [
                    ...prev.slice(0, -1),
                    { ...last, usage: data },
                  ];
                }
                return prev;
              });
              break;
            case "done":
              setIsStreaming(false);
              break;
            case "error":
              setError(data.message);
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.role === "assistant") {
                  return [
                    ...prev.slice(0, -1),
                    { ...last, error: data.message, isStreaming: false },
                  ];
                }
                return prev;
              });
              setIsStreaming(false);
              break;
          }
        },

        onclose() {
          // If we're still streaming when the connection closes,
          // it means the server died without sending done/response
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && last.isStreaming) {
              const errorSteps = stepsRef.current.map((s) =>
                s.status === "active"
                  ? { ...s, status: "error" as const }
                  : s,
              );
              return [
                ...prev.slice(0, -1),
                {
                  ...last,
                  content:
                    last.content ||
                    "The request failed unexpectedly. Please try again.",
                  steps: errorSteps,
                  isStreaming: false,
                  error: "Connection lost",
                },
              ];
            }
            return prev;
          });
          setIsStreaming(false);
        },

        onerror(err) {
          const message =
            err instanceof Error ? err.message : "Stream error";
          setError(message);
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && last.isStreaming) {
              const errorSteps = stepsRef.current.map((s) =>
                s.status === "active"
                  ? { ...s, status: "error" as const }
                  : s,
              );
              return [
                ...prev.slice(0, -1),
                {
                  ...last,
                  content:
                    last.content || "Something went wrong. Please try again.",
                  steps: errorSteps,
                  isStreaming: false,
                  error: message,
                },
              ];
            }
            return prev;
          });
          setIsStreaming(false);
          throw err;
        },
      });
    },
    [addStep, selectedModel],
  );

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    stepsRef.current = [];
    setIsStreaming(false);
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    reset,
    selectedModel,
    setSelectedModel,
  };
}
