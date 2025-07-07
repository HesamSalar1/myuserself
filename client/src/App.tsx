import { Router, Route, Switch } from 'wouter'
import { ThemeProvider } from './components/theme-provider'
import Dashboard from './pages/Dashboard'
import BotManagement from './pages/BotManagement'
import EmojiReports from './pages/EmojiReports'
import Navigation from './components/Navigation'

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="bot-panel-theme">
      <div className="min-h-screen bg-background">
        <Router>
          <Navigation />
          <main className="container mx-auto px-4 py-8">
            <Switch>
              <Route path="/" component={Dashboard} />
              <Route path="/bots" component={BotManagement} />
              <Route path="/reports" component={EmojiReports} />
              <Route>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-muted-foreground">
                    صفحه پیدا نشد
                  </h1>
                  <p className="text-muted-foreground mt-2">
                    صفحه مورد نظر شما وجود ندارد
                  </p>
                </div>
              </Route>
            </Switch>
          </main>
        </Router>
      </div>
    </ThemeProvider>
  )
}

export default App