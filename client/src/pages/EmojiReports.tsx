import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { 
  AlertTriangle, 
  Clock, 
  Hash, 
  Bot,
  RefreshCw 
} from 'lucide-react'

interface EmojiReport {
  id: number
  chatId: string
  chatTitle: string
  emoji: string
  stoppedBots: string[]
  reportedAt: string
}

export default function EmojiReports() {
  const { data: reports, isLoading } = useQuery<EmojiReport[]>({
    queryKey: ['/api/reports/emoji'],
    refetchInterval: 10000, // Refresh every 10 seconds
  })

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
      <div>
        <h1 className="text-3xl font-bold">گزارش ایموجی‌های ممنوعه</h1>
        <p className="text-muted-foreground">
          نظارت بر توقف‌های ناشی از ایموجی‌های ممنوعه
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              کل گزارش‌ها
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reports?.length || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              گزارش‌های امروز
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {reports?.filter(report => {
                const today = new Date().toDateString()
                const reportDate = new Date(report.reportedAt).toDateString()
                return today === reportDate
              }).length || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              گروه‌های تأثیرگذار
            </CardTitle>
            <Hash className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {new Set(reports?.map(r => r.chatId)).size || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              میانگین ربات‌های متوقف شده
            </CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {reports?.length ? 
                Math.round(reports.reduce((sum, r) => sum + r.stoppedBots.length, 0) / reports.length) :
                0
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Reports List */}
      <Card>
        <CardHeader>
          <CardTitle>گزارش‌های اخیر</CardTitle>
        </CardHeader>
        <CardContent>
          {reports && reports.length > 0 ? (
            <div className="space-y-4">
              {reports.map((report) => (
                <div key={report.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 space-x-reverse mb-2">
                        <AlertTriangle className="h-4 w-4 text-orange-500" />
                        <h3 className="font-semibold">{report.chatTitle}</h3>
                        <Badge variant="outline">
                          شناسه: {report.chatId}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                        <div>
                          <div className="text-sm text-muted-foreground">ایموجی ممنوعه</div>
                          <div className="text-2xl">{report.emoji}</div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">تعداد ربات‌های متوقف شده</div>
                          <div className="text-lg font-semibold text-red-600">
                            {report.stoppedBots.length} ربات
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">زمان گزارش</div>
                          <div className="text-sm">
                            {new Date(report.reportedAt).toLocaleString('fa-IR')}
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="text-sm text-muted-foreground mb-2">ربات‌های متوقف شده:</div>
                        <div className="flex flex-wrap gap-2">
                          {report.stoppedBots.map((bot, index) => (
                            <Badge key={index} variant="secondary">
                              {bot}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">هیچ گزارشی ثبت نشده</h3>
              <p className="text-muted-foreground">
                تاکنون هیچ ایموجی ممنوعه‌ای تشخیص داده نشده است
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>فعالیت اخیر</CardTitle>
        </CardHeader>
        <CardContent>
          {reports && reports.length > 0 ? (
            <div className="space-y-2">
              {reports.slice(0, 5).map((report) => (
                <div key={report.id} className="flex items-center space-x-3 space-x-reverse text-sm">
                  <div className="w-2 h-2 bg-orange-500 rounded-full flex-shrink-0"></div>
                  <span>
                    ایموجی <span className="font-mono">{report.emoji}</span> در گروه 
                    <span className="font-medium"> {report.chatTitle} </span>
                    باعث توقف <span className="font-semibold text-red-600">{report.stoppedBots.length}</span> ربات شد
                  </span>
                  <div className="text-muted-foreground flex-shrink-0">
                    {new Date(report.reportedAt).toLocaleTimeString('fa-IR')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-4">
              هیچ فعالیت اخیری وجود ندارد
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}