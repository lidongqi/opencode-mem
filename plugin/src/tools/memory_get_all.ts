import { tool, type ToolContext } from "@opencode-ai/plugin";
import { z } from "zod";
import type { MemoryClient } from "../client.js";

export function createMemoryGetAllTool(client: MemoryClient) {
  return tool({
    description: "Get all memories for a user",
    args: {
      user_id: z.string().optional().describe("User ID to get memories for"),
    },
    async execute(args: { user_id?: string }, context: ToolContext) {
      const result = await client.getAllMemories(args.user_id);

      if (!result.success) {
        return `Failed to get memories: ${result.error}`;
      }

      if (result.count === 0) {
        return "No memories found.";
      }

      const memories = result.memories
        .map((mem: { id: string; content: string }, i: number) => `${i + 1}. [${mem.id.substring(0, 8)}] ${mem.content}`)
        .join('\n');

      return `Total ${result.count} memories:\n${memories}`;
    },
  });
}