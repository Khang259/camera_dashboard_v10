// "use client";
// import React from "react";
// import { useEffect, useRef, useState, useCallback } from "react";
// import { RefreshCw, Camera as CameraIcon, Video, VideoOff } from "lucide-react";
// import { Camera, WebRTCMessage } from "../lib/types";

// interface CameraWithVisible extends Camera {
//   visible: boolean;
// }

// interface CameraCardCallbacks {
//   onMessage: (message: WebRTCMessage) => void;
//   onError: (error: Event) => void;
//   onClose: () => void;
// }

// interface CameraCardProps {
//   camera: CameraWithVisible;
//   ws: WebSocket | null;
//   registerCallback: (cameraId: string, callback: CameraCardCallbacks) => () => void;
// }

// export const CameraCard = React.memo(function CameraCard({ camera, ws, registerCallback }: CameraCardProps) {
//   const videoRef = useRef<HTMLVideoElement>(null);
//   const [isConnected, setIsConnected] = useState(false);
//   const [isVideoPlaying, setIsVideoPlaying] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
//   const [stream, setStream] = useState<MediaStream | null>(null);
//   const pc = useRef<RTCPeerConnection | null>(null);
//   const clientId = useRef<string | null>(null);
//   const hasSentOffer = useRef(false);
//   const isConnecting = useRef(false);
//   const retryCount = useRef(0);
//   const maxRetries = 3;
//   const retryDelay = 5000; // 5 giây
//   const pendingAnswer = useRef<string | null>(null); // Lưu answer tạm thời nếu cần

//   const connectWebRTC = async () => {
//     console.log(
//       `Camera ${camera.id} visibility: ${camera.visible}, WebSocket: ${
//         ws ? ws.readyState : "null"
//       }, isConnecting: ${isConnecting.current}`
//     );
//     if (!camera.visible || !ws || ws.readyState !== WebSocket.OPEN || isConnecting.current) {
//       console.log(`Camera ${camera.id} not visible, WebSocket not available, or already connecting`);
//       return;
//     }

//     isConnecting.current = true;

//     try {
//       console.log(`Camera ${camera.id} initializing RTCPeerConnection`);
//       pc.current = new RTCPeerConnection({
//         iceServers: [
//           { urls: "stun:stun.l.google.com:19302" },
//           {
//             urls: "turn:openrelay.metered.ca:80",
//             username: "openrelayproject",
//             credential: "openrelayproject",
//           },
//           {
//             urls: "turn:openrelay.metered.ca:443",
//             username: "openrelayproject",
//             credential: "openrelayproject",
//           },
//         ],
//       });

//       console.log(`Camera ${camera.id} adding video transceiver`);
//       pc.current.addTransceiver("video", { direction: "recvonly" });

//       pc.current.ontrack = (event) => {
//         console.log(`Camera ${camera.id} received video track:`, event.streams[0]);
//         setStream(event.streams[0]);
//         setIsConnected(true);
//         setConnectionStatus("connected");
//         console.log(`Camera ${camera.id} video stream saved to state`);
//       };

//       pc.current.onicecandidate = (event) => {
//         if (event.candidate && ws.readyState === WebSocket.OPEN) {
//           console.log(`Camera ${camera.id} sending ICE candidate:`, event.candidate.toJSON());
//           ws.send(
//             JSON.stringify({
//               type: "candidate",
//               candidate: event.candidate.toJSON(),
//               target: "webrtc-server",
//               cameraId: camera.id,
//               clientId: clientId.current,
//             })
//           );
//           console.log(`Camera ${camera.id} ICE candidate sent successfully`);
//         } else {
//           console.log(`Camera ${camera.id} no ICE candidate or WebSocket not open`);
//         }
//       };

//       pc.current.onconnectionstatechange = () => {
//         const state = pc.current?.connectionState;
//         console.log(`Camera ${camera.id} connection state changed to: ${state}`);
//         setConnectionStatus(state || "disconnected");
//         if (state === "connected") {
//           console.log(`Camera ${camera.id} WebRTC connected successfully`);
//           retryCount.current = 0;
//         } else if (state === "failed" || state === "disconnected") {
//           setError(`WebRTC connection ${state}`);
//           setIsConnected(false);
//           console.error(`Camera ${camera.id} WebRTC connection ${state}`);
//           if (retryCount.current < maxRetries) {
//             setTimeout(() => {
//               console.log(`Camera ${camera.id} retrying connection, attempt ${retryCount.current + 1}`);
//               retryCount.current += 1;
//               connectWebRTC().then(sendOffer);
//             }, retryDelay);
//           } else {
//             setError("Max retries reached. Please check connection.");
//           }
//         }
//       };

//       pc.current.oniceconnectionstatechange = () => {
//         console.log(`Camera ${camera.id} ICE connection state: ${pc.current?.iceConnectionState}`);
//       };

//       console.log(`Camera ${camera.id} RTCPeerConnection setup completed`);
//       // Gửi offer ngay sau khi tạo PC
//       await sendOffer();
//     } catch (err) {
//       setError(err instanceof Error ? err.message : "Failed to connect");
//       setIsConnected(false);
//       console.error(`Camera ${camera.id} error initializing WebRTC:`, err);
//     } finally {
//       isConnecting.current = false;
//     }
//   };

//   const sendOffer = async () => {
//     if (!pc.current || hasSentOffer.current || !ws || ws.readyState !== WebSocket.OPEN) {
//       console.log(`Camera ${camera.id} cannot send offer: PC or WebSocket not ready`);
//       return;
//     }

//     try {
//       if (pc.current.signalingState !== "stable") {
//         console.warn(
//           `Camera ${camera.id} cannot create offer, signaling state: ${pc.current.signalingState}`
//         );
//         return;
//       }
//       console.log(`Camera ${camera.id} creating WebRTC offer`);
//       const offer = await pc.current.createOffer();
//       console.log(`Camera ${camera.id} setting local description with offer`);
//       await pc.current.setLocalDescription(offer);
//       console.log(`Camera ${camera.id} sending offer to webrtc-server`);
//       ws.send(
//         JSON.stringify({
//           type: "offer",
//           sdp: offer.sdp,
//           clientId: clientId.current,
//           target: "webrtc-server",
//           cameraId: camera.id,
//         })
//       );
//       console.log(`Camera ${camera.id} offer sent successfully`);
//       hasSentOffer.current = true;

//       // Nếu có answer đang chờ, xử lý ngay
//       if (pendingAnswer.current) {
//         console.log(`Camera ${camera.id} processing pending answer`);
//         await pc.current.setRemoteDescription(
//           new RTCSessionDescription({ type: "answer", sdp: pendingAnswer.current })
//         );
//         console.log(`Camera ${camera.id} set remote description successfully (pending answer)`);
//         pendingAnswer.current = null;
//       }
//     } catch (err) {
//       console.error(`Camera ${camera.id} failed to create or send offer:`, err);
//       setError("Failed to create WebRTC offer");
//     }
//   };

//   const onMessage = useCallback(
//     (message: WebRTCMessage) => {
//       console.log(`Camera ${camera.id} received message:`, message);
//       if (message.type === "id") {
//         clientId.current = message.id;
//         console.log(`Camera ${camera.id} assigned client ID: ${clientId.current}`);
//         if (ws && ws.readyState === WebSocket.OPEN) {
//           console.log(`Camera ${camera.id} WebSocket ready, initiating WebRTC connection`);
//           connectWebRTC();
//         }
//       } else if (message.type === "ws_ready" && clientId.current) {
//         if (ws && ws.readyState === WebSocket.OPEN) {
//           console.log(`Camera ${camera.id} WebSocket ready, initiating WebRTC connection`);
//           connectWebRTC();
//         } else {
//           console.log(`Camera ${camera.id} WebSocket still not ready`);
//         }
//       } else if (message.type === "answer" && message.clientId === clientId.current) {
//         console.log(`Camera ${camera.id} received answer from webrtc-server:`, message.sdp);
//         if (message.sdp && pc.current) {
//           if (pc.current.signalingState === "have-local-offer") {
//             pc.current
//               .setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: message.sdp }))
//               .then(() => {
//                 console.log(`Camera ${camera.id} set remote description successfully`);
//               })
//               .catch((err) => {
//                 console.error(`Camera ${camera.id} failed to set remote description:`, err);
//                 setError("Failed to process WebRTC answer");
//               });
//           } else if (pc.current.signalingState === "stable") {
//             console.warn(`Camera ${camera.id} received answer in stable state, queuing answer`);
//             pendingAnswer.current = message.sdp;
//             hasSentOffer.current = false;
//             sendOffer();
//           } else {
//             console.error(`Camera ${camera.id} cannot set remote description, invalid state: ${pc.current.signalingState}`);
//             setError("Invalid WebRTC state for answer");
//           }
//         } else {
//           console.error(`Camera ${camera.id} received invalid answer (no SDP or no PC)`);
//           setError("Invalid WebRTC answer");
//         }
//       } else if (message.type === "candidate" && message.clientId === clientId.current) {
//         console.log(`Camera ${camera.id} received ICE candidate:`, message.candidate);
//         if (pc.current && pc.current.remoteDescription) {
//           pc.current
//             .addIceCandidate(new RTCIceCandidate(message.candidate))
//             .then(() => {
//               console.log(`Camera ${camera.id} added ICE candidate successfully`);
//             })
//             .catch((err) => {
//               console.error(`Camera ${camera.id} failed to add ICE candidate:`, err);
//             });
//         } else {
//           console.warn(`Camera ${camera.id} cannot add ICE candidate: remoteDescription not set or PC not ready`);
//         }
//         } else if (message.type === "error") { // Bỏ điều kiện clientId để đảm bảo xử lý mọi lỗi
//           console.error(`Camera ${camera.id} received error: ${message.message}`);
//           setError(message.message);
//           setIsConnected(false);
//           setConnectionStatus("disconnected");
//           if (retryCount.current < maxRetries && ws && ws.readyState === WebSocket.OPEN) {
//             setTimeout(() => {
//               console.log(`Camera ${camera.id} retrying connection after error, attempt ${retryCount.current + 1}`);
//               retryCount.current += 1;
//               hasSentOffer.current = false;
//               connectWebRTC();
//             }, retryDelay);
//           } else {
//             setError("Max retries reached or WebSocket closed. Please check connection.");
//           }
//         }
//       },
//     [camera.id, ws]
//   );

//   const onError = useCallback(
//     (error: Event) => {
//       setError("WebSocket error occurred");
//       setIsConnected(false);
//       console.error(`WebSocket error for camera ${camera.id}:`, error);
//       if (retryCount.current < maxRetries) {
//         setTimeout(() => {
//           console.log(`Camera ${camera.id} retrying WebSocket connection, attempt ${retryCount.current + 1}`);
//           retryCount.current += 1;
//           connectWebRTC();
//         }, retryDelay);
//       }
//     },
//     [camera.id]
//   );

//   const onClose = useCallback(() => {
//     setError("WebSocket connection closed");
//     setIsConnected(false);
//     setConnectionStatus("disconnected");
//     console.log(`WebSocket closed for camera ${camera.id}`);
//   }, [camera.id]);

//   const captureScreenshot = () => {
//     if (videoRef.current) {
//       const canvas = document.createElement("canvas");
//       canvas.width = videoRef.current.videoWidth;
//       canvas.height = videoRef.current.videoHeight;
//       const ctx = canvas.getContext("2d");
//       if (ctx) {
//         ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
//         const dataUrl = canvas.toDataURL("image/png");
//         const link = document.createElement("a");
//         link.href = dataUrl;
//         link.download = `camera_${camera.id}_screenshot.png`;
//         link.click();
//         console.log(`Camera ${camera.id} screenshot captured`);
//       }
//     }
//   };

//   const toggleVideo = () => {
//     if (videoRef.current) {
//       if (isVideoPlaying) {
//         videoRef.current.pause();
//         console.log(`Camera ${camera.id} video paused`);
//       } else {
//         videoRef.current.play().catch((err) => {
//           console.error(`Camera ${camera.id} failed to play video:`, err);
//           setError("Failed to play video stream");
//         });
//         console.log(`Camera ${camera.id} video resumed`);
//       }
//       setIsVideoPlaying(!isVideoPlaying);
//     }
//   };

//   useEffect(() => {
//     if (stream && videoRef.current) {
//       console.log(`Camera ${camera.id} attaching MediaStream to video element`);
//       videoRef.current.srcObject = stream;
//       videoRef.current.play().catch((err) => {
//         console.error(`Camera ${camera.id} failed to play video:`, err);
//         setError("Failed to play video stream");
//       });
//     }
//   }, [stream, camera.id]);

//   useEffect(() => {
//     console.log(`Camera ${camera.id} mounting, WebSocket state: ${ws ? ws.readyState : "null"}`);
//     const unregister = registerCallback(camera.id, { onMessage, onError, onClose });
//     hasSentOffer.current = false; // Reset hasSentOffer
//     isConnecting.current = false; // Reset isConnecting
//     retryCount.current = 0; // Reset retryCount
//     pendingAnswer.current = null; // Reset pendingAnswer
//     return () => {
//       console.log(`Camera ${camera.id} unmounting`);
//       unregister();
//       if (pc.current) {
//         pc.current.close();
//         console.log(`Camera ${camera.id} RTCPeerConnection closed`);
//         pc.current = null;
//       }
//       setIsConnected(false);
//       setStream(null);
//       setConnectionStatus("disconnected");
//       console.log(`Camera ${camera.id} cleanup completed`);
//     };
//   }, [camera.id, ws, registerCallback, onMessage, onError, onClose]);

//   return (
//     <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
//       <video
//         ref={videoRef}
//         autoPlay
//         playsInline
//         muted
//         className={`w-full h-full object-cover ${isConnected ? "block" : "hidden"}`}
//         onError={(e) => {
//           console.error(`Camera ${camera.id} video error:`, e);
//           setError("Video stream error");
//         }}
//       />
//       {!isConnected && (
//         <div className="absolute inset-0 flex items-center justify-center text-white">
//           {error ? (
//             <div className="text-center">
//               <p className="text-red-500 mb-2">{error}</p>
//               <button
//                 onClick={connectWebRTC}
//                 className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
//               >
//                 <RefreshCw className="w-4 h-4" />
//                 Reconnect
//               </button>
//             </div>
//           ) : (
//             <p>Connecting to camera...</p>
//           )}
//         </div>
//       )}
//       {isConnected && (
//         <div className="absolute bottom-2 right-2 flex gap-2">
//           <button
//             onClick={toggleVideo}
//             className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
//             title={isVideoPlaying ? "Pause Video" : "Play Video"}
//           >
//             {isVideoPlaying ? <VideoOff className="w-4 h-4" /> : <Video className="w-4 h-4" />}
//           </button>
//           <button
//             onClick={captureScreenshot}
//             className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
//             title="Capture Screenshot"
//           >
//             <CameraIcon className="w-4 h-4" />
//           </button>
//           <button
//             onClick={connectWebRTC}
//             className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
//             title="Reconnect"
//           >
//             <RefreshCw className="w-4 h-4" />
//           </button>
//         </div>
//       )}
//       <div className="absolute top-2 left-2 bg-black/50 text-white px-2 py-1 rounded">{camera.name}</div>
//       <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded">
//         {isConnected ? (
//           <span className="text-green-500">Connected</span>
//         ) : (
//           <span className="text-red-500">Disconnected</span>
//         )}
//       </div>
//       <div className="absolute bottom-2 left-2 bg-black/50 text-white px-2 py-1 rounded text-sm">
//         Status: {connectionStatus}
//       </div>
//     </div>
//   );
// });



"use client";
import React from "react";
import { useEffect, useRef, useState, useCallback } from "react";
import { RefreshCw, Camera as CameraIcon, Video, VideoOff } from "lucide-react";
import { Camera, WebRTCMessage } from "../lib/types";

interface CameraWithVisible extends Camera {
  visible: boolean;
}

interface CameraCardCallbacks {
  onMessage: (message: WebRTCMessage) => void;
  onError: (error: Event) => void;
  onClose: () => void;
}

interface CameraCardProps {
  camera: CameraWithVisible;
  ws: WebSocket | null;
  registerCallback: (cameraId: string, callback: CameraCardCallbacks) => () => void;
}

export const CameraCard = React.memo(function CameraCard({ camera, ws, registerCallback }: CameraCardProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isVideoPlaying, setIsVideoPlaying] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const pc = useRef<RTCPeerConnection | null>(null);
  const clientId = useRef<string | null>(null);
  const hasSentOffer = useRef(false);
  const isConnecting = useRef(false);
  const retryCount = useRef(0);
  const maxRetries = 3;
  const retryDelay = 5000; // 5 giây
  const pendingAnswer = useRef<string | null>(null); // Lưu answer tạm thời nếu cần

  const connectWebRTC = async () => {
    console.log(
      `Camera ${camera.id} visibility: ${camera.visible}, WebSocket: ${
        ws ? ws.readyState : "null"
      }, isConnecting: ${isConnecting.current}`
    );
    if (!camera.visible || !ws || ws.readyState !== WebSocket.OPEN || isConnecting.current) {
      console.log(`Camera ${camera.id} not visible, WebSocket not available, or already connecting`);
      return;
    }

    isConnecting.current = true;

    try {
      console.log(`Camera ${camera.id} initializing RTCPeerConnection`);
      pc.current = new RTCPeerConnection({
        iceServers: [
          { urls: "stun:stun.l.google.com:19302" },
          {
            urls: "turn:openrelay.metered.ca:80",
            username: "openrelayproject",
            credential: "openrelayproject",
          },
          {
            urls: "turn:openrelay.metered.ca:443",
            username: "openrelayproject",
            credential: "openrelayproject",
          },
        ],
      });

      console.log(`Camera ${camera.id} adding video transceiver`);
      pc.current.addTransceiver("video", { direction: "recvonly" });

      pc.current.ontrack = (event) => {
        console.log(`Camera ${camera.id} received video track:`, event.streams[0]);
        setStream(event.streams[0]);
        setIsConnected(true);
        setConnectionStatus("connected");
        console.log(`Camera ${camera.id} video stream saved to state`);
      };

      pc.current.onicecandidate = (event) => {
        if (event.candidate && ws.readyState === WebSocket.OPEN) {
          console.log(`Camera ${camera.id} sending ICE candidate:`, event.candidate.toJSON());
          ws.send(
            JSON.stringify({
              type: "candidate",
              candidate: event.candidate.toJSON(),
              target: "webrtc-server",
              cameraId: camera.id,
              clientId: clientId.current,
            })
          );
          console.log(`Camera ${camera.id} ICE candidate sent successfully`);
        } else {
          console.log(`Camera ${camera.id} no ICE candidate or WebSocket not open`);
        }
      };

      pc.current.onconnectionstatechange = () => {
        const state = pc.current?.connectionState;
        console.log(`Camera ${camera.id} connection state changed to: ${state}`);
        setConnectionStatus(state || "disconnected");
        if (state === "connected") {
          console.log(`Camera ${camera.id} WebRTC connected successfully`);
          retryCount.current = 0;
        } else if (state === "failed" || state === "disconnected") {
          setError(`WebRTC connection ${state}`);
          setIsConnected(false);
          console.error(`Camera ${camera.id} WebRTC connection ${state}`);
          if (retryCount.current < maxRetries) {
            setTimeout(() => {
              console.log(`Camera ${camera.id} retrying connection, attempt ${retryCount.current + 1}`);
              retryCount.current += 1;
              connectWebRTC().then(sendOffer);
            }, retryDelay);
          } else {
            setError("Max retries reached. Please check connection.");
          }
        }
      };

      pc.current.oniceconnectionstatechange = () => {
        console.log(`Camera ${camera.id} ICE connection state: ${pc.current?.iceConnectionState}`);
      };

      console.log(`Camera ${camera.id} RTCPeerConnection setup completed`);
      // Gửi offer ngay sau khi tạo PC
      await sendOffer();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
      setIsConnected(false);
      console.error(`Camera ${camera.id} error initializing WebRTC:`, err);
    } finally {
      isConnecting.current = false;
    }
  };

  const sendOffer = async () => {
    if (!pc.current || hasSentOffer.current || !ws || ws.readyState !== WebSocket.OPEN) {
      console.log(`Camera ${camera.id} cannot send offer: PC or WebSocket not ready`);
      return;
    }

    try {
      if (pc.current.signalingState !== "stable") {
        console.warn(
          `Camera ${camera.id} cannot create offer, signaling state: ${pc.current.signalingState}`
        );
        return;
      }
      console.log(`Camera ${camera.id} creating WebRTC offer`);
      const offer = await pc.current.createOffer();
      console.log(`Camera ${camera.id} setting local description with offer`);
      await pc.current.setLocalDescription(offer);
      console.log(`Camera ${camera.id} sending offer to webrtc-server`);
      ws.send(
        JSON.stringify({
          type: "offer",
          sdp: offer.sdp,
          clientId: clientId.current,
          target: "webrtc-server",
          cameraId: camera.id,
        })
      );
      console.log(`Camera ${camera.id} offer sent successfully`);
      hasSentOffer.current = true;

      // Nếu có answer đang chờ, xử lý ngay
      if (pendingAnswer.current) {
        console.log(`Camera ${camera.id} processing pending answer`);
        await pc.current.setRemoteDescription(
          new RTCSessionDescription({ type: "answer", sdp: pendingAnswer.current })
        );
        console.log(`Camera ${camera.id} set remote description successfully (pending answer)`);
        pendingAnswer.current = null;
      }
    } catch (err) {
      console.error(`Camera ${camera.id} failed to create or send offer:`, err);
      setError("Failed to create WebRTC offer");
    }
  };

  const onMessage = useCallback(
    (message: WebRTCMessage) => {
      console.log(`Camera ${camera.id} received message:`, message);
      if (message.type === "id") {
        clientId.current = message.id;
        console.log(`Camera ${camera.id} assigned client ID: ${clientId.current}`);
        if (ws && ws.readyState === WebSocket.OPEN) {
          console.log(`Camera ${camera.id} WebSocket ready, initiating WebRTC connection`);
          connectWebRTC();
        }
      } else if (message.type === "ws_ready" && clientId.current) {
        if (ws && ws.readyState === WebSocket.OPEN) {
          console.log(`Camera ${camera.id} WebSocket ready, initiating WebRTC connection`);
          connectWebRTC();
        } else {
          console.log(`Camera ${camera.id} WebSocket still not ready`);
        }
      } else if (message.type === "answer" && message.clientId === clientId.current) {
        console.log(`Camera ${camera.id} received answer from webrtc-server:`, message.sdp);
        if (message.sdp && pc.current) {
          if (pc.current.signalingState === "have-local-offer") {
            pc.current
              .setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: message.sdp }))
              .then(() => {
                console.log(`Camera ${camera.id} set remote description successfully`);
              })
              .catch((err) => {
                console.error(`Camera ${camera.id} failed to set remote description:`, err);
                setError("Failed to process WebRTC answer");
              });
          } else if (pc.current.signalingState === "stable") {
            console.warn(`Camera ${camera.id} received answer in stable state, queuing answer`);
            pendingAnswer.current = message.sdp;
            // Thử gửi lại offer
            hasSentOffer.current = false;
            sendOffer();
          } else {
            console.error(
              `Camera ${camera.id} cannot set remote description, invalid state: ${pc.current.signalingState}`
            );
            setError("Invalid WebRTC state for answer");
          }
        } else {
          console.error(`Camera ${camera.id} received invalid answer (no SDP or no PC)`);
          setError("Invalid WebRTC answer");
        }
      } else if (message.type === "candidate" && message.clientId === clientId.current) {
        console.log(`Camera ${camera.id} received ICE candidate:`, message.candidate);
        if (pc.current && pc.current.remoteDescription) {
          pc.current
            .addIceCandidate(new RTCIceCandidate(message.candidate))
            .then(() => {
              console.log(`Camera ${camera.id} added ICE candidate successfully`);
            })
            .catch((err) => {
              console.error(`Camera ${camera.id} failed to add ICE candidate:`, err);
            });
        } else {
          console.warn(
            `Camera ${camera.id} cannot add ICE candidate: remoteDescription not set or PC not ready`
          );
        }
      }
    },
    [camera.id, ws]
  );

  const onError = useCallback(
    (error: Event) => {
      setError("WebSocket error occurred");
      setIsConnected(false);
      console.error(`WebSocket error for camera ${camera.id}:`, error);
      if (retryCount.current < maxRetries) {
        setTimeout(() => {
          console.log(`Camera ${camera.id} retrying WebSocket connection, attempt ${retryCount.current + 1}`);
          retryCount.current += 1;
          connectWebRTC();
        }, retryDelay);
      }
    },
    [camera.id]
  );

  const onClose = useCallback(() => {
    setError("WebSocket connection closed");
    setIsConnected(false);
    setConnectionStatus("disconnected");
    console.log(`WebSocket closed for camera ${camera.id}`);
  }, [camera.id]);

  const captureScreenshot = () => {
    if (videoRef.current) {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.href = dataUrl;
        link.download = `camera_${camera.id}_screenshot.png`;
        link.click();
        console.log(`Camera ${camera.id} screenshot captured`);
      }
    }
  };

  const toggleVideo = () => {
    if (videoRef.current) {
      if (isVideoPlaying) {
        videoRef.current.pause();
        console.log(`Camera ${camera.id} video paused`);
      } else {
        videoRef.current.play().catch((err) => {
          console.error(`Camera ${camera.id} failed to play video:`, err);
          setError("Failed to play video stream");
        });
        console.log(`Camera ${camera.id} video resumed`);
      }
      setIsVideoPlaying(!isVideoPlaying);
    }
  };

  useEffect(() => {
    if (stream && videoRef.current) {
      console.log(`Camera ${camera.id} attaching MediaStream to video element`);
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch((err) => {
        console.error(`Camera ${camera.id} failed to play video:`, err);
        setError("Failed to play video stream");
      });
    }
  }, [stream, camera.id]);

  useEffect(() => {
    console.log(`Camera ${camera.id} mounting, WebSocket state: ${ws ? ws.readyState : "null"}`);
    const unregister = registerCallback(camera.id, { onMessage, onError, onClose });
    return () => {
      console.log(`Camera ${camera.id} unmounting`);
      unregister();
      if (pc.current) {
        pc.current.close();
        console.log(`Camera ${camera.id} RTCPeerConnection closed`);
        pc.current = null;
      }
      setIsConnected(false);
      setStream(null);
      setConnectionStatus("disconnected");
      hasSentOffer.current = false;
      retryCount.current = 0;
      pendingAnswer.current = null;
      console.log(`Camera ${camera.id} cleanup completed`);
    };
  }, [camera.id, camera.visible, ws, registerCallback, onMessage, onError, onClose]);

  return (
    <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full h-full object-cover ${isConnected ? "block" : "hidden"}`}
        onError={(e) => {
          console.error(`Camera ${camera.id} video error:`, e);
          setError("Video stream error");
        }}
      />
      {!isConnected && (
        <div className="absolute inset-0 flex items-center justify-center text-white">
          {error ? (
            <div className="text-center">
              <p className="text-red-500 mb-2">{error}</p>
              <button
                onClick={connectWebRTC}
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
      {isConnected && (
        <div className="absolute bottom-2 right-2 flex gap-2">
          <button
            onClick={toggleVideo}
            className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
            title={isVideoPlaying ? "Pause Video" : "Play Video"}
          >
            {isVideoPlaying ? <VideoOff className="w-4 h-4" /> : <Video className="w-4 h-4" />}
          </button>
          <button
            onClick={captureScreenshot}
            className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
            title="Capture Screenshot"
          >
            <CameraIcon className="w-4 h-4" />
          </button>
          <button
            onClick={connectWebRTC}
            className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
            title="Reconnect"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      )}
      <div className="absolute top-2 left-2 bg-black/50 text-white px-2 py-1 rounded">{camera.name}</div>
      <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded">
        {isConnected ? (
          <span className="text-green-500">Connected</span>
        ) : (
          <span className="text-red-500">Disconnected</span>
        )}
      </div>
      <div className="absolute bottom-2 left-2 bg-black/50 text-white px-2 py-1 rounded text-sm">
        Status: {connectionStatus}
      </div>
    </div>
  );
});