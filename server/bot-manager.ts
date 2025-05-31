import { spawn, ChildProcess } from "child_process";
import path from "path";
import fs from "fs-extra";
import { storage } from "./storage";
import { WebSocket } from "ws";

export interface BotProcess {
  id: number;
  process: ChildProcess | null;
  status: "offline" | "starting" | "online" | "error";
  port: number;
  restartCount: number;
  lastError?: string;
}

export class BotManager {
  private bots: Map<number, BotProcess> = new Map();
  private wsClients: Set<WebSocket> = new Set();
  private metricsInterval?: NodeJS.Timeout;

  constructor() {
    this.initializeBots();
    this.startMetricsCollection();
  }

  private async initializeBots() {
    const botConfigs = await storage.getBots();
    
    for (const config of botConfigs) {
      this.bots.set(config.id, {
        id: config.id,
        process: null,
        status: "offline",
        port: config.port,
        restartCount: 0,
      });
    }
  }

  addWebSocketClient(ws: WebSocket) {
    this.wsClients.add(ws);
    
    ws.on("close", () => {
      this.wsClients.delete(ws);
    });
    
    // Send initial state
    this.sendToClients("bots_status", this.getBotStatuses());
  }

  private sendToClients(type: string, data: any) {
    const message = JSON.stringify({ type, data });
    
    this.wsClients.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(message);
      }
    });
  }

  private getBotStatuses() {
    return Array.from(this.bots.values()).map(bot => ({
      id: bot.id,
      status: bot.status,
      pid: bot.process?.pid || null,
      restartCount: bot.restartCount,
      lastError: bot.lastError,
    }));
  }

  async startBot(botId: number): Promise<boolean> {
    const bot = this.bots.get(botId);
    if (!bot) return false;

    if (bot.process && !bot.process.killed) {
      await this.addLog(botId, "warn", "Bot already running");
      return false;
    }

    try {
      bot.status = "starting";
      await storage.updateBotStatus(botId, "starting");
      await this.addLog(botId, "info", `Starting bot ${botId}...`);

      const botPath = path.resolve(process.cwd(), `bots/bot${botId}/index.js`);
      
      // Ensure bot file exists
      if (!fs.existsSync(botPath)) {
        throw new Error(`Bot file not found: ${botPath}`);
      }

      const childProcess = spawn("node", [botPath], {
        cwd: path.dirname(botPath),
        env: { 
          ...process.env, 
          BOT_ID: botId.toString(),
          BOT_PORT: bot.port.toString() 
        },
        stdio: ["pipe", "pipe", "pipe"],
      });

      bot.process = childProcess;

      // Handle process output
      childProcess.stdout?.on("data", (data) => {
        const message = data.toString().trim();
        this.addLog(botId, "info", message);
      });

      childProcess.stderr?.on("data", (data) => {
        const message = data.toString().trim();
        this.addLog(botId, "error", message);
      });

      // Handle process exit
      childProcess.on("exit", (code) => {
        bot.process = null;
        
        if (code === 0) {
          bot.status = "offline";
          this.addLog(botId, "info", `Bot ${botId} stopped normally`);
        } else {
          bot.status = "error";
          bot.lastError = `Process exited with code ${code}`;
          this.addLog(botId, "error", `Bot ${botId} crashed with exit code ${code}`);
        }
        
        storage.updateBotStatus(botId, bot.status);
        this.sendToClients("bot_status_update", { id: botId, status: bot.status, pid: null });
      });

      // Wait a moment for the process to start
      await new Promise(resolve => setTimeout(resolve, 2000));

      if (childProcess.killed || childProcess.exitCode !== null) {
        throw new Error("Process failed to start");
      }

      bot.status = "online";
      await storage.updateBotStatus(botId, "online", childProcess.pid);
      await this.addLog(botId, "success", `Bot ${botId} started successfully on port ${bot.port}`);
      
      this.sendToClients("bot_status_update", { 
        id: botId, 
        status: bot.status, 
        pid: childProcess.pid 
      });

      return true;

    } catch (error) {
      bot.status = "error";
      bot.lastError = error instanceof Error ? error.message : "Unknown error";
      await storage.updateBotStatus(botId, "error");
      await this.addLog(botId, "error", `Failed to start bot ${botId}: ${bot.lastError}`);
      
      this.sendToClients("bot_status_update", { id: botId, status: bot.status, pid: null });
      return false;
    }
  }

  async stopBot(botId: number): Promise<boolean> {
    const bot = this.bots.get(botId);
    if (!bot || !bot.process) return false;

    try {
      await this.addLog(botId, "info", `Stopping bot ${botId}...`);
      
      bot.process.kill("SIGTERM");
      
      // Wait for graceful shutdown
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(() => {
          if (bot.process && !bot.process.killed) {
            bot.process.kill("SIGKILL");
          }
          resolve();
        }, 5000);

        bot.process?.on("exit", () => {
          clearTimeout(timeout);
          resolve();
        });
      });

      bot.status = "offline";
      bot.process = null;
      await storage.updateBotStatus(botId, "offline");
      await this.addLog(botId, "info", `Bot ${botId} stopped`);
      
      this.sendToClients("bot_status_update", { id: botId, status: bot.status, pid: null });
      return true;

    } catch (error) {
      await this.addLog(botId, "error", `Error stopping bot ${botId}: ${error}`);
      return false;
    }
  }

  async restartBot(botId: number): Promise<boolean> {
    const bot = this.bots.get(botId);
    if (!bot) return false;

    bot.restartCount++;
    await this.addLog(botId, "info", `Restarting bot ${botId} (attempt ${bot.restartCount})...`);

    await this.stopBot(botId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    return this.startBot(botId);
  }

  async startAllBots(): Promise<void> {
    await this.addSystemLog("info", "Starting all bots...");
    
    for (const [botId] of this.bots) {
      await this.startBot(botId);
    }
  }

  async uploadBotFile(botId: number, fileBuffer: Buffer, filename: string): Promise<boolean> {
    try {
      const botDir = path.resolve(process.cwd(), `bots/bot${botId}`);
      await fs.ensureDir(botDir);

      const filePath = path.join(botDir, filename);
      await fs.writeFile(filePath, fileBuffer);

      await this.addLog(botId, "info", `File uploaded: ${filename}`);
      return true;

    } catch (error) {
      await this.addLog(botId, "error", `Failed to upload file: ${error}`);
      return false;
    }
  }

  private async addLog(botId: number, level: string, message: string) {
    await storage.addBotLog({
      botId,
      level,
      message,
    });

    this.sendToClients("new_log", {
      botId,
      level,
      message,
      timestamp: new Date().toISOString(),
    });
  }

  private async addSystemLog(level: string, message: string) {
    await storage.addBotLog({
      botId: null,
      level,
      message,
    });

    this.sendToClients("new_log", {
      botId: null,
      level,
      message,
      timestamp: new Date().toISOString(),
    });
  }

  private startMetricsCollection() {
    this.metricsInterval = setInterval(async () => {
      try {
        const bots = await storage.getBots();
        const activeBots = bots.filter(bot => bot.status === "online").length;
        
        // Simulate CPU and memory usage
        const cpuUsage = Math.floor(Math.random() * 50) + 10;
        const memoryUsage = Math.floor(Math.random() * 1000) + 500;
        const uptime = this.formatUptime(process.uptime());

        await storage.addSystemMetrics({
          cpuUsage,
          memoryUsage,
          uptime,
          activeBots,
        });

        // Update individual bot metrics
        for (const bot of bots) {
          if (bot.status === "online") {
            const botCpu = Math.floor(Math.random() * 20) + 5;
            const botMemory = Math.floor(Math.random() * 300) + 100;
            
            await storage.updateBot(bot.id, {
              cpuUsage: botCpu,
              memoryUsage: botMemory,
            });
          }
        }

        // Send updates to clients
        this.sendToClients("system_metrics", {
          cpuUsage,
          memoryUsage,
          uptime,
          activeBots,
        });

        this.sendToClients("bots_status", this.getBotStatuses());

      } catch (error) {
        console.error("Error collecting metrics:", error);
      }
    }, 5000);
  }

  private formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }

  cleanup() {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }

    // Stop all bots
    for (const [botId] of this.bots) {
      this.stopBot(botId);
    }
  }
}

export const botManager = new BotManager();
