"use client"

import React, { useEffect, useState, useRef } from 'react';
import { useTaskStore } from "@/lib/stores/task-store";
import styled from 'styled-components';

interface AppBackgroundProps {
  children: React.ReactNode;
}

export function AppBackground({ children }: AppBackgroundProps) {
  const { isAutoMode } = useTaskStore();
  const [hasActivated, setHasActivated] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  
  useEffect(() => {
    // Tạo container cho các hiệu ứng holographic
    if (!document.getElementById('holo-effects-container')) {
      const holoContainer = document.createElement('div');
      holoContainer.id = 'holo-effects-container';
      holoContainer.style.position = 'fixed';
      holoContainer.style.top = '0';
      holoContainer.style.left = '0';
      holoContainer.style.width = '100%';
      holoContainer.style.height = '100%';
      holoContainer.style.pointerEvents = 'none';
      holoContainer.style.zIndex = '-1';
      document.body.appendChild(holoContainer);
    }

    if (isAutoMode) {
      // Đánh dấu rằng đã kích hoạt chế độ auto
      setHasActivated(true);
      
      // Thêm class cho body
      document.body.classList.add('auto-mode');
      document.body.classList.remove('bg-black');
      
      // Thay đổi màu nền của header
      const headerEl = document.querySelector('header');
      if (headerEl) {
        headerEl.classList.add('auto-mode-header');
      }
      
      // Thêm css cho holographic effects
      if (!document.getElementById('holo-animation-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'holo-animation-styles';
        styleEl.textContent = `
          body.auto-mode {
            background-color: rgba(8, 208, 140, 0.3);
            transition: background-color 0.5s ease;
            position: relative;
          }
          
          .auto-mode-header {
            background-color: rgba(8, 208, 140, 0.3) !important;
            border-bottom-color: rgba(8, 208, 140, 0.3) !important;
            transition: background-color 0.5s ease, border-color 0.5s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 
              0 0 10px rgba(8, 208, 140, 0.5),
              inset 0 0 15px rgba(8, 208, 140, 0.3);
          }
          
          .auto-mode-header nav a.bg-primary {
            background-color: rgba(8, 208, 140, 0.8) !important;
          }
          
          .auto-mode-header::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 200%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(8, 208, 140, 0.8), transparent);
            animation: scan-on 2s infinite;
          }

          body.auto-mode .sidebar {
            border-right-color: rgba(8, 208, 140, 0.7) !important;
            background-color: rgba(8, 208, 140, 0.2) !important;
            box-shadow: 
              0 0 10px rgba(8, 208, 140, 0.3),
              inset 0 0 15px rgba(8, 208, 140, 0.2);
          }
          
          body.auto-mode button,
          body.auto-mode .button,
          body.auto-mode [role="button"] {
            transition: all 0.3s ease;
          }

          body.auto-mode button:hover,
          body.auto-mode .button:hover,
          body.auto-mode [role="button"]:hover {
            box-shadow: 0 0 10px rgba(8, 208, 140, 0.7);
          }

          body.auto-mode input,
          body.auto-mode select,
          body.auto-mode textarea {
            border-color: rgba(8, 208, 140, 0.5) !important;
            transition: all 0.3s ease;
          }

          body.auto-mode input:focus,
          body.auto-mode select:focus,
          body.auto-mode textarea:focus {
            box-shadow: 0 0 5px rgba(8, 208, 140, 0.7) !important;
            border-color: rgba(8, 208, 140, 0.8) !important;
          }
          
          .corner-accent {
            position: fixed;
            width: 80px;
            height: 80px;
            border-style: solid;
            border-width: 3px;
            border-color: rgba(8, 208, 140, 0);
            transition: all 0.6s ease;
            z-index: 9990;
            pointer-events: none;
            opacity: 0;
          }

          body.auto-mode .corner-accent {
            opacity: 0.7;
            border-color: rgba(8, 208, 140, 0.7);
          }
          
          
          @keyframes scan-on {
            0% {
              left: -100%;
              opacity: 1;
            }
            100% {
              left: 100%;
              opacity: 1;
            }
          }
          
          @keyframes scan-off {
            0% {
              left: -100%;
              opacity: 0.3;
            }
            100% {
              left: 100%;
              opacity: 0.3;
            }
          }
          
          .grid-plane {
            position: fixed;
            width: 200%;
            height: 200%;
            top: -50%;
            left: -50%;
            background-image: linear-gradient(rgba(8, 208, 140, 0.15) 1px, transparent 1px),
              linear-gradient(90deg, rgba(8, 208, 140, 0.15) 1px, transparent 1px);
            background-size: 40px 40px;
            transform: perspective(500px) rotateX(60deg);
            transform-origin: center;
            animation: grid-move 20s linear infinite;
            opacity: 0;
            transition: opacity 1s ease;
            z-index: -1;
          }
          
          body.auto-mode .grid-plane {
            opacity: 0.3;
          }
          
          @keyframes grid-move {
            0% {
              transform: perspective(500px) rotateX(60deg) translateY(0);
            }
            100% {
              transform: perspective(500px) rotateX(60deg) translateY(40px);
            }
          }
          
          .stars-container {
            position: fixed;
            width: 100%;
            height: 100%;
            perspective: 500px;
            transform-style: preserve-3d;
            pointer-events: none;
            z-index: -3;
          }
          
          .star-layer {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            opacity: 0;
            transition: opacity 1s ease;
          }
          
          body.auto-mode .star-layer {
            opacity: 0.8;
          }
          
          .star-layer:nth-child(1) {
            transform: translateZ(-50px);
            animation: star-drift 150s linear infinite;
          }
          
          .star-layer:nth-child(2) {
            transform: translateZ(-100px);
            animation: star-drift 200s linear infinite reverse;
            opacity: 0;
          }
          
          .star-layer:nth-child(3) {
            transform: translateZ(-200px);
            animation: star-drift 250s linear infinite;
            opacity: 0;
          }
          
          body.auto-mode .star-layer:nth-child(2) {
            opacity: 0.6;
          }
          
          body.auto-mode .star-layer:nth-child(3) {
            opacity: 0.4;
          }
          
          @keyframes star-drift {
            0% {
              transform: translateZ(-50px) translateY(0);
            }
            100% {
              transform: translateZ(-50px) translateY(100%);
            }
          }
          
          .star-layer::before,
          .star-layer::after {
            content: "";
            position: absolute;
            width: 100%;
            height: 100%;
          }
          
          .star-layer:nth-child(1)::before {
            background-image: radial-gradient(1px 1px at 10% 10%, white 100%, transparent),
              radial-gradient(1px 1px at 20% 20%, white 100%, transparent),
              radial-gradient(2px 2px at 30% 30%, white 100%, transparent),
              radial-gradient(1px 1px at 40% 40%, white 100%, transparent),
              radial-gradient(2px 2px at 50% 50%, white 100%, transparent),
              radial-gradient(1px 1px at 60% 60%, white 100%, transparent),
              radial-gradient(2px 2px at 70% 70%, white 100%, transparent),
              radial-gradient(1px 1px at 80% 80%, white 100%, transparent),
              radial-gradient(2px 2px at 90% 90%, white 100%, transparent),
              radial-gradient(1px 1px at 15% 85%, white 100%, transparent);
          }

          .nebula {
            position: fixed;
            width: 140%;
            height: 140%;
            top: -20%;
            left: -20%;
            background: 
              radial-gradient(
                ellipse at 30% 30%,
                rgba(8, 208, 140, 0.8) 0%,
                rgba(8, 208, 140, 0) 70%
              ),
              radial-gradient(
                ellipse at 70% 60%,
                rgba(0, 113, 167, 0.7) 0%,
                rgba(0, 113, 167, 0) 70%
              ),
              radial-gradient(
                ellipse at 50% 50%,
                rgba(167, 0, 157, 0.7) 0%,
                rgba(167, 0, 157, 0) 70%
              ),
              radial-gradient(
                ellipse at 80% 20%,
                rgba(255, 255, 255, 0.4) 0%,
                rgba(255, 255, 255, 0) 70%
              ),
              radial-gradient(
                ellipse at 20% 80%,
                rgba(8, 208, 140, 0.5) 0%,
                rgba(8, 208, 140, 0) 70%
              ),
              radial-gradient(
                ellipse at 60% 10%,
                rgba(0, 255, 255, 0.3) 0%,
                rgba(0, 255, 255, 0) 70%
              ),
              radial-gradient(
                ellipse at 10% 60%,
                rgba(255, 0, 255, 0.3) 0%,
                rgba(255, 0, 255, 0) 70%
              ),
              radial-gradient(
                ellipse at 90% 80%,
                rgba(255, 255, 0, 0.2) 0%,
                rgba(255, 255, 0, 0) 70%
              );
            filter: blur(40px);
            opacity: 0;
            transition: opacity 1s ease;
            animation: nebula-shift 30s infinite alternate ease-in-out;
            pointer-events: none;
            z-index: -2;
          }
          
          body.auto-mode .nebula {
            opacity: 1;
          }
          
          @keyframes nebula-shift {
            0% {
              transform: scale(1) rotate(0deg);
              opacity: 0.3;
            }
            50% {
              opacity: 0.5;
            }
            100% {
              transform: scale(1.2) rotate(5deg);
              opacity: 0.4;
            }
          }
          
          .activation-ring {
            position: fixed;
            top: 50%;
            left: 50%;
            width: 100vw;
            height: 100vh;
            border: 2px solid rgba(8, 208, 140, 0);
            border-radius: 50%;
            transform: translate(-50%, -50%) scale(0);
            opacity: 0;
            pointer-events: none;
            z-index: 9999;
          }
          
          @keyframes ring-expand {
            0% {
              transform: translate(-50%, -50%) scale(0);
              opacity: 0.8;
              border-color: rgba(8, 208, 140, 0.8);
            }
            100% {
              transform: translate(-50%, -50%) scale(1.5);
              opacity: 0;
              border-color: rgba(8, 208, 140, 0);
            }
          }
          
          .holo-particles {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            pointer-events: none;
            z-index: 9998;
          }
          
          .holo-particle {
            position: absolute;
            background-color: rgba(8, 208, 140, 0.7);
            border-radius: 50%;
            width: 5px;
            height: 5px;
            opacity: 0;
            filter: blur(1px);
            pointer-events: none;
          }
          
          @keyframes particle-float {
            0% {
              transform: translateY(0) scale(1);
              opacity: 0;
            }
            20% {
              opacity: 1;
            }
            80% {
              opacity: 0.5;
            }
            100% {
              transform: translateY(-100px) scale(0);
              opacity: 0;
            }
          }
          
          .app-glow {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(
              ellipse at center,
              rgba(8, 208, 140, 0.2) 0%,
              rgba(8, 208, 140, 0.1) 40%,
              rgba(0, 0, 0, 0) 70%
            );
            pointer-events: none;
            opacity: 0;
            transition: opacity 1s ease;
            z-index: -2;
          }
          
          body.auto-mode .app-glow {
            opacity: 1;
            animation: glow-pulse 4s infinite alternate;
          }
          
          @keyframes glow-pulse {
            0% {
              opacity: 0.3;
              filter: blur(15px) brightness(0.8);
            }
            100% {
              opacity: 0.7;
              filter: blur(25px) brightness(1.2);
            }
          }
          
          .cube-transform {
            position: fixed;
            top: 50%;
            left: 50%;
            width: 100px;
            height: 100px;
            transform-style: preserve-3d;
            opacity: 0;
            transform: translate(-50%, -50%);
            transition: opacity 0.3s ease;
            pointer-events: none;
            z-index: -2;
          }
          
          body.auto-mode .cube-transform {
            opacity: 0.5;
            animation: cube-rotate 20s infinite linear;
          }
          
          .cube-face {
            position: absolute;
            width: 100%;
            height: 100%;
            background-color: rgba(8, 208, 140, 0.1);
            border: 2px solid rgba(8, 208, 140, 0.3);
            box-shadow: 0 0 5px rgba(8, 208, 140, 0.3);
          }
          
          .cube-face:nth-child(1) {
            transform: translateZ(50px);
          }
          
          .cube-face:nth-child(2) {
            transform: rotateY(180deg) translateZ(50px);
          }
          
          .cube-face:nth-child(3) {
            transform: rotateY(90deg) translateZ(50px);
          }
          
          .cube-face:nth-child(4) {
            transform: rotateY(-90deg) translateZ(50px);
          }
          
          .cube-face:nth-child(5) {
            transform: rotateX(90deg) translateZ(50px);
          }
          
          .cube-face:nth-child(6) {
            transform: rotateX(-90deg) translateZ(50px);
          }
          
          @keyframes cube-rotate {
            0% {
              transform: translate(-50%, -50%) rotateX(0) rotateY(0) rotateZ(0);
            }
            100% {
              transform: translate(-50%, -50%) rotateX(360deg) rotateY(360deg) rotateZ(360deg);
            }
          }
          
          .data-chips {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 200px;
            pointer-events: none;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.5s ease;
          }
          
          body.auto-mode .data-chips {
            opacity: 1;
          }
          
          .data-chip {
            padding: 5px 8px;
            background-color: rgba(0, 24, 55, 0.7);
            border: 1px solid rgba(8, 208, 140, 0.5);
            border-radius: 4px;
            font-size: 10px;
            color: white;
            margin-bottom: 5px;
            opacity: 0;
            transform: scale(0);
          }
          
          body.auto-mode .data-chip {
            animation: chip-appear 0.5s ease forwards;
          }
          
          @keyframes chip-appear {
            0% {
              opacity: 0;
              transform: scale(0);
            }
            100% {
              opacity: 1;
              transform: scale(1);
            }
          }
          
          .data-chip:nth-child(1) {
            animation-delay: 0.5s;
          }
          
          .data-chip:nth-child(2) {
            animation-delay: 1.2s;
          }
          
          .data-chip:nth-child(3) {
            animation-delay: 1.8s;
          }
          
          .data-chip:nth-child(4) {
            animation-delay: 2.3s;
          }

          .scan-effect {
            position: fixed;
            height: 2px;
            width: 100%;
            top: 50%;
            left: -100%;
            background: linear-gradient(
              90deg,
              transparent,
              rgba(8, 208, 140, 0.8),
              transparent
            );
            opacity: 0;
            transition: opacity 1s ease;
            pointer-events: none;
            z-index: 9997;
          }
          
          body.auto-mode .scan-effect {
            opacity: 1;
            animation: scan-on 3s infinite ease-in-out;
          }
        `;
        document.head.appendChild(styleEl);
      }
      
      // Tạo hiệu ứng grid plane
      const holoContainer = document.getElementById('holo-effects-container');
      if (holoContainer) {
        // Tạo grid plane 
        if (!document.getElementById('grid-plane')) {
          const gridPlane = document.createElement('div');
          gridPlane.id = 'grid-plane';
          gridPlane.className = 'grid-plane';
          holoContainer.appendChild(gridPlane);
        }
        
        // Tạo stars container 
        if (!document.getElementById('stars-container')) {
          const starsContainer = document.createElement('div');
          starsContainer.id = 'stars-container';
          starsContainer.className = 'stars-container';
          
          // Tạo 3 star layers
          for (let i = 0; i < 20; i++) {
            const starLayer = document.createElement('div');
            starLayer.className = 'star-layer';
            starsContainer.appendChild(starLayer);
          }
          
          holoContainer.appendChild(starsContainer);
        }
        
        // Tạo nebula effect nếu chưa có
        if (!document.getElementById('nebula-effect')) {
          const nebula = document.createElement('div');
          nebula.id = 'nebula-effect';
          nebula.className = 'nebula';
          holoContainer.appendChild(nebula);
        }
        
        // Tạo hiệu ứng glow
        if (!document.getElementById('app-glow')) {
          const appGlow = document.createElement('div');
          appGlow.id = 'app-glow';
          appGlow.className = 'app-glow';
          holoContainer.appendChild(appGlow);
        }
        
        // Tạo cube transform
        if (!document.getElementById('cube-transform')) {
          const cubeTransform = document.createElement('div');
          cubeTransform.id = 'cube-transform';
          cubeTransform.className = 'cube-transform';
          
          // Tạo 6 mặt của khối lập phương
          for (let i = 0; i < 6; i++) {
            const cubeFace = document.createElement('div');
            cubeFace.className = 'cube-face';
            cubeTransform.appendChild(cubeFace);
          }
          
          holoContainer.appendChild(cubeTransform);
        }
        
        // Tạo hiệu ứng particles
        if (!document.getElementById('holo-particles')) {
          const particles = document.createElement('div');
          particles.id = 'holo-particles';
          particles.className = 'holo-particles';
          
          // Tạo 20 particles
          for (let i = 20; i < 0; i++) {
            const particle = document.createElement('div');
            particle.className = 'holo-particle';
            
            // Vị trí ngẫu nhiên
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.left = `${Math.random() * 100}%`;
            
            // Animation delay ngẫu nhiên
            const delay = Math.random() * 5;
            particle.style.animation = `particle-float 8s infinite ease-in-out`;
            particle.style.animationDelay = `${delay}s`;
            
            particles.appendChild(particle);
          }
          
          holoContainer.appendChild(particles);
        }
        
        // Tạo hiệu ứng scan-effect
        // if (!document.getElementById('scan-effect')) {
        //   const scanEffect = document.createElement('div');
        //   scanEffect.id = 'scan-effect';
        //   scanEffect.className = 'scan-effect';
        //   holoContainer.appendChild(scanEffect);
        // }
        
        // Tạo corner accents giống HoloSwitch
        // if (!document.getElementById('corner-accents')) {
        //   const cornerAccents = document.createElement('div');
        //   cornerAccents.id = 'corner-accents';
          
        //   for (let i = 0; i < 4; i++) {
        //     const cornerAccent = document.createElement('div');
        //     cornerAccent.className = 'corner-accent';
        //     cornerAccents.appendChild(cornerAccent);
        //   }
          
        //   holoContainer.appendChild(cornerAccents);
        // }
      
        // Hiệu ứng vòng sóng khi chuyển sang chế độ auto
        if (hasActivated) {
          // Tạo các vòng sóng khi kích hoạt
          for (let i = 0; i < 3; i++) {
            const ring = document.createElement('div');
            ring.className = 'activation-ring';
            ring.style.animation = `ring-expand 2s ease-out forwards`;
            ring.style.animationDelay = `${i * 0.3}s`;
            
            // Tự xóa sau khi animation kết thúc
            setTimeout(() => {
              ring.remove();
            }, 2000 + i * 300);
            
            holoContainer.appendChild(ring);
          }
        }
      }
      
    } else {
      // Trở lại màu nền mặc định
      document.body.classList.remove('auto-mode');
      document.body.style.backgroundColor = 'black';
      
      // Loại bỏ class auto-mode-header từ header
      const headerEl = document.querySelector('header');
      if (headerEl) {
        headerEl.classList.remove('auto-mode-header');
      }
    }
    
    return () => {
      // Cleanup khi component unmount
      const styleEl = document.getElementById('holo-animation-styles');
      if (styleEl) {
        styleEl.remove();
      }
      
      const holoContainer = document.getElementById('holo-effects-container');
      if (holoContainer) {
        holoContainer.remove();
      }
      
      document.body.classList.remove('auto-mode');
    };
  }, [isAutoMode, hasActivated]);

  // useEffect(() => {
  //   if (videoRef.current) {
  //     videoRef.current.playbackRate = 0.5; // Giảm tốc độ phát video xuống 0.5 lần
  //   }
  // }, []);

  return (
    <>
      {/* <video
        ref={videoRef}
        src="/videos/video_gen.mp4"
        autoPlay
        loop
        muted
        playsInline
        style={{
          position: 'fixed',
          // backgroundPositionY: '50px',
          left: 0,
          top: 0,
          width: '100vh',
          height: '100vw',
          objectFit: 'cover',
          zIndex: -4,
          transform: 'rotate(90deg) translateY(-100vw)',
          transformOrigin: 'left top',
        }}
      /> */}
      <img
        src="/img_wave.jpg"
        alt="Background Image"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          objectFit: 'cover',
          zIndex: -3,
        }}
      />
      {/* <img
        src="/img_half_world.png"
        alt="Background Image"
        style={{
          position: 'fixed',
          top: 0,
          left: '28%',
          transform: 'translateX(-10%) translateY(35%)',
          width: '50vw',
          height: '28vh',
          objectFit: 'cover',
          zIndex: -2,
          opacity: 1
        }}
      /> */}
      {/* <img
        src="/animation_consistent.gif"
        alt="Animation GIF"
        style={{
          position: 'fixed',
          top: '20px',
          left: '20px',
          width: '150px',
          transform: 'translateX(5%) translateY(90%)',
          height: 'auto',
          zIndex: -1,
          scale: 2,
          animation: 'infinite-loop 120s linear infinite'
        }}
      /> */}
      {children}
    </>
  );
} 