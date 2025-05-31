import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { type Bot } from "@shared/schema";

interface BotCardProps {
  bot: Bot;
}

export function BotCard({ bot }: BotCardProps) {
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const startBotMutation = useMutation({
    mutationFn: () => apiRequest("POST", `/api/bots/${bot.id}/start`),
    onSuccess: () => {
      toast({ title: "بات در حال راه‌اندازی است" });
      queryClient.invalidateQueries({ queryKey: ["/api/bots"] });
    },
    onError: () => {
      toast({ title: "خطا در راه‌اندازی بات", variant: "destructive" });
    },
  });

  const stopBotMutation = useMutation({
    mutationFn: () => apiRequest("POST", `/api/bots/${bot.id}/stop`),
    onSuccess: () => {
      toast({ title: "بات در حال توقف است" });
      queryClient.invalidateQueries({ queryKey: ["/api/bots"] });
    },
    onError: () => {
      toast({ title: "خطا در توقف بات", variant: "destructive" });
    },
  });

  const restartBotMutation = useMutation({
    mutationFn: () => apiRequest("POST", `/api/bots/${bot.id}/restart`),
    onSuccess: () => {
      toast({ title: "بات در حال ریستارت است" });
      queryClient.invalidateQueries({ queryKey: ["/api/bots"] });
    },
    onError: () => {
      toast({ title: "خطا در ریستارت بات", variant: "destructive" });
    },
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      await fetch(`/api/bots/${bot.id}/upload`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      toast({ title: "فایل با موفقیت آپلود شد" });
    } catch (error) {
      toast({ title: "خطا در آپلود فایل", variant: "destructive" });
    } finally {
      setIsUploading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "bg-green-500/10 text-green-600";
      case "starting":
        return "bg-yellow-500/10 text-yellow-600";
      case "error":
        return "bg-red-500/10 text-red-600";
      default:
        return "bg-gray-500/10 text-gray-600";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "online":
        return "آنلاین";
      case "starting":
        return "در حال راه‌اندازی";
      case "error":
        return "خطا";
      default:
        return "آفلاین";
    }
  };

  const getIconColor = (status: string) => {
    switch (status) {
      case "online":
        return "text-green-500";
      case "starting":
        return "text-yellow-500";
      case "error":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3 space-x-reverse">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getStatusColor(bot.status).replace('text-', 'bg-')}/10`}>
                <i className={`fas fa-robot ${getIconColor(bot.status)}`}></i>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800">{bot.name}</h3>
                <p className="text-sm text-slate-500">{bot.account}</p>
              </div>
            </div>
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(bot.status)}`}>
              {getStatusText(bot.status)}
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center p-3 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-500">پورت</p>
              <p className="text-lg font-semibold text-slate-800">{bot.port}</p>
            </div>
            <div className="text-center p-3 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-500">PID</p>
              <p className="text-lg font-semibold text-slate-800">
                {bot.pid || "---"}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">مصرف CPU:</span>
              <span className="font-medium">{bot.cpuUsage || 0}%</span>
            </div>
            <Progress value={bot.cpuUsage || 0} className="h-2" />
            
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">مصرف RAM:</span>
              <span className="font-medium">{bot.memoryUsage || 0}MB</span>
            </div>
            <Progress value={(bot.memoryUsage || 0) / 10} className="h-2" />
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex space-x-2 space-x-reverse">
            {bot.status === "offline" || bot.status === "error" ? (
              <Button 
                className="flex-1 bg-green-500 hover:bg-green-600"
                onClick={() => startBotMutation.mutate()}
                disabled={startBotMutation.isPending}
              >
                <i className="fas fa-play mr-2"></i>
                شروع
              </Button>
            ) : (
              <Button 
                className="flex-1 bg-red-500 hover:bg-red-600"
                onClick={() => stopBotMutation.mutate()}
                disabled={stopBotMutation.isPending}
              >
                <i className="fas fa-stop mr-2"></i>
                توقف
              </Button>
            )}
            <Button 
              className="flex-1 bg-yellow-500 hover:bg-yellow-600"
              onClick={() => restartBotMutation.mutate()}
              disabled={restartBotMutation.isPending || bot.status === "offline"}
            >
              <i className="fas fa-redo mr-2"></i>
              ریستارت
            </Button>
          </div>
          
          <div className="border-t border-slate-200 pt-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              آپلود فایل جدید:
            </label>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-primary transition-colors cursor-pointer">
              <input
                type="file"
                accept=".js,.py,.zip"
                onChange={handleFileUpload}
                className="hidden"
                id={`file-upload-${bot.id}`}
                disabled={isUploading}
              />
              <label htmlFor={`file-upload-${bot.id}`} className="cursor-pointer">
                <i className="fas fa-upload text-slate-400 text-2xl mb-2 block"></i>
                <p className="text-sm text-slate-500">
                  {isUploading ? "در حال آپلود..." : "فایل را اینجا رها کنید یا کلیک کنید"}
                </p>
              </label>
            </div>
          </div>
          
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => window.open(`/logs?botId=${bot.id}`, "_blank")}
          >
            <i className="fas fa-file-alt mr-2"></i>
            مشاهده لاگها
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
