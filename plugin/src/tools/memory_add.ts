import { tool, type ToolContext } from "@opencode-ai/plugin";
import { z } from "zod";
import type { MemoryClient } from "../client.js";

export function createMemoryAddTool(client: MemoryClient, defaultUserId?: string) {
  return tool({
    description: "Add a memory to the mem0 storage",
    args: {
      content: z.string().describe("The content to remember"),
      user_id: z.string().optional().describe("User ID for the memory"),
      metadata: z.record(z.string(), z.any()).optional().describe("Optional metadata for the memory"),
    },
    async execute(args: { content: string; user_id?: string; metadata?: Record<string, any> }, context: ToolContext) {
      const result = await client.addMemory({
        content: args.content,
        user_id: args.user_id || defaultUserId,
        metadata: args.metadata,
      });

      if (!result.success) {
        return `Failed to add memory: ${result.error}`;
      }

      return `Memory added successfully with ID: ${result.memory_id}`;
    },
  });
}