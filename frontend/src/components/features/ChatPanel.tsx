"use client";

import { useEffect, useRef, useState } from "react";
import { UserButton } from "@clerk/nextjs";
import {
  AlertTriangle,
  Bot,
  Brain,
  Briefcase,
  Building2,
  ChevronDown,
  Eye,
  Footprints,
  Loader2,
  Search,
  Send,
  Sparkles,
  Wrench,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { AgentStep, ChatMessage, JobResult, StepType } from "@/types";
import { JobCards } from "./JobCards";
import { ModelPicker } from "./ModelPicker";
import { UsageReport } from "./UsageReport";

/* ------------------------------------------------------------------ */
/*  Config                                                             */
/* ------------------------------------------------------------------ */

const STEP_ICON: Record<StepType, React.ElementType> = {
  parse: Search,
  thought: Brain,
  action: Wrench,
  observation: Eye,
  agent_start: Search,
  step: Footprints,
  error: AlertTriangle,
};

const STEP_COLOR: Record<StepType, string> = {
  parse: "text-blue-500",
  thought: "text-purple-500",
  action: "text-amber-500",
  observation: "text-green-500",
  agent_start: "text-zinc-500",
  step: "text-indigo-500",
  error: "text-red-500",
};

const AGENT_CONFIG: Record<
  string,
  { icon: React.ElementType; pill: string; iconColor: string }
> = {
  job_search: {
    icon: Briefcase,
    pill: "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/30 dark:border-blue-800 dark:text-blue-400",
    iconColor: "text-blue-500 dark:text-blue-400",
  },
  company_research: {
    icon: Building2,
    pill: "bg-violet-50 border-violet-200 text-violet-700 dark:bg-violet-950/30 dark:border-violet-800 dark:text-violet-400",
    iconColor: "text-violet-500 dark:text-violet-400",
  },
};

/* ------------------------------------------------------------------ */
/*  Cycle + section grouping (reused from CommodityAI)                 */
/* ------------------------------------------------------------------ */

interface ActionPair {
  action: AgentStep;
  observation?: AgentStep;
}

interface ReActCycle {
  number: number;
  thought?: AgentStep;
  pairs: ActionPair[];
}

interface AgentSection {
  stepId: number;
  agentKey: string;
  agentLabel: string;
  taskId?: string;
  cycles: ReActCycle[];
}

interface ParallelGroup {
  sections: AgentSection[];
}

type SectionOrGroup =
  | { kind: "single"; section: AgentSection }
  | { kind: "parallel"; group: ParallelGroup };

interface GroupedSteps {
  preamble: AgentStep[];
  sequence: SectionOrGroup[];
}

function groupIntoCycles(steps: AgentStep[]): GroupedSteps {
  const preamble: AgentStep[] = [];
  const allSections: AgentSection[] = [];
  const taskIdMap = new Map<string, AgentSection>();
  let currentSection: AgentSection | null = null;
  let currentCycle: ReActCycle | null = null;

  for (const step of steps) {
    if (step.type === "parse") {
      if (!currentSection) preamble.push(step);
      continue;
    }
    if (step.type === "error") {
      if (!currentSection) preamble.push(step);
      continue;
    }
    if (step.type === "step") continue;

    if (step.type === "agent_start") {
      currentSection = {
        stepId: step.id,
        agentKey: step.agentKey ?? "",
        agentLabel: step.agentLabel ?? step.content,
        taskId: step.taskId,
        cycles: [],
      };
      currentCycle = null;
      allSections.push(currentSection);
      if (step.taskId) taskIdMap.set(step.taskId, currentSection);
      continue;
    }

    let targetSection: AgentSection | null = currentSection;
    if (step.taskId && taskIdMap.has(step.taskId)) {
      targetSection = taskIdMap.get(step.taskId)!;
    }
    if (!targetSection) {
      targetSection = {
        stepId: step.id,
        agentKey: "",
        agentLabel: "Agent",
        cycles: [],
      };
      allSections.push(targetSection);
      currentSection = targetSection;
    }

    let sectionCycle: ReActCycle | null =
      targetSection === currentSection
        ? currentCycle
        : targetSection.cycles[targetSection.cycles.length - 1] ?? null;

    if (step.type === "thought") {
      sectionCycle = {
        number: targetSection.cycles.length + 1,
        thought: step,
        pairs: [],
      };
      targetSection.cycles.push(sectionCycle);
      if (targetSection === currentSection) currentCycle = sectionCycle;
      continue;
    }

    if (step.type === "action") {
      if (
        !sectionCycle ||
        sectionCycle.pairs.some((p: ActionPair) => p.observation)
      ) {
        sectionCycle = {
          number: targetSection.cycles.length + 1,
          pairs: [],
        };
        targetSection.cycles.push(sectionCycle);
        if (targetSection === currentSection) currentCycle = sectionCycle;
      }
      sectionCycle.pairs.push({ action: step });
      continue;
    }

    if (step.type === "observation" && sectionCycle) {
      const match = sectionCycle.pairs.find(
        (p: ActionPair) => p.action.tool === step.tool && !p.observation,
      );
      if (match) {
        match.observation = step;
      } else {
        sectionCycle.pairs.push({ action: step });
      }
    }
  }

  // Group consecutive taskId sections into parallel groups
  const sequence: SectionOrGroup[] = [];
  let i = 0;
  while (i < allSections.length) {
    const section = allSections[i]!;
    if (section.taskId) {
      const parallelSections: AgentSection[] = [section];
      while (i + 1 < allSections.length && allSections[i + 1]!.taskId) {
        i++;
        parallelSections.push(allSections[i]!);
      }
      if (parallelSections.length >= 2) {
        sequence.push({
          kind: "parallel",
          group: { sections: parallelSections },
        });
      } else {
        sequence.push({ kind: "single", section });
      }
    } else {
      sequence.push({ kind: "single", section });
    }
    i++;
  }

  return { preamble, sequence };
}

/* ------------------------------------------------------------------ */
/*  Main ChatPanel                                                     */
/* ------------------------------------------------------------------ */

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSendMessage: (content: string) => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
}

export function ChatPanel({
  messages,
  isStreaming,
  onSendMessage,
  selectedModel,
  onModelChange,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-zinc-200 p-3 dark:border-zinc-800">
        <h2 className="text-sm font-semibold">Interview Prep Chat</h2>
        <div className="flex items-center gap-3">
          {isStreaming && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
          <UserButton />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="mt-12 text-center">
            <Bot className="mx-auto h-10 w-10 text-zinc-300 dark:text-zinc-600" />
            <p className="mt-3 text-sm text-zinc-500">
              Ask me to find jobs, research companies, or help you prepare for
              interviews.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                "Find React jobs in Remote",
                "Tell me about Google's interview process",
                "Find React jobs at Google and tell me about their interview process",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => onSendMessage(suggestion)}
                  className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs text-zinc-600 transition-colors hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 dark:border-zinc-700 dark:text-zinc-400 dark:hover:border-blue-800 dark:hover:bg-blue-950/30 dark:hover:text-blue-400"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) =>
          msg.role === "user" ? (
            <UserBubble key={msg.id} content={msg.content} />
          ) : (
            <AssistantMessage key={msg.id} message={msg} />
          ),
        )}
        <div ref={bottomRef} />
      </div>

      <InputBar
        disabled={isStreaming}
        onSend={onSendMessage}
        selectedModel={selectedModel}
        onModelChange={onModelChange}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Message components                                                 */
/* ------------------------------------------------------------------ */

function UserBubble({ content }: { content: string }) {
  return (
    <div className="mb-4 flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-br-md bg-blue-600 px-4 py-2.5 text-sm text-white">
        {content}
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  const steps = message.steps ?? [];
  const hasSteps = steps.length > 0;
  const { preamble, sequence } = groupIntoCycles(steps);

  // Extract structured jobs if available
  const jobs: JobResult[] = message.output?.results?.jobs ?? [];

  // Strip the "Found N job(s):" listing from the text when rendering cards
  let contentWithoutJobs = "";
  let followUp = "";
  if (jobs.length > 0 && message.content) {
    const parts = message.content.split(/\*\*What would you like to do next\?\*\*/);
    const before = parts[0] ?? "";
    followUp = parts[1] ? `**What would you like to do next?**${parts[1]}` : "";
    // Remove the job listing block (lines starting with "**Found" through numbered items)
    contentWithoutJobs = before
      .replace(/\*\*Found \d+ job\(s\):\*\*[\s\S]*?(?=\n\n|$)/, "")
      .trim();
  }

  return (
    <div className="mb-4">
      <div className="flex gap-2">
        <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800">
          <Bot className="h-4 w-4 text-zinc-500" />
        </div>
        <div className="min-w-0 flex-1">
          {/* Agent activity log */}
          {hasSteps && (
            <AgentActivityLog
              preamble={preamble}
              sequence={sequence}
              isStreaming={message.isStreaming ?? false}
            />
          )}

          {/* Final response content */}
          {message.content && (
            <div className="mt-2 rounded-2xl rounded-tl-md bg-zinc-100 px-4 py-2.5 text-sm dark:bg-zinc-800">
              {jobs.length > 0 ? (
                <div className="space-y-3">
                  {contentWithoutJobs && (
                    <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                      {contentWithoutJobs}
                    </div>
                  )}
                  <JobCards jobs={jobs} />
                  {followUp && (
                    <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                      {followUp}
                    </div>
                  )}
                </div>
              ) : (
                <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                  {message.content}
                </div>
              )}
            </div>
          )}

          {/* Usage report */}
          {message.usage && !message.isStreaming && (
            <UsageReport usage={message.usage} />
          )}

          {/* Error */}
          {message.error && (
            <div className="mt-2 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950/30">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
              <p className="text-sm text-red-700 dark:text-red-400">
                {message.error}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Agent Activity Log                                                 */
/* ------------------------------------------------------------------ */

function AgentActivityLog({
  preamble,
  sequence,
  isStreaming,
}: {
  preamble: AgentStep[];
  sequence: SectionOrGroup[];
  isStreaming: boolean;
}) {
  const [open, setOpen] = useState(true);
  const allSections = sequence.flatMap((item) =>
    item.kind === "single" ? [item.section] : item.group.sections,
  );
  const hasParallel = sequence.some((item) => item.kind === "parallel");
  const agentChain = allSections
    .map((s) => s.agentLabel)
    .join(hasParallel ? " + " : " → ");

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 p-2 text-left"
      >
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-zinc-400 transition-transform",
            !open && "-rotate-90",
          )}
        />
        <span className="text-xs font-medium text-zinc-500">
          {agentChain || "Processing..."}
        </span>
        {isStreaming && (
          <Loader2 className="ml-auto h-3 w-3 animate-spin text-blue-500" />
        )}
      </button>

      {open && (
        <div className="border-t border-zinc-100 px-2 pb-2 dark:border-zinc-800">
          {preamble.map((step) => (
            <StepRow key={step.id} step={step} />
          ))}

          {sequence.map((item) =>
            item.kind === "single" ? (
              <AgentSectionBlock
                key={item.section.stepId}
                section={item.section}
              />
            ) : (
              <ParallelAgentGroup
                key={item.group.sections[0]!.stepId}
                group={item.group}
              />
            ),
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Agent section blocks                                               */
/* ------------------------------------------------------------------ */

function ParallelAgentGroup({ group }: { group: ParallelGroup }) {
  return (
    <div className="mt-2">
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
          <Sparkles className="h-3 w-3" />
          Parallel
        </span>
        <div className="h-px flex-1 bg-amber-200 dark:bg-amber-800" />
      </div>

      <div
        className="mt-2 grid gap-2"
        style={{
          gridTemplateColumns: `repeat(${Math.min(group.sections.length, 3)}, minmax(0, 1fr))`,
        }}
      >
        {group.sections.map((section) => (
          <div
            key={section.stepId}
            className={cn(
              "rounded-lg border-l-4 bg-zinc-50/50 p-2 dark:bg-zinc-900/50",
              AGENT_CONFIG[section.agentKey]
                ? "border-l-violet-400 dark:border-l-violet-600"
                : "border-l-zinc-300 dark:border-l-zinc-600",
            )}
          >
            <AgentSectionBlock section={section} compact />
          </div>
        ))}
      </div>
    </div>
  );
}

function AgentSectionBlock({
  section,
  compact,
}: {
  section: AgentSection;
  compact?: boolean;
}) {
  const cfg = AGENT_CONFIG[section.agentKey];
  const Icon = cfg?.icon ?? Search;

  return (
    <div className={compact ? "mt-1" : "mt-2"}>
      <div className="flex items-center gap-2">
        <div
          className={cn(
            "flex items-center gap-1.5 rounded-full border py-0.5 text-xs font-semibold",
            compact ? "px-2" : "px-2.5",
            cfg?.pill ??
              "border-zinc-200 bg-zinc-50 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
          )}
        >
          <Icon
            className={cn("h-3 w-3", cfg?.iconColor ?? "text-zinc-400")}
          />
          {section.agentLabel}
        </div>
        {!compact && (
          <div className="h-px flex-1 bg-zinc-200 dark:bg-zinc-700" />
        )}
      </div>

      <div className={compact ? "ml-1" : "ml-2"}>
        {section.cycles.map((cycle) => (
          <CycleBlock key={cycle.number} cycle={cycle} />
        ))}
        {section.cycles.length === 0 && (
          <p className="mt-1 text-xs italic text-zinc-400">Running...</p>
        )}
      </div>
    </div>
  );
}

function CycleBlock({ cycle }: { cycle: ReActCycle }) {
  return (
    <div className="mt-2 rounded border border-zinc-100 bg-zinc-50/50 p-2 dark:border-zinc-800 dark:bg-zinc-900/50">
      <div className="mb-1 text-xs font-semibold text-zinc-400">
        Cycle {cycle.number}
      </div>

      {cycle.thought && <StepRow step={cycle.thought} />}

      {cycle.pairs.map((pair, i) => (
        <div
          key={pair.action.id ?? i}
          className={cn(
            "ml-4 border-l-2 pl-3",
            pair.observation?.isError
              ? "border-red-400 dark:border-red-700"
              : "border-zinc-200 dark:border-zinc-700",
          )}
        >
          <StepRow step={pair.action} />
          {pair.observation && <StepRow step={pair.observation} nested />}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step row                                                           */
/* ------------------------------------------------------------------ */

function formatDetail(
  output: string | undefined,
  input: Record<string, unknown> | undefined,
): string {
  if (input) return JSON.stringify(input, null, 2);
  if (!output) return "";
  try {
    return JSON.stringify(JSON.parse(output), null, 2);
  } catch {
    return output;
  }
}

function StepRow({
  step,
  nested,
}: {
  step: AgentStep;
  nested?: boolean;
}) {
  const [expanded, setExpanded] = useState(!!step.isError);
  const isErr = step.isError;
  const Icon = isErr ? AlertTriangle : STEP_ICON[step.type];
  const color = isErr ? "text-red-500" : STEP_COLOR[step.type];
  const hasDetail = step.output ?? step.input;

  return (
    <div
      className={cn(
        "mt-1",
        nested && "mt-0.5",
        isErr && "rounded bg-red-50 px-2 py-1 dark:bg-red-950/40",
      )}
    >
      <button
        onClick={() => hasDetail && setExpanded(!expanded)}
        className={cn(
          "flex w-full items-start gap-2 rounded-md px-1 py-0.5 text-left transition-colors",
          hasDetail &&
            "cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800",
        )}
      >
        {step.status === "active" ? (
          <Loader2
            className={cn("mt-0.5 h-4 w-4 shrink-0 animate-spin", color)}
          />
        ) : (
          <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", color)} />
        )}
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              "text-sm",
              nested && !isErr && "text-xs text-zinc-600 dark:text-zinc-400",
              isErr && "font-medium text-red-700 dark:text-red-400",
            )}
          >
            {step.content}
          </p>
        </div>
        {hasDetail && (
          <ChevronDown
            className={cn(
              "mt-1 h-3 w-3 shrink-0 transition-transform",
              isErr ? "text-red-400" : "text-zinc-400",
              !expanded && "-rotate-90",
            )}
          />
        )}
      </button>
      {expanded && hasDetail && (
        <pre
          className={cn(
            "mt-1 ml-6 max-h-40 overflow-auto rounded p-2 font-mono text-xs whitespace-pre-wrap break-words",
            isErr
              ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
              : "bg-zinc-100 dark:bg-zinc-900",
          )}
        >
          {formatDetail(step.output, step.input)}
        </pre>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Input bar                                                          */
/* ------------------------------------------------------------------ */

function InputBar({
  disabled,
  onSend,
  selectedModel,
  onModelChange,
}: {
  disabled: boolean;
  onSend: (msg: string) => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
}) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 border-t border-zinc-200 p-3 dark:border-zinc-800"
    >
      <ModelPicker
        value={selectedModel}
        onChange={onModelChange}
        disabled={disabled}
      />
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Search for jobs, ask about companies, or prep for interviews..."
        className="flex-1 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-400 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-lg bg-blue-600 p-2 text-white hover:bg-blue-700 disabled:opacity-50"
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}
