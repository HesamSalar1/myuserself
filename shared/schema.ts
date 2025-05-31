import { pgTable, text, serial, integer, boolean, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const bots = pgTable("bots", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  account: text("account").notNull(),
  port: integer("port").notNull(),
  status: text("status").notNull().default("offline"), // offline, starting, online, error
  pid: integer("pid"),
  cpuUsage: integer("cpu_usage").default(0),
  memoryUsage: integer("memory_usage").default(0), // in MB
  lastStarted: timestamp("last_started"),
});

export const botLogs = pgTable("bot_logs", {
  id: serial("id").primaryKey(),
  botId: integer("bot_id").references(() => bots.id),
  level: text("level").notNull(), // info, warn, error, success
  message: text("message").notNull(),
  timestamp: timestamp("timestamp").defaultNow(),
});

export const systemMetrics = pgTable("system_metrics", {
  id: serial("id").primaryKey(),
  cpuUsage: integer("cpu_usage").notNull(),
  memoryUsage: integer("memory_usage").notNull(), // in MB
  uptime: text("uptime").notNull(),
  activeBots: integer("active_bots").notNull(),
  timestamp: timestamp("timestamp").defaultNow(),
});

export const insertBotSchema = createInsertSchema(bots).omit({
  id: true,
  pid: true,
  lastStarted: true,
});

export const insertBotLogSchema = createInsertSchema(botLogs).omit({
  id: true,
  timestamp: true,
});

export const insertSystemMetricsSchema = createInsertSchema(systemMetrics).omit({
  id: true,
  timestamp: true,
});

export type Bot = typeof bots.$inferSelect;
export type InsertBot = z.infer<typeof insertBotSchema>;
export type BotLog = typeof botLogs.$inferSelect;
export type InsertBotLog = z.infer<typeof insertBotLogSchema>;
export type SystemMetrics = typeof systemMetrics.$inferSelect;
export type InsertSystemMetrics = z.infer<typeof insertSystemMetricsSchema>;

export type BotStatus = "offline" | "starting" | "online" | "error";
export type LogLevel = "info" | "warn" | "error" | "success";
