"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import type { Camera, StreamInfo } from "@/lib/types"

interface AccuracyTableProps {
  cameras: Camera[]
  streamInfo: Record<string, StreamInfo | undefined>
}

export function AccuracyTable({ cameras, streamInfo }: AccuracyTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Camera</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Overall</TableHead>
          <TableHead>Person</TableHead>
          <TableHead>Car</TableHead>
          <TableHead>Animal</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {cameras.map((camera) => {
          const info = streamInfo[camera.id] || {
            isOnline: false,
            accuracy: { overall: 0, person: 0, car: 0, animal: 0 },
          }

          return (
            <TableRow key={camera.id}>
              <TableCell className="font-medium">{camera.name}</TableCell>
              <TableCell>
                <Badge variant={info.isOnline ? "success" : "destructive"}>
                  {info.isOnline ? "Online" : "Offline"}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={info.accuracy?.overall * 100 || 0} className="h-2 w-24" />
                  <span className="text-sm">{Math.round(info.accuracy?.overall * 100 || 0)}%</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={info.accuracy?.person * 100 || 0} className="h-2 w-24" />
                  <span className="text-sm">{Math.round(info.accuracy?.person * 100 || 0)}%</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={info.accuracy?.car * 100 || 0} className="h-2 w-24" />
                  <span className="text-sm">{Math.round(info.accuracy?.car * 100 || 0)}%</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={info.accuracy?.animal * 100 || 0} className="h-2 w-24" />
                  <span className="text-sm">{Math.round(info.accuracy?.animal * 100 || 0)}%</span>
                </div>
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}
