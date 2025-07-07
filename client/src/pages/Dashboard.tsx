import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { 
  Bot, 
  Activity, 
  AlertCircle, 
  Play, 
  Square,
  RefreshCw 
} from 'lucide-react'

interface BotStatus {
  mainBots: Array<{
    id: number
    name: string
    status: string
    lastSeen: string
  }>
  monitoringBot: {
    name: string
    status: string
    lastSeen: string
  }
  totalBots: number
  activeBots: number
  lastUpdate: string
}

export default function Dashboard() {
  const { data: botStatus, isLoading, refetch } = useQuery<BotStatus>({
    queryKey: ['/api/bots/status'],
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const { data: recentLogs } = useQuery<{ logs: string[] }>({
    queryKey: ['/api/logs'],
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const startLauncher = async () => {
    try {
      const response = await fetch('/api/launcher/start', {
        method: 'POST',
      })
      if (response.ok) {
        refetch()
      }
    } catch (error) {
      console.error('Failed to start launcher:', error)
    }
  }

  const stopLauncher = async () => {
    try {
      const response = await fetch('/api/launcher/stop', {
        method: 'POST',
      })
      if (response.ok) {
        refetch()
      }
    } catch (error) {
      console.error('Failed to stop launcher:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">داشبورد مدیریت ربات‌ها</h1>
          <p className="text-muted-foreground">
            نظارت و کنترل ربات‌های تلگرام
          </p>
        </div>
        <div className="flex space-x-2 space-x-reverse">
          <Button onClick={startLauncher} className="flex items-center space-x-2 space-x-reverse">
            <Play className="h-4 w-4" />
            <span>شروع لانچر</span>
          </Button>
          <Button 
            variant="destructive" 
            onClick={stopLauncher}
            className="flex items-center space-x-2 space-x-reverse"
          >
            <Square className="h-4 w-4" />
            <span>توقف لانچر</span>
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              کل ربات‌ها
            </CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{botStatus?.totalBots || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              ربات‌های فعال
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {botStatus?.activeBots || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              ربات مانیتورینگ
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Badge variant={botStatus?.monitoringBot.status === 'active' ? 'default' : 'secondary'}>
              {botStatus?.monitoringBot.status === 'active' ? 'فعال' : 'غیرفعال'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              آخرین بروزرسانی
            </CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              {botStatus?.lastUpdate ? 
                new Date(botStatus.lastUpdate).toLocaleString('fa-IR') : 
                'نامشخص'
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bot List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>وضعیت ربات‌های اصلی</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {botStatus?.mainBots.map((bot) => (
                <div key={bot.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3 space-x-reverse">
                    <Bot className="h-5 w-5" />
                    <div>
                      <div className="font-medium">{bot.name}</div>
                      <div className="text-sm text-muted-foreground">
                        آخرین بازدید: {new Date(bot.lastSeen).toLocaleString('fa-IR')}
                      </div>
                    </div>
                  </div>
                  <Badge variant={bot.status === 'active' ? 'default' : 'secondary'}>
                    {bot.status === 'active' ? 'فعال' : 'غیرفعال'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>آخرین لاگ‌ها</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {recentLogs?.logs.slice(-10).reverse().map((log, index) => (
                <div key={index} className="text-sm font-mono p-2 bg-muted rounded">
                  {log}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}