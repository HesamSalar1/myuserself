import { type SystemMetrics } from "@shared/schema";

interface SystemOverviewProps {
  metrics?: SystemMetrics;
}

export function SystemOverview({ metrics }: SystemOverviewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">باتهای فعال</p>
            <p className="text-2xl font-bold text-slate-800">
              {metrics?.activeBots || 0}
            </p>
          </div>
          <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
            <i className="fas fa-robot text-green-500 text-xl"></i>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">مصرف CPU</p>
            <p className="text-2xl font-bold text-slate-800">
              {metrics?.cpuUsage || 0}%
            </p>
          </div>
          <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
            <i className="fas fa-microchip text-yellow-500 text-xl"></i>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">مصرف RAM</p>
            <p className="text-2xl font-bold text-slate-800">
              {metrics?.memoryUsage ? `${(metrics.memoryUsage / 1024).toFixed(1)}GB` : "0GB"}
            </p>
          </div>
          <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
            <i className="fas fa-memory text-blue-500 text-xl"></i>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">آپتایم سیستم</p>
            <p className="text-2xl font-bold text-slate-800">
              {metrics?.uptime || "0h 0m"}
            </p>
          </div>
          <div className="w-12 h-12 bg-slate-500/10 rounded-lg flex items-center justify-center">
            <i className="fas fa-clock text-slate-500 text-xl"></i>
          </div>
        </div>
      </div>
    </div>
  );
}
