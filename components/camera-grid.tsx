// "use client"

// import { useCameraStore } from "@/lib/stores/camera-store"
// import { CameraCard } from "./camera-card"
// import { RefreshCw } from "lucide-react"

// export function CameraGrid() {
//   const { cameras } = useCameraStore()

//   return (
//     <div className="space-y-4">
//       <div className="border-2 border-red-500 rounded-lg p-4">
//         <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
//           {cameras.map((camera) => (
//             <CameraCard key={camera.id} camera={camera} />
//           ))}
//         </div>
//       </div>

//       <div className="border-2 border-red-500 rounded-lg p-4">
//         <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
//           {Array.from({ length: 12 }).map((_, index) => (
//             <button
//               key={index}
//               className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
//             >
//               Button {index + 1}
//             </button>
//           ))}
//         </div>
//       </div>
//     </div>
//   )
// }



"use client";

import { useEffect, useState } from "react";
import { useCameraStore } from "@/lib/stores/camera-store";
import { CameraCard } from "./camera-card";

export function CameraGrid() {
  const { cameras, setCameras } = useCameraStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCameras() {
      try {
        const response = await fetch("http://localhost:7000/api/cameras");
        const data = await response.json();
        // Add useWebRTC flag (example: use WebRTC for camera_2)
        const updatedCameras = data.cameras.map((cam: any) => ({
          ...cam,
          useWebRTC: cam.id === "camera_2", // Example condition
        }));
        setCameras(updatedCameras);
      } catch (error) {
        console.error("Error fetching cameras:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchCameras();
  }, [setCameras]);

  if (loading) return <div>Loading cameras...</div>;

  return (
    <div className="space-y-4">
      <div className="border-2 border-red-500 rounded-lg p-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {cameras.map((camera) => (
            <CameraCard key={camera.id} camera={camera} />
          ))}
        </div>
      </div>
    </div>
  );
}