import cv2
import socket
import threading
import time
import numpy as np

class RTSPServer:
    def __init__(self, host='0.0.0.0', port=8554, stream_path='/stream1'):
        self.host = host
        self.port = port
        self.stream_path = stream_path
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = []
        self.cap = cv2.VideoCapture(0)  # Mở camera mặc định
        if not self.cap.isOpened():
            raise Exception("Không thể mở camera")
        
        # Cài đặt codec H.264 (dùng MJPEG để đơn giản hóa, vì H.264 cần thư viện bổ sung)
        self.frame = None
        self.running = True

    def start(self):
        print(f"RTSP Server chạy tại rtsp://{self.host}:{self.port}{self.stream_path}")
        # Luồng capture video
        threading.Thread(target=self.capture_video, daemon=True).start()
        # Luồng xử lý client
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def capture_video(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Không thể lấy frame từ camera")
                break
            # Mã hóa frame thành JPEG (đơn giản, thay vì H.264)
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                self.frame = buffer.tobytes()
            time.sleep(0.033)  # ~30 FPS

    def accept_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"Kết nối từ {addr}")
                client_handler = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, addr), 
                    daemon=True
                )
                client_handler.start()
                self.clients.append(client_socket)
            except Exception as e:
                print(f"Lỗi khi chấp nhận client: {e}")
                break

    def handle_client(self, client_socket, addr):
        try:
            # Đọc yêu cầu RTSP
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                return
            
            # Xử lý yêu cầu RTSP đơn giản (chỉ hỗ trợ DESCRIBE, SETUP, PLAY)
            if 'DESCRIBE' in request:
                response = (
                    f"RTSP/1.0 200 OK\r\n"
                    f"CSeq: {self.get_cseq(request)}\r\n"
                    f"Content-Type: application/sdp\r\n"
                    f"Content-Length: 156\r\n\r\n"
                    f"v=0\r\n"
                    f"m=video 0 RTP/AVP 26\r\n"  # 26 là payload type cho MJPEG
                    f"a=rtpmap:26 JPEG/90000\r\n"
                    f"a=control:stream1\r\n"
                )
                client_socket.send(response.encode('utf-8'))
            
            elif 'SETUP' in request:
                response = (
                    f"RTSP/1.0 200 OK\r\n"
                    f"CSeq: {self.get_cseq(request)}\r\n"
                    f"Transport: RTP/AVP;unicast;client_port=5000-5001\r\n"
                    f"Session: 12345678\r\n\r\n"
                )
                client_socket.send(response.encode('utf-8'))
            
            elif 'PLAY' in request:
                response = (
                    f"RTSP/1.0 200 OK\r\n"
                    f"CSeq: {self.get_cseq(request)}\r\n"
                    f"Session: 12345678\r\n"
                    f"RTP-Info: url=rtsp://{self.host}:{self.port}{self.stream_path};seq=0\r\n\r\n"
                )
                client_socket.send(response.encode('utf-8'))
                
                # Bắt đầu gửi frame video qua RTP (giả lập)
                self.send_rtp_stream(client_socket, addr)
            
        except Exception as e:
            print(f"Lỗi khi xử lý client {addr}: {e}")
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)

    def get_cseq(self, request):
        for line in request.split('\n'):
            if line.startswith('CSeq:'):
                return line.split(':')[1].strip()
        return '1'

    def send_rtp_stream(self, client_socket, addr):
        # Tạo socket UDP để gửi RTP (giả lập)
        rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_port = 5000  # Cổng client mặc định (lấy từ SETUP)
        
        sequence_number = 0
        timestamp = 0
        ssrc = 0x12345678  # Identifier ngẫu nhiên

        while self.running and client_socket in self.clients:
            if self.frame is None:
                time.sleep(0.1)
                continue

            # Tạo header RTP đơn giản
            rtp_header = bytearray(12)
            rtp_header[0] = 0x80  # Phiên bản RTP
            rtp_header[1] = 26    # Payload type (MJPEG)
            rtp_header[2:4] = sequence_number.to_bytes(2, 'big')
            rtp_header[4:8] = timestamp.to_bytes(4, 'big')
            rtp_header[8:12] = ssrc.to_bytes(4, 'big')

            # Gửi frame qua UDP
            try:
                rtp_socket.sendto(rtp_header + self.frame, (addr[0], client_port))
            except:
                break

            sequence_number += 1
            timestamp += 3000  # Tăng timestamp (90000 Hz clock, ~30 FPS)
            time.sleep(0.033)  # ~30 FPS

        rtp_socket.close()

    def stop(self):
        self.running = False
        self.cap.release()
        for client in self.clients:
            client.close()
        self.server_socket.close()

def main():
    server = RTSPServer(host='192.168.1.188', port=8554, stream_path='/stream1')
    try:
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nĐang tắt server...")
        server.stop()

if __name__ == '__main__':
    main()
