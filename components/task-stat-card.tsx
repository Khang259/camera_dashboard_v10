import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface TaskStatCardProps {
  title: string
  value: number
  description: string
  variant?: "default" | "success" | "destructive"
}

export function TaskStatCard({ title, value, description, variant = "default" }: TaskStatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "text-2xl font-bold",
            variant === "success" && "text-green-500",
            variant === "destructive" && "text-red-500",
          )}
        >
          {value}
        </div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}
