import express from 'express'
import { createServer } from 'http'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { createServer as createViteServer } from 'vite'
import apiRoutes from './routes.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const app = express()
const httpServer = createServer(app)

// Middleware
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// API Routes
app.use('/api', apiRoutes)

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

const PORT = process.env.PORT || 5000

if (process.env.NODE_ENV === 'production') {
  // Serve static files in production
  app.use(express.static(join(__dirname, '../dist')))
  
  app.get('*', (req, res) => {
    res.sendFile(join(__dirname, '../dist/index.html'))
  })
  
  httpServer.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`)
  })
} else {
  // Serve static HTML for development
  app.get('*', (req, res) => {
    res.send(`
      <!DOCTYPE html>
      <html lang="fa" dir="rtl">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>پنل مدیریت ربات‌های تلگرام</title>
          <script src="https://cdn.tailwindcss.com"></script>
          <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
          </style>
        </head>
        <body class="bg-gray-900 text-white">
          <div class="container mx-auto px-4 py-8">
            <div class="text-center mb-8">
              <h1 class="text-4xl font-bold mb-4">🤖 پنل مدیریت ربات‌های تلگرام</h1>
              <p class="text-gray-300">سیستم نظارت و کنترل ربات‌ها</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-xl font-semibold mb-2">ربات مانیتورینگ</h3>
                <div class="text-green-400 font-medium">✅ فعال</div>
                <p class="text-gray-400 text-sm mt-2">گزارش‌دهی ایموجی‌های ممنوعه</p>
              </div>
              
              <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-xl font-semibold mb-2">ربات‌های اصلی</h3>
                <div class="text-orange-400 font-medium">⏸️ آماده</div>
                <p class="text-gray-400 text-sm mt-2">9 ربات در حالت انتظار</p>
              </div>
              
              <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-xl font-semibold mb-2">وضعیت سیستم</h3>
                <div class="text-blue-400 font-medium">🔄 آماده</div>
                <p class="text-gray-400 text-sm mt-2">همه سیستم‌ها عملیاتی</p>
              </div>
            </div>
            
            <div class="bg-gray-800 p-6 rounded-lg mb-6">
              <h2 class="text-2xl font-bold mb-4">راهنمای راه‌اندازی</h2>
              <div class="space-y-4">
                <div class="border-l-4 border-green-500 pl-4">
                  <h3 class="font-semibold">1. راه‌اندازی کامل سیستم:</h3>
                  <code class="bg-gray-700 px-2 py-1 rounded text-sm">python3 start_system.py</code>
                </div>
                
                <div class="border-l-4 border-blue-500 pl-4">
                  <h3 class="font-semibold">2. فقط ربات‌های تلگرام:</h3>
                  <code class="bg-gray-700 px-2 py-1 rounded text-sm">python3 unified_bot_launcher.py</code>
                </div>
                
                <div class="border-l-4 border-purple-500 pl-4">
                  <h3 class="font-semibold">3. فقط ربات مانیتورینگ:</h3>
                  <code class="bg-gray-700 px-2 py-1 rounded text-sm">python3 monitoring_bot.py</code>
                </div>
              </div>
            </div>
            
            <div class="bg-gray-800 p-6 rounded-lg">
              <h2 class="text-2xl font-bold mb-4">قابلیت‌های سیستم</h2>
              <ul class="space-y-2 text-gray-300">
                <li>✅ ربات مانیتورینگ با توکن: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk</li>
                <li>✅ گزارش‌دهی فوری ایموجی‌های ممنوعه</li>
                <li>✅ یکپارچه‌سازی با 9 ربات اصلی</li>
                <li>✅ جداسازی رویدادها در هر چت</li>
                <li>✅ پنل مدیریت وب</li>
              </ul>
            </div>
          </div>
        </body>
      </html>
    `)
  })

  httpServer.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`)
    console.log(`🤖 Bot monitoring panel available at http://localhost:${PORT}`)
  })
}