import type { Plugin, Hooks, PluginOptions } from "@opencode-ai/plugin";
import type { TextPart } from "@opencode-ai/sdk";
import { MemoryClient } from "./client.js";
import { createMemoryAddTool } from "./tools/memory_add.js";
import { createMemorySearchTool } from "./tools/memory_search.js";
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

function getLastUserMessage(input: any): { content: string } | null {
  if (!input || !input.messages || !Array.isArray(input.messages)) {
    return null;
  }
  
  for (let i = input.messages.length - 1; i >= 0; i--) {
    const msg = input.messages[i];
    if (msg && msg.role === 'user') {
      const content = typeof msg.content === 'string' 
        ? msg.content 
        : extractTextFromParts(msg.content || []);
      return { content };
    }
  }
  
  return null;
}

function getLastUserMessageFromSession(messages: Array<{ info: any; parts: any[] }>): { content: string } | null {
  if (!messages || !Array.isArray(messages)) {
    return null;
  }
  
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg && msg.info && msg.info.role === 'user') {
      const content = extractTextFromParts(msg.parts || []);
      return { content };
    }
  }
  
  return null;
}

function convertSessionMessages(messages: Array<{ info: any; parts: any[] }>): Array<{ role: string; content: string }> {
  return messages.map(msg => ({
    role: msg.info?.role || 'unknown',
    content: extractTextFromParts(msg.parts || []),
  }));
}

interface ConversationMessage {
  role: string;
  content: string | any[];
}

interface PluginInput {
  sessionID?: string;
  messages?: ConversationMessage[];
  [key: string]: any;
}

function isQuestion(content: string): boolean {
  const questionPatterns = [
    /^(谁|什么|哪|怎么|如何|为什么|哪位|多少|几时|何时)/,
    /\?|？$/,
    /^(我是谁|你知道|还记得|告诉我|请问|能不能|可以|是否|有没有)/,
  ];
  
  return questionPatterns.some(pattern => pattern.test(content.trim()));
}

function isWorthRemembering(content: string): boolean {
  if (content.trim().length < 5) {
    return false;
  }
  
  if (isQuestion(content)) {
    return false;
  }
  
  const informativePatterns = [
    /(我叫|我的名字|我是|我喜欢|我偏好|我习惯|我想要|我希望)/,
    /(记住|记得|别忘了|记下来)/,
    /(邮箱|电话|地址|生日|职业|工作)/,
  ];
  
  return informativePatterns.some(pattern => pattern.test(content));
}

const plugin: Plugin = async (input, options?: Mem0PluginOptions) => {
  const configFile = loadConfigFile();

  const backendUrl = options?.backendUrl || process.env.MEM0_BACKEND_URL || configFile?.backendUrl || "http://localhost:8000";
  const apiKey = options?.apiKey || process.env.MEM0_API_KEY || configFile?.apiKey;
  const timeout = options?.timeout || configFile?.timeout || 30000;
  const autoSave = options?.autoSave ?? configFile?.autoSave ?? true;
  const userId = options?.userId || configFile?.userId || "default";
  const enableMemoryQuery = options?.enableMemoryQuery ?? configFile?.enableMemoryQuery ?? true;
  const memoryQueryLimit = options?.memoryQueryLimit || configFile?.memoryQueryLimit || 5;

  const memoryClient = new MemoryClient({
    baseUrl: backendUrl,
    apiKey,
    timeout,
  });

  const opencodeClient = input.client;

  const hooks: Hooks = {
    tool: {
      memory_add: createMemoryAddTool(memoryClient, userId),
      memory_search: createMemorySearchTool(memoryClient, userId),
    },
  };

  if (autoSave) {
    hooks["chat.message"] = async (input, output) => {
      console.log("[opencode-mem0] chat.message hook triggered");
      console.log("[opencode-mem0] sessionID:", input.sessionID);
      console.log("[opencode-mem0] agent:", input.agent);
      console.log("[opencode-mem0] parts count:", output.parts.length);

      const content = extractTextFromParts(output.parts);
      console.log("[opencode-mem0] extracted content:", content.substring(0, 100) + (content.length > 100 ? "..." : ""));

      if (!content.trim()) {
        console.log("[opencode-mem0] content is empty, skipping save");
        return;
      }

      if (!isWorthRemembering(content)) {
        console.log("[opencode-mem0] content not worth remembering (question or too short), skipping save");
        return;
      }

      console.log("[opencode-mem0] saving memory for user:", userId);
      const result = await memoryClient.addMemory({
        content,
        user_id: userId,
        metadata: {
          source: "chat",
          timestamp: new Date().toISOString(),
        },
      });
      console.log("[opencode-mem0] memory save result:", result.success ? "success" : "failed", result.error || "");
    };
  }

  // Intelligent memory query and injection into system prompt
  if (enableMemoryQuery) {
    hooks["experimental.chat.system.transform"] = async (input, output) => {
      console.log("[opencode-mem0] auto-loading memories for session");
      console.log("[opencode-mem0] sessionID:", input.sessionID);

      if (!input.sessionID) {
        console.log("[opencode-mem0] no sessionID, skipping");
        return;
      }

      try {
        const sessionMessages = await opencodeClient.session.messages({
          path: {
            id: input.sessionID,
          },
        });

        if (!sessionMessages.data || sessionMessages.data.length === 0) {
          console.log("[opencode-mem0] no messages in session, skipping");
          return;
        }

        const lastUserMessage = getLastUserMessageFromSession(sessionMessages.data);
        if (!lastUserMessage) {
          console.log("[opencode-mem0] no user message found, skipping");
          return;
        }

        console.log("[opencode-mem0] searching memories for:", lastUserMessage.content.substring(0, 50) + "...");

        const conversationHistory = convertSessionMessages(sessionMessages.data);

        const result = await memoryClient.getIntelligentMemories({
          user_input: lastUserMessage.content,
          user_id: userId,
          session_id: input.sessionID,
          conversation_history: conversationHistory,
          token_budget: memoryQueryLimit * 100,
        });

        if (result.success && result.context) {
          output.system.push(result.context);
          console.log(
            "[opencode-mem0] auto-injected memories -",
            `count: ${result.memories_count},`,
            `latency: ${result.latency_ms}ms,`,
            `cache_hit: ${result.cache_hit}`
          );
        } else {
          console.log("[opencode-mem0] no relevant memories found");
        }
      } catch (error) {
        console.error("[opencode-mem0] auto-load error:", error);
      }
    };
  }

  return hooks;
};

export default {
  id: "opencode-mem0",
  server: plugin,
};