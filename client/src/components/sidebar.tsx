import { Link, useLocation } from "wouter";
import { type Bot } from "@shared/schema";

interface SidebarProps {
  bots: Bot[];
}

export function Sidebar({ bots }: SidebarProps) {
  const [location] = useLocation();

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "bg-green-500";
      case "starting":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
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

  return (
    <div className="w-64 bg-white shadow-lg border-r border-slate-200">
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center space-x-3 space-x-reverse">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <i className="fas fa-robot text-white text-lg"></i>
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-800">مدیریت باتها</h1>
            <p className="text-sm text-slate-500">Bot Manager v2.1</p>
          </div>
        </div>
      </div>
      
      <nav className="p-4 space-y-2">
        <Link href="/">
          <a className={`flex items-center space-x-3 space-x-reverse p-3 rounded-lg font-medium ${
            location === "/" 
              ? "bg-primary/10 text-primary" 
              : "hover:bg-slate-100 text-slate-600"
          }`}>
            <i className="fas fa-tachometer-alt w-5"></i>
            <span>داشبورد کلی</span>
          </a>
        </Link>
        
        {bots.map((bot) => (
          <Link key={bot.id} href={`/bot/${bot.id}`}>
            <a className={`flex items-center space-x-3 space-x-reverse p-3 rounded-lg ${
              location === `/bot/${bot.id}` 
                ? "bg-primary/10 text-primary" 
                : "hover:bg-slate-100 text-slate-600"
            }`}>
              <i className="fas fa-robot w-5"></i>
              <span>{bot.name}</span>
              <span className={`mr-auto px-2 py-1 text-white text-xs rounded-full ${getStatusColor(bot.status)}`}>
                {getStatusText(bot.status)}
              </span>
            </a>
          </Link>
        ))}
        
        <div className="border-t border-slate-200 mt-4 pt-4">
          <Link href="/settings">
            <a className={`flex items-center space-x-3 space-x-reverse p-3 rounded-lg ${
              location === "/settings" 
                ? "bg-primary/10 text-primary" 
                : "hover:bg-slate-100 text-slate-600"
            }`}>
              <i className="fas fa-cog w-5"></i>
              <span>تنظیمات کلی</span>
            </a>
          </Link>
          <Link href="/stats">
            <a className={`flex items-center space-x-3 space-x-reverse p-3 rounded-lg ${
              location === "/stats" 
                ? "bg-primary/10 text-primary" 
                : "hover:bg-slate-100 text-slate-600"
            }`}>
              <i className="fas fa-chart-line w-5"></i>
              <span>آمار و گزارشات</span>
            </a>
          </Link>
          <Link href="/logs">
            <a className={`flex items-center space-x-3 space-x-reverse p-3 rounded-lg ${
              location === "/logs" 
                ? "bg-primary/10 text-primary" 
                : "hover:bg-slate-100 text-slate-600"
            }`}>
              <i className="fas fa-file-alt w-5"></i>
              <span>لاگ کلی سیستم</span>
            </a>
          </Link>
        </div>
      </nav>
    </div>
  );
}
