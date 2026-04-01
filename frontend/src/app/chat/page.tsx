"use client";

import { ChatPanel } from "@/components/features/ChatPanel";
import { useAgentStream } from "@/hooks/useAgentStream";

export default function ChatPage() {
  const { messages, isStreaming, sendMessage, selectedModel, setSelectedModel } =
    useAgentStream();

  return (
    <ChatPanel
      messages={messages}
      isStreaming={isStreaming}
      onSendMessage={sendMessage}
      selectedModel={selectedModel}
      onModelChange={setSelectedModel}
    />
  );
}
