import * as React from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "./card"
import { LucideIcon } from "lucide-react"

interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  value: string | number
  icon?: LucideIcon
  trend?: {
    value: number
    isPositive: boolean
  }
  description?: string
  loading?: boolean
}

const StatCard = React.forwardRef<HTMLDivElement, StatCardProps>(
  ({ className, title, value, icon: Icon, trend, description, loading, ...props }, ref) => {
    if (loading) {
      return (
        <Card ref={ref} className={cn("", className)} {...props}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
            {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
          </CardHeader>
          <CardContent>
            <div className="h-8 w-24 bg-muted animate-pulse rounded" />
            {description && (
              <div className="h-4 w-32 bg-muted animate-pulse rounded mt-2" />
            )}
          </CardContent>
        </Card>
      )
    }

    return (
      <Card ref={ref} className={cn("", className)} {...props}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          {trend && (
            <p className={cn("text-xs", trend.isPositive ? "text-green-600" : "text-red-600")}>
              {trend.isPositive ? "+" : ""}{trend.value}% from last month
            </p>
          )}
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </CardContent>
      </Card>
    )
  }
)
StatCard.displayName = "StatCard"

export { StatCard }
