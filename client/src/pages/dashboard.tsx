import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useWebSocket } from "@/hooks/use-websocket";
import { Sidebar } from "@/components/sidebar";
import { SystemOverview } from "@/components/system-overview";
import { BotCard } from "@/components/bot-card";
import { SystemLogs } from "@/components/system-logs";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { type Bot, type SystemMetrics, type BotLog } from "@shared/schema";

export default function Dashboard() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>();
  const [realtimeLogs, setRealtimeLogs] = useState<BotLog[]>([]);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: bots = [], isLoading: botsLoading } = useQuery<Bot[]>({
    queryKey: ["/api/bots"],
    refetchInterval: 5000,
  });

  const { data: metrics } = useQuery<SystemMetrics>({
    queryKey: ["/api/metrics"],
    refetchInterval: 5000,
  });

  const startAllBotsMutation = useMutation({
    mutationFn: () => apiRequest("POST", "/api/bots/start-all"),
    onSuccess: () => {
      toast({ title: "همه باتها در حال راه‌اندازی هستند" });
      queryClient.invalidateQueries({ queryKey: ["/api/bots"] });
    },
    onError: () => {
      toast({ title: "خطا در راه‌اندازی باتها", variant: "destructive" });
    },
  });

  const { isConnected } = useWebSocket((message) => {
    switch (message.type) {
      case "system_metrics":
        setSystemMetrics(message.data);
        break;
      case "bot_status_update":
        queryClient.invalidateQueries({ queryKey: ["/api/bots"] });
        break;
      case "new_log":
        setRealtimeLogs(prev => [message.data, ...prev].slice(0, 50));
        break;
      case "bots_status":
        queryClient.invalidateQueries({ queryKey: ["/api/bots"] });
        break;
    }
  });

  useEffect(() => {
    if (metrics) {
      setSystemMetrics(metrics);
    }
  }, [metrics]);

  if (botsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-slate-600">در حال بارگذاری...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-slate-50" dir="rtl">
      <Sidebar bots={bots} />
      
      <div className="flex-1 overflow-hidden">
        <header className="bg-white shadow-sm border-b border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-800">داشبورد مدیریت باتها</h2>
              <p className="text-slate-500 mt-1">مدیریت و کنترل سه اکانت بات به صورت همزمان</p>
            </div>
            <div className="flex items-center space-x-4 space-x-reverse">
              <div className="flex items-center space-x-2 space-x-reverse bg-slate-100 px-4 py-2 rounded-lg">
                <i className="fas fa-server text-slate-500"></i>
                <span className="text-sm text-slate-600">
                  سرور: {isConnected ? "آنلاین" : "آفلاین"}
                </span>
                <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}></div>
              </div>
              <Button 
                onClick={() => startAllBotsMutation.mutate()}
                disabled={startAllBotsMutation.isPending}
                className="bg-primary hover:bg-blue-600"
              >
                <i className="fas fa-play mr-2"></i>
                شروع همه باتها
              </Button>
            </div>
          </div>
        </header>

        <main className="p-6 overflow-y-auto">
          <SystemOverview metrics={systemMetrics} />
          
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
            {bots.map((bot) => (
              <BotCard key={bot.id} bot={bot} />
            ))}
          </div>

          <SystemLogs newLogs={realtimeLogs} />
        </main>
      </div>
    </div>
  );
}
