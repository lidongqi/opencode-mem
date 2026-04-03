import { tool, type ToolContext } from "@opencode-ai/plugin";
import { z } from "zod";
import type { MemoryClient } from "../client.js";

export function createMemoryHistoryTool(client: MemoryClient) {
  return tool({
    description: "Get the history of changes for a memory",
    args: {
      memory_id: z.string().describe("ID of the memory to get history for"),
    },
    async execute(args: { memory_id: string }, context: ToolContext) {
      const result = await client.getMemoryHistory(args.memory_id);

      if (!result.success) {
        return `Failed to get memory history: ${result.error}`;
      }

      if (!result.history || result.history.length === 0) {
        return "No history available for this memory.";
      }

      const history = result.history
        .map((entry: { old_memory?: string; new_memory?: string; timestamp?: string }, i: number) => {
          const oldMem = entry.old_memory || 'None';
          const newMem = entry.new_memory || 'None';
          const timestamp = entry.timestamp || 'Unknown time';
          return `${i + 1}. [${timestamp}]\n   Old: ${oldMem}\n   New: ${newMem}`;
        })
        .join('\n\n');

      return `Memory history:\n${history}`;
    },
  });
}