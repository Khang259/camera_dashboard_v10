"use client"

import { useState, useEffect } from "react"
import { useTaskStore } from "@/lib/stores/task-store"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TaskStatCard } from "./task-stat-card"
import { TaskChart } from "./task-chart"

export function TaskStatistics() {
  const { taskRecords, getTasksByDate } = useTaskStore()
  const [todayStats, setTodayStats] = useState({ total: 0, completed: 0, failed: 0 })
  const [weekStats, setWeekStats] = useState({ total: 0, completed: 0, failed: 0 })
  const [monthStats, setMonthStats] = useState({ total: 0, completed: 0, failed: 0 })

  useEffect(() => {
    // Calculate today's stats
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const endOfDay = new Date(today)
    endOfDay.setHours(23, 59, 59, 999)

    const todayRecords = getTasksByDate(today, endOfDay)
    setTodayStats({
      total: todayRecords.length,
      completed: todayRecords.filter((r) => r.status === "completed").length,
      failed: todayRecords.filter((r) => r.status === "failed").length,
    })

    // Calculate 7-day stats
    const weekStart = new Date(today)
    weekStart.setDate(today.getDate() - 6)

    const weekRecords = getTasksByDate(weekStart, endOfDay)
    setWeekStats({
      total: weekRecords.length,
      completed: weekRecords.filter((r) => r.status === "completed").length,
      failed: weekRecords.filter((r) => r.status === "failed").length,
    })

    // Calculate 30-day stats
    const monthStart = new Date(today)
    monthStart.setDate(today.getDate() - 29)

    const monthRecords = getTasksByDate(monthStart, endOfDay)
    setMonthStats({
      total: monthRecords.length,
      completed: monthRecords.filter((r) => r.status === "completed").length,
      failed: monthRecords.filter((r) => r.status === "failed").length,
    })
  }, [taskRecords, getTasksByDate])

  return (
    <Tabs defaultValue="today" className="w-full">
      <TabsList>
        <TabsTrigger value="today">Today</TabsTrigger>
        <TabsTrigger value="week">Last 7 Days</TabsTrigger>
        <TabsTrigger value="month">Last 30 Days</TabsTrigger>
      </TabsList>

      <TabsContent value="today" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TaskStatCard title="Total Tasks" value={todayStats.total} description="Tasks executed today" />
          <TaskStatCard
            title="Completed"
            value={todayStats.completed}
            description="Successfully completed tasks"
            variant="success"
          />
          <TaskStatCard
            title="Failed"
            value={todayStats.failed}
            description="Failed task executions"
            variant="destructive"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Today's Task Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <TaskChart period="today" />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="week" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TaskStatCard title="Total Tasks" value={weekStats.total} description="Tasks executed in the last 7 days" />
          <TaskStatCard
            title="Completed"
            value={weekStats.completed}
            description="Successfully completed tasks"
            variant="success"
          />
          <TaskStatCard
            title="Failed"
            value={weekStats.failed}
            description="Failed task executions"
            variant="destructive"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>7-Day Task Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <TaskChart period="week" />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="month" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TaskStatCard title="Total Tasks" value={monthStats.total} description="Tasks executed in the last 30 days" />
          <TaskStatCard
            title="Completed"
            value={monthStats.completed}
            description="Successfully completed tasks"
            variant="success"
          />
          <TaskStatCard
            title="Failed"
            value={monthStats.failed}
            description="Failed task executions"
            variant="destructive"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>30-Day Task Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <TaskChart period="month" />
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  )
}
