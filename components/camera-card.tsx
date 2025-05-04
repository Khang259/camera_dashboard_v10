// "use client"

// import { useIPCamera } from "@/hooks/use-ip-camera"
// import type { Camera } from "@/lib/types"
// import { RefreshCw } from "lucide-react"

// interface CameraCardProps {
//   camera: Camera
// }

// export function CameraCard({ camera }: CameraCardProps) {
//   const { isConnected, error, streamUrl, connect } = useIPCamera(camera)

//   return (
//     <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
//       {streamUrl ? (
//         <img
//           src={streamUrl}
//           alt={`${camera.name} Stream`}
//           className="w-full h-full object-cover"
//         />
//       ) : (
//         <div className="absolute inset-0 flex items-center justify-center text-white">
//           {error ? (
//             <div className="text-center">
//               <p className="text-red-500 mb-2">{error}</p>
//               <button
//                 onClick={connect}
//                 className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
//               >
//                 <RefreshCw className="w-4 h-4" />
//                 Reconnect
//               </button>
//             </div>
//           ) : !isConnected ? (
//             <div className="text-center">
//               <p>Connecting to camera...</p>
//               <button
//                 onClick={connect}
//                 className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors mt-2"
//               >
//                 <RefreshCw className="w-4 h-4" />
//                 Reconnect
//               </button>
//             </div>
//           ) : (
//             <p>No stream available</p>
//           )}
//         </div>
//       )}
//       <div className="absolute top-2 left-2 bg-black/50 text-white px-2 py-1 rounded">
//         {camera.name}
//       </div>
//       <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded">
//         {isConnected ? (
//           <span className="text-green-500">Connected</span>
//         ) : (
//           <span className="text-red-500">Disconnected</span>
//         )}
//       </div>
//     </div>
//   )
// }



"use client";

import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

interface CameraCardProps {
  camera: { id: string; name: string; rtsp_url?: string; useWebRTC?: boolean };
}

export function CameraCard({ camera }: CameraCardProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signalingUrl, setSignalingUrl] = useState<string>("");
  const [streamUrl, setStreamUrl] = useState<string>("");
  const ws = useRef<WebSocket | null>(null);
  const pc = useRef<RTCPeerConnection | null>(null);

  // Fetch config and stream URL
  useEffect(() => {
    async function fetchConfig() {
      try {
        const response = await fetch("http://localhost:7000/api/config");
        const config = await response.json();
        setSignalingUrl(config.signaling_server_url);

        // Fetch MJPEG stream URL if not using WebRTC
        if (!camera.useWebRTC) {
          const streamResponse = await fetch(`http://localhost:7000/api/cameras/${camera.id}/stream`);
          const streamData = await streamResponse.json();
          setStreamUrl(streamData.streamUrl);
          setIsConnected(true);
        }
      } catch (err) {
        setError("Failed to load configuration or stream");
      }
    }
    fetchConfig();
  }, [camera.id, camera.useWebRTC]);

  const connectWebRTC = async () => {
    if (!signalingUrl) return;

    try {
      ws.current = new WebSocket(signalingUrl);
      ws.current.onopen = () => {
        console.log("Connected to Signaling Server");
      };

      ws.current.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "id") {
          console.log("Client ID:", data.id);
        } else if (data.type === "answer") {
          await pc.current?.setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: data.sdp }));
        } else if (data.type === "candidate") {
          await pc.current?.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
      };

      pc.current = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      pc.current.ontrack = (event) => {
        if (videoRef.current) {
          videoRef.current.srcObject = event.streams[0];
          setIsConnected(true);
        }
      };

      pc.current.onicecandidate = (event) => {
        if (event.candidate) {
          ws.current?.send(
            JSON.stringify({
              type: "candidate",
              candidate: event.candidate.toJSON(),
              target: "webrtc-server",
            })
          );
        }
      };

      const offer = await pc.current.createOffer();
      await pc.current.setLocalDescription(offer);
      ws.current?.send(
        JSON.stringify({
          type: "offer",
          sdp: offer.sdp,
          clientId: "client",
          target: "webrtc-server",
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
      setIsConnected(false);
    }
  };

  useEffect(() => {
    if (camera.useWebRTC && signalingUrl) {
      connectWebRTC();
    }
    return () => {
      ws.current?.close();
      pc.current?.close();
    };
  }, [signalingUrl, camera.useWebRTC]);

  return (
    <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
      {isConnected ? (
        camera.useWebRTC ? (
          <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
        ) : (
          <img ref={imgRef} src={streamUrl} alt={`${camera.name} Stream`} className="w-full h-full object-cover" />
        )
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-white">
          {error ? (
            <div className="text-center">
              <p className="text-red-500 mb-2">{error}</p>
              <button
                onClick={() => (camera.useWebRTC ? connectWebRTC() : window.location.reload())}
                className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Reconnect
              </button>
            </div>
          ) : (
            <p>Connecting to camera...</p>
          )}
        </div>
      )}
      <div className="absolute top-2 left-2 bg-black/50 text-white px-2 py-1 rounded">{camera.name}</div>
      <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded">
        {isConnected ? <span className="text-green-500">Connected</span> : <span className="text-red-500">Disconnected</span>}
      </div>
    </div>
  );
}