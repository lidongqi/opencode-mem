import { tool, type ToolContext } from "@opencode-ai/plugin";
import { z } from "zod";
import type { MemoryClient } from "../client.js";

export function createMemorySearchTool(client: MemoryClient) {
  return tool({
    description: "Search for relevant memories",
    args: {
      query: z.string().describe("Search query"),
      user_id: z.string().optional().describe("User ID to search memories for"),
      limit: z.number().optional().describe("Maximum number of results"),
    },
    async execute(args: { query: string; user_id?: string; limit?: number }, context: ToolContext) {
      const result = await client.searchMemories({
        query: args.query,
        user_id: args.user_id,
        limit: args.limit,
      });

      if (!result.success) {
        return `Failed to search memories: ${result.error}`;
      }

      if (result.count === 0) {
        return "No memories found matching your query.";
      }

      const memories = result.memories
        .map((mem: { content: string; score?: number }, i: number) => `${i + 1}. ${mem.content}${mem.score ? ` (relevance: ${mem.score.toFixed(2)})` : ''}`)
        .join('\n');

      return `Found ${result.count} memories:\n${memories}`;
    },
  });
}