"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { RefreshCw } from "lucide-react";
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

export function CameraCard({ camera, ws, registerCallback }: CameraCardProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pc = useRef<RTCPeerConnection | null>(null);
  const clientId = useRef<string | null>(null);
  const hasSentOffer = useRef(false);
  const isConnecting = useRef(false);

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
      console.log(`Camera ${camera.id} connecting WebRTC, WebSocket state: ${ws.readyState}`);
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

      pc.current.addTransceiver("video", { direction: "recvonly" });

      pc.current.ontrack = (event) => {
        if (videoRef.current) {
          videoRef.current.srcObject = event.streams[0];
          setIsConnected(true);
          console.log(`Camera ${camera.id} received video track`);
        }
      };

      pc.current.onicecandidate = (event) => {
        if (event.candidate && ws.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: "candidate",
              candidate: event.candidate.toJSON(),
              target: "webrtc-server",
              cameraId: camera.id,
              clientId: clientId.current,
            })
          );
          console.log(`Camera ${camera.id} sent ICE candidate`);
        }
      };

      pc.current.onconnectionstatechange = () => {
        console.log(`Camera ${camera.id} connection state: ${pc.current?.connectionState}`);
        if (pc.current?.connectionState === "failed") {
          setError("WebRTC connection failed");
          setIsConnected(false);
        }
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
      setIsConnected(false);
      console.error(`Error connecting WebRTC for camera ${camera.id}:`, err);
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
      console.log(`Camera ${camera.id} creating offer`);
      const offer = await pc.current.createOffer();
      await pc.current.setLocalDescription(offer);
      ws.send(
        JSON.stringify({
          type: "offer",
          sdp: offer.sdp,
          clientId: clientId.current,
          target: "webrtc-server",
          cameraId: camera.id,
        })
      );
      console.log(`Camera ${camera.id} sent offer`);
      hasSentOffer.current = true;
    } catch (err) {
      console.error(`Camera ${camera.id} failed to create offer:`, err);
      setError("Failed to create WebRTC offer");
    }
  };

  const onMessage = useCallback(
    (message: WebRTCMessage) => {
      console.log(`Camera ${camera.id} received message:`, message);
      if (message.type === "id") {
        clientId.current = message.id;
        console.log(`Camera ${camera.id} Client ID:`, clientId.current);
        if (ws && ws.readyState === WebSocket.OPEN) {
          console.log(`Camera ${camera.id} WebSocket ready on id message, connecting WebRTC`);
          connectWebRTC().then(() => {
            sendOffer();
          });
        }
      } else if (message.type === "ws_ready" && clientId.current) {
        if (ws && ws.readyState === WebSocket.OPEN) {
          console.log(`Camera ${camera.id} WebSocket ready, connecting WebRTC`);
          connectWebRTC().then(() => {
            sendOffer();
          });
        } else {
          console.log(`Camera ${camera.id} WebSocket still not ready`);
        }
      } else if (message.type === "answer" && message.clientId === clientId.current) {
        console.log(`Camera ${camera.id} processing answer:`, message.sdp);
        if (message.sdp) {
          pc.current?.setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: message.sdp }));
          console.log(`Camera ${camera.id} received answer`);
        } else {
          console.error(`Camera ${camera.id} received answer with undefined sdp`);
          setError("Invalid WebRTC answer");
        }
      } else if (message.type === "candidate" && message.clientId === clientId.current) {
        console.log(`Camera ${camera.id} processing ICE candidate:`, message.candidate);
        pc.current?.addIceCandidate(new RTCIceCandidate(message.candidate));
        console.log(`Camera ${camera.id} added ICE candidate`);
      }
    },
    [camera.id, ws]
  );

  const onError = useCallback(
    (error: Event) => {
      setError("WebSocket error occurred");
      setIsConnected(false);
      console.error(`WebSocket error for camera ${camera.id}:`, error);
    },
    [camera.id]
  );

  const onClose = useCallback(() => {
    setError("WebSocket connection closed");
    setIsConnected(false);
    console.log(`WebSocket closed for camera ${camera.id}`);
  }, [camera.id]);

  useEffect(() => {
    console.log(`Camera ${camera.id} WebSocket state: ${ws ? ws.readyState : "null"}`);
    console.log(`Camera ${camera.id} mounting`);
    const unregister = registerCallback(camera.id, { onMessage, onError, onClose });
    return () => {
      console.log(`Camera ${camera.id} unmounting`);
      unregister();
      if (pc.current) {
        pc.current.close();
        pc.current = null;
      }
      setIsConnected(false);
      hasSentOffer.current = false;
      console.log(`Camera ${camera.id} cleanup`);
    };
  }, [camera.id, camera.visible, ws, registerCallback, onMessage, onError, onClose]);

  return (
    <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
      {isConnected ? (
        <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
      ) : (
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
      <div className="absolute top-2 left-2 bg-black/50 text-white px-2 py-1 rounded">{camera.name}</div>
      <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded">
        {isConnected ? (
          <span className="text-green-500">Connected</span>
        ) : (
          <span className="text-red-500">Disconnected</span>
        )}
      </div>
    </div>
  );
}