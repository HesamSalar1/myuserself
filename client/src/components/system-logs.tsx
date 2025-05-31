import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type BotLog } from "@shared/schema";

interface SystemLogsProps {
  newLogs?: BotLog[];
}

export function SystemLogs({ newLogs = [] }: SystemLogsProps) {
  const [logs, setLogs] = useState<BotLog[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const { data: initialLogs, refetch } = useQuery({
    queryKey: ["/api/logs?limit=50"],
  });

  useEffect(() => {
    if (initialLogs) {
      setLogs(initialLogs);
    }
  }, [initialLogs]);

  useEffect(() => {
    if (newLogs.length > 0) {
      setLogs(prev => [...newLogs, ...prev].slice(0, 100));
    }
  }, [newLogs]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const clearLogs = async () => {
    try {
      await fetch("/api/logs", {
        method: "DELETE",
        credentials: "include",
      });
      setLogs([]);
    } catch (error) {
      console.error("Failed to clear logs:", error);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "success":
        return "text-green-400";
      case "warn":
        return "text-yellow-400";
      case "error":
        return "text-red-400";
      default:
        return "text-blue-400";
    }
  };

  const formatTime = (timestamp: string | Date | null) => {
    if (!timestamp) return "[--:--:--]";
    
    const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
    return `[${date.toLocaleTimeString("fa-IR", { hour12: false })}]`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-slate-800">
            لاگ سیستم کلی
          </CardTitle>
          <div className="flex space-x-2 space-x-reverse">
            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
            >
              پاک کردن لاگها
            </Button>
            <Button
              size="sm"
              onClick={() => refetch()}
            >
              <i className="fas fa-refresh mr-2"></i>
              تازه‌سازی
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="bg-slate-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
          <div className="space-y-1">
            {logs.length === 0 ? (
              <div className="text-slate-500 text-center py-8">
                هیچ لاگی یافت نشد
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex items-start space-x-2 space-x-reverse">
                  <span className="text-slate-500 text-xs mt-0.5 flex-shrink-0">
                    {formatTime(log.timestamp)}
                  </span>
                  <span className={`flex-shrink-0 ${getLevelColor(log.level)}`}>
                    [{log.level.toUpperCase()}]
                  </span>
                  {log.botId && (
                    <span className="text-slate-400 flex-shrink-0">
                      [Bot {log.botId}]
                    </span>
                  )}
                  <span className="text-green-400 break-words">
                    {log.message}
                  </span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
