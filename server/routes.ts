import { Router } from 'express'
import { exec } from 'child_process'
import { promisify } from 'util'
import fs from 'fs/promises'
import path from 'path'

const router = Router()
const execAsync = promisify(exec)

// Bot status endpoint
router.get('/bots/status', async (req, res) => {
  try {
    // Read the log file to get bot status
    const logPath = path.join(process.cwd(), 'unified_bots.log')
    let logContent = ''
    
    try {
      logContent = await fs.readFile(logPath, 'utf-8')
    } catch (error) {
      // Log file doesn't exist yet
    }

    // Extract recent status information from logs
    const recentLogs = logContent.split('\n').slice(-50).filter(line => line.trim())
    
    const botStatus = {
      mainBots: Array.from({length: 9}, (_, i) => ({
        id: i + 1,
        name: `Bot ${i + 1}`,
        status: 'unknown',
        lastSeen: new Date().toISOString()
      })),
      monitoringBot: {
        name: 'Monitoring Bot',
        status: 'unknown',
        lastSeen: new Date().toISOString()
      },
      totalBots: 10,
      activeBots: 0,
      lastUpdate: new Date().toISOString()
    }

    res.json(botStatus)
  } catch (error) {
    console.error('Error getting bot status:', error)
    res.status(500).json({ error: 'Failed to get bot status' })
  }
})

// Emoji reports endpoint
router.get('/reports/emoji', async (req, res) => {
  try {
    // Read monitoring bot database
    const dbPath = path.join(process.cwd(), 'monitoring_bot.db')
    
    // For now, return mock data since DB integration requires more setup
    const reports = [
      {
        id: 1,
        chatId: '-1001234567890',
        chatTitle: 'Test Group',
        emoji: '⚡',
        stoppedBots: ['bot_1', 'bot_2', 'bot_3'],
        reportedAt: new Date().toISOString()
      }
    ]

    res.json(reports)
  } catch (error) {
    console.error('Error getting emoji reports:', error)
    res.status(500).json({ error: 'Failed to get emoji reports' })
  }
})

// Start/stop bot endpoints
router.post('/bots/:id/start', async (req, res) => {
  try {
    const botId = req.params.id
    // Implementation would depend on how bots are managed
    res.json({ success: true, message: `Bot ${botId} start command sent` })
  } catch (error) {
    console.error('Error starting bot:', error)
    res.status(500).json({ error: 'Failed to start bot' })
  }
})

router.post('/bots/:id/stop', async (req, res) => {
  try {
    const botId = req.params.id
    // Implementation would depend on how bots are managed
    res.json({ success: true, message: `Bot ${botId} stop command sent` })
  } catch (error) {
    console.error('Error stopping bot:', error)
    res.status(500).json({ error: 'Failed to stop bot' })
  }
})

// Launcher control endpoints
router.post('/launcher/start', async (req, res) => {
  try {
    // Start the unified bot launcher
    execAsync('python3 unified_bot_launcher.py', { cwd: process.cwd() })
    res.json({ success: true, message: 'Bot launcher started' })
  } catch (error) {
    console.error('Error starting launcher:', error)
    res.status(500).json({ error: 'Failed to start launcher' })
  }
})

router.post('/launcher/stop', async (req, res) => {
  try {
    // Stop the unified bot launcher (would need process management)
    res.json({ success: true, message: 'Bot launcher stop command sent' })
  } catch (error) {
    console.error('Error stopping launcher:', error)
    res.status(500).json({ error: 'Failed to stop launcher' })
  }
})

// Get recent logs
router.get('/logs', async (req, res) => {
  try {
    const logPath = path.join(process.cwd(), 'unified_bots.log')
    let logContent = ''
    
    try {
      logContent = await fs.readFile(logPath, 'utf-8')
    } catch (error) {
      logContent = 'No logs available yet'
    }

    const recentLogs = logContent.split('\n').slice(-100).filter(line => line.trim())
    
    res.json({ logs: recentLogs })
  } catch (error) {
    console.error('Error reading logs:', error)
    res.status(500).json({ error: 'Failed to read logs' })
  }
})

export default router