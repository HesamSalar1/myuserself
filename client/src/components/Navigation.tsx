import { Link, useLocation } from 'wouter'
import { cn } from '../lib/utils'
import { Button } from './ui/button'
import { 
  LayoutDashboard, 
  Bot, 
  AlertTriangle, 
  Moon, 
  Sun, 
  Monitor 
} from 'lucide-react'
import { useTheme } from './theme-provider'

const navItems = [
  {
    href: '/',
    label: 'داشبورد',
    icon: LayoutDashboard
  },
  {
    href: '/bots',
    label: 'مدیریت ربات‌ها',
    icon: Bot
  },
  {
    href: '/reports',
    label: 'گزارش ایموجی‌ها',
    icon: AlertTriangle
  }
]

export default function Navigation() {
  const [location] = useLocation()
  const { theme, setTheme } = useTheme()

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-4 space-x-reverse">
            <Link href="/">
              <div className="flex items-center space-x-2 space-x-reverse">
                <Bot className="h-6 w-6 text-primary" />
                <span className="font-bold text-lg">پنل مدیریت ربات‌ها</span>
              </div>
            </Link>
            
            <div className="flex items-center space-x-1 space-x-reverse">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location === item.href
                
                return (
                  <Link key={item.href} href={item.href}>
                    <Button
                      variant={isActive ? 'default' : 'ghost'}
                      size="sm"
                      className="flex items-center space-x-2 space-x-reverse"
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Button>
                  </Link>
                )
              })}
            </div>
          </div>

          <div className="flex items-center space-x-2 space-x-reverse">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setTheme(theme === 'dark' ? 'light' : 'dark')
              }}
            >
              {theme === 'dark' ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}