"use client"

import { useState } from "react"
import { useTaskStore, formatDate } from "@/lib/stores/task-store"
import { useCameraStore } from "@/lib/stores/camera-store"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import type { TaskStatus } from "@/lib/types"

export function TaskList() {
  const { taskRecords } = useTaskStore()
  const { cameras } = useCameraStore()
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all")
  const [cameraFilter, setCameraFilter] = useState("all")
  const [modeFilter, setModeFilter] = useState<"all" | "auto" | "manual">("all")
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Get camera name by ID
  const getCameraName = (id: string) => {
    const camera = cameras.find((c) => c.id === id)
    return camera ? camera.name : "Unknown Camera"
  }

  // Filter and sort records
  const filteredRecords = taskRecords
    .filter((record) => {
      const matchesSearch =
        record.taskName.toLowerCase().includes(search.toLowerCase()) ||
        record.details.toLowerCase().includes(search.toLowerCase())
      const matchesStatus = statusFilter === "all" || record.status === statusFilter
      const matchesCamera = cameraFilter === "all" || record.cameraId === cameraFilter
      const matchesMode = modeFilter === "all" || record.mode === modeFilter
      return matchesSearch && matchesStatus && matchesCamera && matchesMode
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  // Pagination
  const totalPages = Math.ceil(filteredRecords.length / itemsPerPage)
  const paginatedRecords = filteredRecords.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

  // Status badge variant
  const getStatusVariant = (status: TaskStatus) => {
    switch (status) {
      case "completed":
        return "success"
      case "failed":
        return "destructive"
      case "in-progress":
        return "default"
      case "pending":
        return "secondary"
      default:
        return "outline"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Task History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input placeholder="Search tasks..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <div className="w-full sm:w-48">
              <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as TaskStatus | "all")}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="in-progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-full sm:w-48">
              <Select value={cameraFilter} onValueChange={setCameraFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by camera" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Cameras</SelectItem>
                  {cameras.map((camera) => (
                    <SelectItem key={camera.id} value={camera.id}>
                      {camera.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="w-full sm:w-48">
              <Select value={modeFilter} onValueChange={(value) => setModeFilter(value as "all" | "auto" | "manual")}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Modes</SelectItem>
                  <SelectItem value="manual">Manual</SelectItem>
                  <SelectItem value="auto">Auto</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Camera</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Task</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedRecords.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-4">
                      No task records found
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedRecords.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium whitespace-nowrap">{formatDate(record.timestamp)}</TableCell>
                      <TableCell>{getCameraName(record.cameraId)}</TableCell>
                      <TableCell className="capitalize">{record.mode}</TableCell>
                      <TableCell>{record.taskName}</TableCell>
                      <TableCell>
                        <div className="max-w-md">
                          {record.details}
                          {record.error && <div className="text-destructive text-sm mt-1">Error: {record.error}</div>}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(record.status)}>
                          {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    aria-disabled={currentPage === 1}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>

                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  // Show pages around current page
                  let pageNum = currentPage - 2 + i
                  if (pageNum < 1) pageNum += Math.min(5, totalPages)
                  if (pageNum > totalPages) pageNum -= Math.min(5, totalPages)

                  return (
                    <PaginationItem key={i}>
                      <PaginationLink onClick={() => setCurrentPage(pageNum)} isActive={currentPage === pageNum}>
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                <PaginationItem>
                  <PaginationNext
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    aria-disabled={currentPage === totalPages}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
