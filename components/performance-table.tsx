// "use client"

// import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table"
// import { useCameraStore } from "@/lib/stores/camera-store"
// import { useStreamStore } from "@/lib/stores/stream-store"
// import { PerformanceRow } from "./performance-row"

// export function PerformanceTable() {
//   const { cameras } = useCameraStore()
//   const { streamInfo } = useStreamStore()

//   return (
//     <div className="rounded-md border">
//       <Table>
//         <TableHeader>
//           <TableRow>
//             <TableHead>Camera</TableHead>
//             <TableHead>Status</TableHead>
//             <TableHead>FPS</TableHead>
//             <TableHead>Resolution</TableHead>
//             <TableHead>Bitrate</TableHead>
//             <TableHead>Latency</TableHead>
//           </TableRow>
//         </TableHeader>
//         <TableBody>
//           {cameras.map((camera) => (
//             <PerformanceRow key={camera.id} camera={camera} streamInfo={streamInfo[camera.id]} />
//           ))}
//         </TableBody>
//       </Table>
//     </div>
//   )
// }
