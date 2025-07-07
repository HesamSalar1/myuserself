import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { 
  Bot, 
  Play, 
  Square, 
  RotateCcw,
  Settings,
  AlertCircle 
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
}

export default function BotManagement() {
  const queryClient = useQueryClient()
  
  const { data: botStatus, isLoading } = useQuery<BotStatus>({
    queryKey: ['/api/bots/status'],
    refetchInterval: 5000,
  })

  const startBotMutation = useMutation({
    mutationFn: async (botId: number) => {
      const response = await fetch(`/api/bots/${botId}/start`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to start bot')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/bots/status'] })
    },
  })

  const stopBotMutation = useMutation({
    mutationFn: async (botId: number) => {
      const response = await fetch(`/api/bots/${botId}/stop`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to stop bot')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/bots/status'] })
    },
  })

  const handleStartBot = (botId: number) => {
    startBotMutation.mutate(botId)
  }

  const handleStopBot = (botId: number) => {
    stopBotMutation.mutate(botId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RotateCcw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">مدیریت ربات‌ها</h1>
        <p className="text-muted-foreground">
          کنترل کامل ربات‌های تلگرام شما
        </p>
      </div>

      {/* Monitoring Bot */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 space-x-reverse">
            <AlertCircle className="h-5 w-5" />
            <span>ربات مانیتورینگ</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center space-x-4 space-x-reverse">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Bot className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold">{botStatus?.monitoringBot.name}</h3>
                <p className="text-sm text-muted-foreground">
                  ربات گزارش‌دهی ایموجی‌های ممنوعه
                </p>
                <p className="text-xs text-muted-foreground">
                  آخرین بازدید: {botStatus?.monitoringBot.lastSeen ? 
                    new Date(botStatus.monitoringBot.lastSeen).toLocaleString('fa-IR') : 
                    'نامشخص'
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 space-x-reverse">
              <Badge variant={botStatus?.monitoringBot.status === 'active' ? 'default' : 'secondary'}>
                {botStatus?.monitoringBot.status === 'active' ? 'فعال' : 'غیرفعال'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Bots */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 space-x-reverse">
            <Bot className="h-5 w-5" />
            <span>ربات‌های اصلی</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {botStatus?.mainBots.map((bot) => (
              <div key={bot.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2 space-x-reverse">
                    <div className="p-2 bg-secondary rounded-lg">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="font-medium">{bot.name}</h3>
                      <p className="text-xs text-muted-foreground">
                        ID: {bot.id}
                      </p>
                    </div>
                  </div>
                  <Badge variant={bot.status === 'active' ? 'default' : 'secondary'}>
                    {bot.status === 'active' ? 'فعال' : 'غیرفعال'}
                  </Badge>
                </div>

                <div className="text-xs text-muted-foreground mb-3">
                  آخرین بازدید: {new Date(bot.lastSeen).toLocaleString('fa-IR')}
                </div>

                <div className="flex space-x-2 space-x-reverse">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStartBot(bot.id)}
                    disabled={startBotMutation.isPending}
                    className="flex-1"
                  >
                    <Play className="h-3 w-3 mr-1" />
                    شروع
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleStopBot(bot.id)}
                    disabled={stopBotMutation.isPending}
                    className="flex-1"
                  >
                    <Square className="h-3 w-3 mr-1" />
                    توقف
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="px-2"
                  >
                    <Settings className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Information */}
      <Card>
        <CardHeader>
          <CardTitle>اطلاعات سیستم</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground">کل ربات‌ها</div>
              <div className="text-2xl font-bold">{botStatus?.mainBots.length || 0} + 1</div>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground">ربات‌های فعال</div>
              <div className="text-2xl font-bold text-green-600">
                {botStatus?.mainBots.filter(bot => bot.status === 'active').length || 0}
              </div>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground">ربات‌های غیرفعال</div>
              <div className="text-2xl font-bold text-red-600">
                {botStatus?.mainBots.filter(bot => bot.status !== 'active').length || 0}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}