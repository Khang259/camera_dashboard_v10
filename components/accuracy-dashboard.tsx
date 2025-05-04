"use client"

import { useCameraStore } from "@/lib/stores/camera-store"
import { useStreamStore } from "@/lib/stores/stream-store"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AccuracyChart } from "./accuracy-chart"
import { AccuracyTable } from "./accuracy-table"

export function AccuracyDashboard() {
  const { cameras } = useCameraStore()
  const { streamInfo } = useStreamStore()

  return (
    <div className="space-y-4">
      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="details">Detailed View</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {cameras.map((camera) => {
              const info = streamInfo[camera.id] || {
                accuracy: { overall: 0, person: 0, car: 0, animal: 0 },
              }

              return (
                <Card key={camera.id}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">{camera.name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{Math.round(info.accuracy?.overall * 100)}%</div>
                    <p className="text-xs text-muted-foreground">Overall detection accuracy</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Accuracy Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <AccuracyChart cameras={cameras} streamInfo={streamInfo} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="details">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Accuracy Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <AccuracyTable cameras={cameras} streamInfo={streamInfo} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
