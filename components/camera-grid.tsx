"use client";

import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import ReactPaginate from "react-paginate";
import { CameraCard } from "./camera-card";
import { Camera, WebRTCMessage } from "../lib/types";
import { Button } from "./ui/button";
import { useTaskStore } from "@/lib/stores/task-store";

interface CameraWithVisible extends Camera {
  visible: boolean;
}

interface CameraCardCallbacks {
  onMessage: (message: WebRTCMessage) => void;
  onError: (error: Event) => void;
  onClose: () => void;
}

export function CameraGrid() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [page, setPage] = useState(0);
  const camerasPerPage = 5;
  const [loading, setLoading] = useState(true);
  const [signalingUrl, setSignalingUrl] = useState<string>("");
  const ws = useRef<WebSocket | null>(null);
  const callbacks = useRef<Map<string, CameraCardCallbacks>>(new Map());
  const clientId = useRef<string | null>(null);
  const [postLoading, setPostLoading] = useState(false);
  const [postResult, setPostResult] = useState<string | null>(null);
  const [multiPostLoading, setMultiPostLoading] = useState<number | null>(null);
  const [multiPostResult, setMultiPostResult] = useState<string | null>(null);
  const { isAutoMode } = useTaskStore();

  const registerCallback = useCallback(
    (cameraId: string, callback: CameraCardCallbacks) => {
      console.log(`Registering callback for camera ${cameraId}`);
      callbacks.current.set(cameraId, callback);
      if (clientId.current) {
        callback.onMessage({
          type: "id",
          id: clientId.current,
          cameraId: null,
          clientId: null,
          sdp: undefined,
          candidate: null,
        });
      }
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        callback.onMessage({
          type: "ws_ready",
          id: null,
          cameraId: null,
          clientId: null,
          sdp: undefined,
          candidate: null,
        });
      }
      return () => {
        console.log(`Unregistering callback for camera ${cameraId}`);
        callbacks.current.delete(cameraId);
      };
    },
    [] 
  );

  useEffect(() => {
    async function fetchConfigAndCameras() {
      try {
        const [configResponse, camerasResponse] = await Promise.all([
          fetch("http://localhost:7000/api/config"),
          fetch("http://localhost:7000/api/cameras"),
        ]);
        const config = await configResponse.json();
        const data = await camerasResponse.json();
        console.log("Fetched config:", config);
        console.log("Fetched cameras:", data);
        setSignalingUrl(config.signaling_server_url);
        setCameras(data.cameras);

        // Khởi tạo WebSocket
        if (config.signaling_server_url) {
          console.log("Creating WebSocket with signaling URL:", config.signaling_server_url);
          ws.current = new WebSocket(config.signaling_server_url);

          ws.current.onopen = () => {
            console.log("Connected to Signaling Server");
          };

          ws.current.onmessage = (event) => {
            const data: WebRTCMessage = JSON.parse(event.data);
            console.log("Received message in CameraGrid:", data);

            if (data.type === "id") {
              clientId.current = data.id;
              console.log("Client ID assigned in CameraGrid:", clientId.current);
              callbacks.current.forEach((callback) => {
                callback.onMessage(data);
              });
            } else if (data.cameraId) {
              const callback = callbacks.current.get(data.cameraId);
              if (callback) {
                callback.onMessage(data);
              } else {
                console.warn(`No callback found for cameraId: ${data.cameraId}`);
              }
            }
          };

          ws.current.onerror = (error) => {
            console.error("WebSocket error in CameraGrid:", error);
            callbacks.current.forEach((callback) => callback.onError(error));
          };

          ws.current.onclose = () => {
            console.log("WebSocket connection closed in CameraGrid");
            clientId.current = null;
            callbacks.current.forEach((callback) => callback.onClose());
          };
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchConfigAndCameras();
  }, []);

  // Ổn định danh sách cameras
  const stableCameras = useMemo(() => cameras, [cameras.length]);

  // Log để debug cameras
  useEffect(() => {
    console.log("Cameras:", cameras);
    console.log("Stable cameras:", stableCameras);
  }, [cameras, stableCameras]);

  // Gửi ws_ready
  useEffect(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log("Notifying CameraCards of WebSocket readiness");
      callbacks.current.forEach((callback) => {
        callback.onMessage({
          type: "ws_ready",
          id: null,
          cameraId: null,
          clientId: null,
          sdp: undefined,
          candidate: null,
        });
      });
    }
  }, [ws.current?.readyState, callbacks.current.size]);

  const handlePageChange = useCallback(({ selected }: { selected: number }) => {
    setPage(selected);
  }, []);

  // Tính displayedCameras sau khi cameras sẵn sàng
  const displayedCameras = useMemo(
    () => (loading || !stableCameras.length ? [] : stableCameras.slice(page * camerasPerPage, (page + 1) * camerasPerPage)),
    [stableCameras, page, loading]
  );

  // Log để debug displayedCameras
  useEffect(() => {
    console.log("Displayed cameras:", displayedCameras);
  }, [displayedCameras]);

  const handleGridButtonClick = async () => {
    setPostLoading(true);
    setPostResult(null);
    try {
      const response = await fetch("http://192.168.1.x:7000/ics/taskOrder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "grid" }), // Bạn có thể thay đổi payload nếu cần
      });
      if (!response.ok) throw new Error("Request failed");
      setPostResult("Gửi thành công!");
    } catch (err) {
      setPostResult("Gửi thất bại!");
    } finally {
      setPostLoading(false);
    }
  };

  const handleMultiGridButtonClick = async (buttonNumber: number) => {
    setMultiPostLoading(buttonNumber);
    setMultiPostResult(null);
    try {
      const response = await fetch("http://192.168.1.x:7000/ics/taskOrder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "grid", button: buttonNumber }),
      });
      if (!response.ok) throw new Error("Request failed");
      setMultiPostResult(`Gửi thành công cho nút ${buttonNumber}!`);
    } catch (err) {
      setMultiPostResult(`Gửi thất bại cho nút ${buttonNumber}!`);
    } finally {
      setMultiPostLoading(null);
    }
  };

  if (loading) return <div>Loading cameras...</div>;

  if (!stableCameras.length) return <div>No cameras available</div>;

  return (
    <div className=" space-y-4 pt-[10px] ">
        {/* <img
          src="/img_khung.png"
          alt="Background Image"
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-51%, -40%)',
            width: '88vw',
            height: '50vh',
            // objectFit: 'cover',
            zIndex: 1,
            opacity: 0.75
          }}
        /> */}
      <div className=" rounded-lg p-4">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-3">
          {displayedCameras.map((camera) => (
            <CameraCard
              key={camera.id}
              camera={{ ...camera, visible: true }}
              ws={ws.current}
              registerCallback={registerCallback}
            />
          ))}
        </div>
        <ReactPaginate
          pageCount={Math.ceil(stableCameras.length / camerasPerPage)}
          onPageChange={handlePageChange}
          containerClassName="pagination flex justify-center mt-4 pt-15"
          pageClassName="mx-1"
          activeClassName="font-bold text-blue-500"
          pageLinkClassName="px-3 py-1 border rounded"
        />
      </div>
      {/* Nút 5x2 */}
      {!isAutoMode && (
        <div className="grid grid-cols-5 gap-2 w-fit mx-auto mt-6">
          {Array.from({ length: 10 }, (_, i) => (
            <Button
              key={i + 1}
              onClick={() => handleMultiGridButtonClick(i + 1)}
              disabled={multiPostLoading === i + 1}
              className="w-16"
            >
              {multiPostLoading === i + 1 ? "Đang gửi..." : `Nút ${i + 1}`}
            </Button>
          ))}
        </div>
      )}
      {multiPostResult && (
        <div className={`text-center mt-2 ${multiPostResult.includes("thành công") ? "text-green-600" : "text-red-600"}`}>
          {multiPostResult}
        </div>
      )}
    </div>
  );
}