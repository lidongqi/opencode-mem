import { tool, type ToolContext } from "@opencode-ai/plugin";
import { z } from "zod";
import type { MemoryClient } from "../client.js";

export function createMemoryDeleteTool(client: MemoryClient) {
  return tool({
    description: "Delete a specific memory by ID",
    args: {
      memory_id: z.string().describe("ID of the memory to delete"),
    },
    async execute(args: { memory_id: string }, context: ToolContext) {
      const result = await client.deleteMemory(args.memory_id);

      if (!result.success) {
        return `Failed to delete memory: ${result.error}`;
      }

      return `Memory ${args.memory_id} deleted successfully.`;
    },
  });
}