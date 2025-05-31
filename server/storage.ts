import { bots, botLogs, systemMetrics, type Bot, type InsertBot, type BotLog, type InsertBotLog, type SystemMetrics, type InsertSystemMetrics, type BotStatus } from "@shared/schema";

export interface IStorage {
  // Bot management
  getBots(): Promise<Bot[]>;
  getBot(id: number): Promise<Bot | undefined>;
  createBot(bot: InsertBot): Promise<Bot>;
  updateBot(id: number, updates: Partial<Bot>): Promise<Bot | undefined>;
  updateBotStatus(id: number, status: BotStatus, pid?: number): Promise<Bot | undefined>;
  
  // Bot logs
  getBotLogs(botId?: number, limit?: number): Promise<BotLog[]>;
  addBotLog(log: InsertBotLog): Promise<BotLog>;
  clearBotLogs(botId?: number): Promise<void>;
  
  // System metrics
  getLatestSystemMetrics(): Promise<SystemMetrics | undefined>;
  addSystemMetrics(metrics: InsertSystemMetrics): Promise<SystemMetrics>;
  
  // Users (keeping existing interface)
  getUser(id: number): Promise<any>;
  getUserByUsername(username: string): Promise<any>;
  createUser(user: any): Promise<any>;
}

export class MemStorage implements IStorage {
  private bots: Map<number, Bot>;
  private botLogs: BotLog[];
  private systemMetrics: SystemMetrics[];
  private users: Map<number, any>;
  private currentBotId: number;
  private currentLogId: number;
  private currentMetricsId: number;
  private currentUserId: number;

  constructor() {
    this.bots = new Map();
    this.botLogs = [];
    this.systemMetrics = [];
    this.users = new Map();
    this.currentBotId = 1;
    this.currentLogId = 1;
    this.currentMetricsId = 1;
    this.currentUserId = 1;
    
    // Initialize with three bots
    this.initializeBots();
  }

  private initializeBots() {
    const defaultBots: InsertBot[] = [
      {
        name: "بات تلگرام اول",
        account: "API ID: 15508294",
        port: 3001,
        status: "offline",
        cpuUsage: 0,
        memoryUsage: 0,
      },
      {
        name: "بات تلگرام دوم", 
        account: "API ID: 29262538",
        port: 3002,
        status: "offline",
        cpuUsage: 0,
        memoryUsage: 0,
      },
      {
        name: "بات تلگرام سوم",
        account: "API ID: 21555907",
        port: 3003,
        status: "offline",
        cpuUsage: 0,
        memoryUsage: 0,
      },
    ];

    for (const bot of defaultBots) {
      const id = this.currentBotId++;
      this.bots.set(id, { 
        ...bot, 
        id, 
        pid: null, 
        lastStarted: null,
        status: bot.status || "offline",
        cpuUsage: bot.cpuUsage || 0,
        memoryUsage: bot.memoryUsage || 0
      });
    }
  }

  async getBots(): Promise<Bot[]> {
    return Array.from(this.bots.values());
  }

  async getBot(id: number): Promise<Bot | undefined> {
    return this.bots.get(id);
  }

  async createBot(insertBot: InsertBot): Promise<Bot> {
    const id = this.currentBotId++;
    const bot: Bot = { 
      ...insertBot, 
      id, 
      pid: null, 
      lastStarted: null,
      status: insertBot.status || "offline",
      cpuUsage: insertBot.cpuUsage || 0,
      memoryUsage: insertBot.memoryUsage || 0
    };
    this.bots.set(id, bot);
    return bot;
  }

  async updateBot(id: number, updates: Partial<Bot>): Promise<Bot | undefined> {
    const bot = this.bots.get(id);
    if (!bot) return undefined;
    
    const updatedBot = { ...bot, ...updates };
    this.bots.set(id, updatedBot);
    return updatedBot;
  }

  async updateBotStatus(id: number, status: BotStatus, pid?: number): Promise<Bot | undefined> {
    const bot = this.bots.get(id);
    if (!bot) return undefined;
    
    const updates: Partial<Bot> = { 
      status,
      lastStarted: status === "online" ? new Date() : bot.lastStarted
    };
    
    if (pid !== undefined) {
      updates.pid = pid;
    }
    
    return this.updateBot(id, updates);
  }

  async getBotLogs(botId?: number, limit: number = 100): Promise<BotLog[]> {
    let logs = this.botLogs;
    
    if (botId !== undefined) {
      logs = logs.filter(log => log.botId === botId);
    }
    
    return logs
      .sort((a, b) => (b.timestamp?.getTime() || 0) - (a.timestamp?.getTime() || 0))
      .slice(0, limit);
  }

  async addBotLog(insertLog: InsertBotLog): Promise<BotLog> {
    const id = this.currentLogId++;
    const log: BotLog = {
      id,
      botId: insertLog.botId || null,
      level: insertLog.level,
      message: insertLog.message,
      timestamp: new Date(),
    };
    this.botLogs.push(log);
    return log;
  }

  async clearBotLogs(botId?: number): Promise<void> {
    if (botId !== undefined) {
      this.botLogs = this.botLogs.filter(log => log.botId !== botId);
    } else {
      this.botLogs = [];
    }
  }

  async getLatestSystemMetrics(): Promise<SystemMetrics | undefined> {
    if (this.systemMetrics.length === 0) return undefined;
    
    return this.systemMetrics
      .sort((a, b) => (b.timestamp?.getTime() || 0) - (a.timestamp?.getTime() || 0))[0];
  }

  async addSystemMetrics(insertMetrics: InsertSystemMetrics): Promise<SystemMetrics> {
    const id = this.currentMetricsId++;
    const metrics: SystemMetrics = {
      ...insertMetrics,
      id,
      timestamp: new Date(),
    };
    this.systemMetrics.push(metrics);
    
    // Keep only last 100 entries
    if (this.systemMetrics.length > 100) {
      this.systemMetrics = this.systemMetrics.slice(-100);
    }
    
    return metrics;
  }

  // Keep existing user methods for compatibility
  async getUser(id: number): Promise<any> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<any> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: any): Promise<any> {
    const id = this.currentUserId++;
    const user = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }
}

export const storage = new MemStorage();
