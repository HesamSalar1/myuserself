import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import multer from "multer";
import { storage } from "./storage";
import { botManager } from "./bot-manager";

const upload = multer({ storage: multer.memoryStorage() });

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time updates
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  wss.on('connection', (ws: WebSocket) => {
    console.log('WebSocket client connected');
    botManager.addWebSocketClient(ws);

    ws.on('close', () => {
      console.log('WebSocket client disconnected');
    });
  });

  // Bot management routes
  app.get("/api/bots", async (req, res) => {
    try {
      const bots = await storage.getBots();
      res.json(bots);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch bots" });
    }
  });

  app.get("/api/bots/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const bot = await storage.getBot(id);
      
      if (!bot) {
        return res.status(404).json({ error: "Bot not found" });
      }
      
      res.json(bot);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch bot" });
    }
  });

  app.post("/api/bots/:id/start", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const success = await botManager.startBot(id);
      
      if (success) {
        res.json({ message: "Bot start initiated" });
      } else {
        res.status(400).json({ error: "Failed to start bot" });
      }
    } catch (error) {
      res.status(500).json({ error: "Internal server error" });
    }
  });

  app.post("/api/bots/:id/stop", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const success = await botManager.stopBot(id);
      
      if (success) {
        res.json({ message: "Bot stop initiated" });
      } else {
        res.status(400).json({ error: "Failed to stop bot" });
      }
    } catch (error) {
      res.status(500).json({ error: "Internal server error" });
    }
  });

  app.post("/api/bots/:id/restart", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const success = await botManager.restartBot(id);
      
      if (success) {
        res.json({ message: "Bot restart initiated" });
      } else {
        res.status(400).json({ error: "Failed to restart bot" });
      }
    } catch (error) {
      res.status(500).json({ error: "Internal server error" });
    }
  });

  app.post("/api/bots/start-all", async (req, res) => {
    try {
      await botManager.startAllBots();
      res.json({ message: "All bots start initiated" });
    } catch (error) {
      res.status(500).json({ error: "Failed to start all bots" });
    }
  });

  app.post("/api/bots/:id/upload", upload.single("file"), async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }

      const success = await botManager.uploadBotFile(
        id,
        req.file.buffer,
        req.file.originalname
      );

      if (success) {
        res.json({ message: "File uploaded successfully" });
      } else {
        res.status(400).json({ error: "Failed to upload file" });
      }
    } catch (error) {
      res.status(500).json({ error: "File upload failed" });
    }
  });

  // Logs routes
  app.get("/api/logs", async (req, res) => {
    try {
      const botId = req.query.botId ? parseInt(req.query.botId as string) : undefined;
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 100;
      
      const logs = await storage.getBotLogs(botId, limit);
      res.json(logs);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch logs" });
    }
  });

  app.delete("/api/logs", async (req, res) => {
    try {
      const botId = req.query.botId ? parseInt(req.query.botId as string) : undefined;
      await storage.clearBotLogs(botId);
      res.json({ message: "Logs cleared" });
    } catch (error) {
      res.status(500).json({ error: "Failed to clear logs" });
    }
  });

  // System metrics routes
  app.get("/api/metrics", async (req, res) => {
    try {
      const metrics = await storage.getLatestSystemMetrics();
      res.json(metrics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch metrics" });
    }
  });

  return httpServer;
}
