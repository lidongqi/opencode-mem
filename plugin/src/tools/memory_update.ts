import { tool, type ToolContext } from "@opencode-ai/plugin";
import { z } from "zod";
import type { MemoryClient } from "../client.js";

export function createMemoryUpdateTool(client: MemoryClient) {
  return tool({
    description: "Update a specific memory by ID",
    args: {
      memory_id: z.string().describe("ID of the memory to update"),
      content: z.string().describe("New content for the memory"),
    },
    async execute(args: { memory_id: string; content: string }, context: ToolContext) {
      const result = await client.updateMemory({
        memory_id: args.memory_id,
        content: args.content,
      });

      if (!result.success) {
        return `Failed to update memory: ${result.error}`;
      }

      return `Memory ${args.memory_id} updated successfully.`;
    },
  });
}