"use client"

import { TableCell, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import type { Camera, StreamInfo } from "@/lib/types"

interface PerformanceRowProps {
  camera: Camera
  streamInfo?: StreamInfo
}

export function PerformanceRow({ camera, streamInfo }: PerformanceRowProps) {
  const info = streamInfo || {
    boundingBoxes: [],
    fps: 0,
    resolution: "Unknown",
    bitrate: 0,
    latency: 0,
    isOnline: false,
  }

  return (
    <TableRow>
      <TableCell className="font-medium">{camera.name}</TableCell>
      <TableCell>
        <Badge variant={info.isOnline ? "success" : "destructive"}>{info.isOnline ? "Online" : "Offline"}</Badge>
      </TableCell>
      <TableCell>{info.fps} FPS</TableCell>
      <TableCell>{info.resolution}</TableCell>
      <TableCell>{info.bitrate} Kbps</TableCell>
      <TableCell>{info.latency} ms</TableCell>
    </TableRow>
  )
}
