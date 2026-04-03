import type { Plugin, Hooks, PluginOptions } from "@opencode-ai/plugin";
import type { TextPart } from "@opencode-ai/sdk";
import { MemoryClient } from "./client.js";
import { createMemoryAddTool } from "./tools/memory_add.js";
import { createMemorySearchTool } from "./tools/memory_search.js";
import { createMemoryGetAllTool } from "./tools/memory_get_all.js";
import { createMemoryUpdateTool } from "./tools/memory_update.js";
import { createMemoryDeleteTool } from "./tools/memory_delete.js";
import { createMemoryHistoryTool } from "./tools/memory_history.js";
import { readFileSync } from "fs";
import { join } from "path";
import { homedir } from "os";

export interface Mem0PluginOptions extends PluginOptions {
  backendUrl?: string;
  apiKey?: string;
  timeout?: number;
  autoSave?: boolean;
  userId?: string;
  enableMemoryQuery?: boolean;
  memoryQueryLimit?: number;
}

interface ConfigFile {
  backendUrl?: string;
  apiKey?: string;
  timeout?: number;
  autoSave?: boolean;
  userId?: string;
  enableMemoryQuery?: boolean;
  memoryQueryLimit?: number;
}

function loadConfigFile(): ConfigFile | null {
  try {
    const configPath = join(homedir(), ".config", "opencode", ".opencode-mem0.json");
    const content = readFileSync(configPath, "utf-8");
    return JSON.parse(content) as ConfigFile;
  } catch {
    return null;
  }
}

function extractTextFromParts(parts: unknown[]): string {
  return parts
    .filter((part): part is TextPart => {
      const p = part as { type?: string; text?: string };
      return p.type === "text" && typeof p.text === "string";
    })
    .map(part => part.text)
    .join("\n");
}

const plugin: Plugin = async (input: unknown, options?: Mem0PluginOptions) => {
  const configFile = loadConfigFile();

  const backendUrl = options?.backendUrl || process.env.MEM0_BACKEND_URL || configFile?.backendUrl || "http://localhost:8000";
  const apiKey = options?.apiKey || process.env.MEM0_API_KEY || configFile?.apiKey;
  const timeout = options?.timeout || configFile?.timeout || 30000;
  const autoSave = options?.autoSave ?? configFile?.autoSave ?? true;
  const userId = options?.userId || configFile?.userId || "default";
  const enableMemoryQuery = options?.enableMemoryQuery ?? configFile?.enableMemoryQuery ?? true;
  const memoryQueryLimit = options?.memoryQueryLimit || configFile?.memoryQueryLimit || 5;

  const client = new MemoryClient({
    baseUrl: backendUrl,
    apiKey,
    timeout,
  });

  const hooks: Hooks = {
    tool: {
      memory_add: createMemoryAddTool(client),
      memory_search: createMemorySearchTool(client),
      memory_get_all: createMemoryGetAllTool(client),
      memory_update: createMemoryUpdateTool(client),
      memory_delete: createMemoryDeleteTool(client),
      memory_history: createMemoryHistoryTool(client),
    },
  };

  // Auto-save user messages to memory
  if (autoSave) {
    hooks["chat.message"] = async (input, output) => {
      console.log("[opencode-mem0] chat.message hook triggered");
      console.log("[opencode-mem0] sessionID:", input.sessionID);
      console.log("[opencode-mem0] agent:", input.agent);
      console.log("[opencode-mem0] parts count:", output.parts.length);

      const content = extractTextFromParts(output.parts);
      console.log("[opencode-mem0] extracted content:", content.substring(0, 100) + (content.length > 100 ? "..." : ""));

      if (content.trim()) {
        console.log("[opencode-mem0] saving memory for user:", userId);
        const result = await client.addMemory({
          content,
          user_id: userId,
          metadata: {
            source: "chat",
            timestamp: new Date().toISOString(),
          },
        });
        console.log("[opencode-mem0] memory save result:", result.success ? "success" : "failed", result.error || "");
      } else {
        console.log("[opencode-mem0] content is empty, skipping save");
      }
    };
  }

  // Query relevant memories and inject into system prompt
  if (enableMemoryQuery) {
    hooks["experimental.chat.system.transform"] = async (input, output) => {
      console.log("[opencode-mem0] system.transform hook triggered");
      console.log("[opencode-mem0] sessionID:", input.sessionID);

      // Get the last user message from the session to search relevant memories
      // Since we don't have direct access to messages here, we'll add a general context
      const result = await client.getAllMemories(userId);

      if (result.success && result.memories && result.memories.length > 0) {
        console.log("[opencode-mem0] found", result.memories.length, "memories");

        // Format memories for system prompt
        const memoryContext = result.memories
          .slice(0, memoryQueryLimit)
          .map((m: { content: string; created_at?: string }) => `- ${m.content}${m.created_at ? ` (${m.created_at})` : ""}`)
          .join("\n");

        const memoryPrompt = `## Relevant Context from Previous Conversations

The following information was remembered from previous conversations:

${memoryContext}

Use this context to provide more relevant and personalized responses when appropriate.`;

        output.system.push(memoryPrompt);
        console.log("[opencode-mem0] injected", result.memories.slice(0, memoryQueryLimit).length, "memories into system prompt");
      } else {
        console.log("[opencode-mem0] no memories found");
      }
    };
  }

  return hooks;
};

export default {
  id: "opencode-mem0",
  server: plugin,
};