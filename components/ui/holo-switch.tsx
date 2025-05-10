"use client"

import React from 'react';
import styled from 'styled-components';
import * as SwitchPrimitives from "@radix-ui/react-switch"
import { cn } from "@/lib/utils"

const HoloSwitch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <StyledSwitchWrapper>
    <SwitchPrimitives.Root
      className={cn(
        "peer holo-checkbox-input",
        className
      )}
      {...props}
      ref={ref}
    >
      <SwitchPrimitives.Thumb className="hidden" />
    </SwitchPrimitives.Root>
    
    <div className="checkbox-container">
      <label className="holo-checkbox" htmlFor={props.id}>
        <div className="holo-box">
          <div className="holo-inner" />
          <div className="scan-effect" />
          <div className="holo-particles">
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
          </div>
          <div className="activation-rings">
            <div className="activation-ring" />
            <div className="activation-ring" />
            <div className="activation-ring" />
          </div>
          <div className="cube-transform">
            <div className="cube-face" />
            <div className="cube-face" />
            <div className="cube-face" />
            <div className="cube-face" />
            <div className="cube-face" />
            <div className="cube-face" />
          </div>
        </div>
        <div className="corner-accent corner-accent-top-left" />
        <div className="corner-accent corner-accent-top-right" />
        <div className="corner-accent corner-accent-bottom-left" />
        <div className="corner-accent corner-accent-bottom-right" />
        <div className="holo-glow" />
      </label>
    </div>
  </StyledSwitchWrapper>
));

HoloSwitch.displayName = SwitchPrimitives.Root.displayName;

const StyledSwitchWrapper = styled.div`
  position: relative;
  display: inline-block;
  
  .checkbox-container {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    z-index: 10;
  }

  /* Ẩn input mặc định */
  .holo-checkbox-input {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    z-index: 100;
    top: 0;
    left: 0;
    margin: 0;
    cursor: pointer;
  }

  .holo-checkbox {
    position: relative;
    width: 40px;
    height: 40px;
    cursor: pointer;
    transform-style: preserve-3d;
    perspective: 1000px;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .holo-box {
    position: relative;
    width: 100%;
    height: 100%;
    border: 2px solid rgba(0, 162, 255, 0.7);
    border-radius: 8px;
    background-color: rgba(0, 24, 55, 0.5);
    box-shadow:
      0 0 10px rgba(0, 162, 255, 0.5),
      inset 0 0 15px rgba(0, 162, 255, 0.3);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    transition: all 0.3s ease;
    transform-style: preserve-3d;
  }

  .holo-inner {
    position: absolute;
    width: 30%;
    height: 30%;
    background-color: rgba(0, 162, 255, 0.5);
    border-radius: 4px;
    opacity: 0;
    transform: scale(0) rotate(45deg);
    transition: all 0.3s ease;
    box-shadow: 0 0 15px rgba(0, 162, 255, 0.8);
  }

  .scan-effect {
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 2px;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(0, 162, 255, 0.8),
      transparent
    );
    animation: scan-off 4s infinite;
    opacity: 0.3;
    transition: all 0.3s ease;
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

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-box {
    border-color: rgba(0, 255, 136, 0.7);
    box-shadow:
      0 0 10px rgba(0, 255, 136, 0.6),
      inset 0 0 15px rgba(0, 255, 136, 0.4);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-inner {
    background-color: rgba(0, 255, 136, 0.7);
    box-shadow: 0 0 15px rgba(0, 255, 136, 1);
    opacity: 1;
    transform: scale(1) rotate(45deg);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .scan-effect {
    animation: scan-on 2s infinite;
    opacity: 1;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(0, 255, 136, 0.8),
      transparent
    );
  }

  .holo-glow {
    position: absolute;
    width: 200%;
    height: 200%;
    left: -50%;
    top: -50%;
    background: radial-gradient(
      ellipse at center,
      rgba(0, 162, 255, 0.2) 0%,
      rgba(0, 162, 255, 0.1) 40%,
      rgba(0, 0, 0, 0) 70%
    );
    pointer-events: none;
    filter: blur(10px);
    opacity: 0.5;
    z-index: -1;
    animation: glow-pulse 4s infinite alternate;
    transition: all 0.5s ease;
  }

  @keyframes glow-pulse {
    0% {
      opacity: 0.3;
      filter: blur(10px) brightness(0.8);
    }
    100% {
      opacity: 0.6;
      filter: blur(15px) brightness(1.2);
    }
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-glow {
    background: radial-gradient(
      ellipse at center,
      rgba(0, 255, 136, 0.2) 0%,
      rgba(0, 255, 136, 0.1) 40%,
      rgba(0, 0, 0, 0) 70%
    );
    animation: active-glow-pulse 2s infinite alternate;
  }

  @keyframes active-glow-pulse {
    0% {
      opacity: 0.4;
      filter: blur(10px) brightness(1);
    }
    100% {
      opacity: 0.8;
      filter: blur(20px) brightness(1.5);
    }
  }

  .corner-accent {
    position: absolute;
    width: 12px;
    height: 12px;
    border-style: solid;
    border-width: 2px;
    border-color: rgba(0, 162, 255, 0.5);
    transition: all 0.3s ease;
    z-index: 1;
    opacity: 1;
    pointer-events: none;
  }

  .corner-accent-top-left {
    top: -5px;
    left: -5px;
    border-right: none;
    border-bottom: none;
    border-top: 2px solid rgba(0, 162, 255, 0.5);
    border-left: 2px solid rgba(0, 162, 255, 0.5);
    border-radius: 4px 0 0 0;
    width: 12px;
    height: 12px;
  }
  .corner-accent-top-right {
    top: -5px;
    right: -5px;
    border-left: none;
    border-bottom: none;
    border-top: 2px solid rgba(0, 162, 255, 0.5);
    border-right: 2px solid rgba(0, 162, 255, 0.5);
    border-radius: 0 4px 0 0;
    width: 12px;
    height: 12px;
  }
  .corner-accent-bottom-left {
    bottom: -5px;
    left: -5px;
    border-right: none;
    border-top: none;
    border-bottom: 2px solid rgba(0, 162, 255, 0.5);
    border-left: 2px solid rgba(0, 162, 255, 0.5);
    border-radius: 0 0 0 4px;
    width: 12px;
    height: 12px;
  }
  .corner-accent-bottom-right {
    bottom: -5px;
    right: -5px;
    border-left: none;
    border-top: none;
    border-bottom: 2px solid rgba(0, 162, 255, 0.5);
    border-right: 2px solid rgba(0, 162, 255, 0.5);
    border-radius: 0 0 4px 0;
    width: 12px;
    height: 12px;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .corner-accent-top-left {

    border-top: 2px solid rgba(0, 255, 136, 0.7);
    border-left: 2px solid rgba(0, 255, 136, 0.7);
    box-shadow: 0 0 5px rgba(0,255,136,0.5);
  }
  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .corner-accent-top-right {

    border-top: 2px solid rgba(0, 255, 136, 0.7);
    border-right: 2px solid rgba(0, 255, 136, 0.7);
    box-shadow: 0 0 5px rgba(0,255,136,0.5);
  }
  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .corner-accent-bottom-left {
    border-bottom: 2px solid rgba(0, 255, 136, 0.7);
    border-left: 2px solid rgba(0, 255, 136, 0.7);
    box-shadow: 0 0 5px rgba(0,255,136,0.5);
  }
  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .corner-accent-bottom-right {
    border-bottom: 2px solid rgba(0, 255, 136, 0.7);
    border-right: 2px solid rgba(0, 255, 136, 0.7);
    box-shadow: 0 0 5px rgba(0,255,136,0.5);
  }

  .activation-rings {
    position: absolute;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .activation-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 40%;
    height: 40%;
    border: 1px solid rgba(0, 255, 136, 0);
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
    transition: all 0.3s ease;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .activation-ring {
    animation: ring-expand 2s ease-out forwards;
    border-color: rgba(0, 255, 136, 0.7);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .activation-ring:nth-child(1) {
    animation-delay: 0s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .activation-ring:nth-child(2) {
    animation-delay: 0.3s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .activation-ring:nth-child(3) {
    animation-delay: 0.6s;
  }

  @keyframes ring-expand {
    0% {
      transform: translate(-50%, -50%) scale(0);
      opacity: 1;
    }
    100% {
      transform: translate(-50%, -50%) scale(2.5);
      opacity: 0;
    }
  }

  .holo-particles {
    position: absolute;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .holo-particle {
    position: absolute;
    background-color: rgba(0, 162, 255, 0.7);
    border-radius: 50%;
    width: 3px;
    height: 3px;
    opacity: 0;
    filter: blur(1px);
    transition: all 0.3s ease;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle {
    background-color: rgba(0, 255, 136, 0.7);
    animation: particle-float 3s infinite ease-in-out;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle:nth-child(1) {
    top: 20%;
    left: 30%;
    animation-delay: 0.1s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle:nth-child(2) {
    top: 70%;
    left: 20%;
    animation-delay: 0.7s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle:nth-child(3) {
    top: 40%;
    left: 80%;
    animation-delay: 1.3s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle:nth-child(4) {
    top: 60%;
    left: 60%;
    animation-delay: 1.9s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle:nth-child(5) {
    top: 30%;
    left: 45%;
    animation-delay: 2.5s;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .holo-particle:nth-child(6) {
    top: 60%;
    left: 40%;
    animation-delay: 3.1s;
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
      opacity: 1;
    }
    100% {
      transform: translateY(-20px) scale(0);
      opacity: 0;
    }
  }

  .cube-transform {
    position: absolute;
    width: 30%;
    height: 30%;
    transform-style: preserve-3d;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .cube-face {
    position: absolute;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 162, 255, 0.3);
    border: 1px solid rgba(0, 162, 255, 0.5);
    box-shadow: 0 0 5px rgba(0, 162, 255, 0.3);
    transition: all 0.3s ease;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-transform {
    opacity: 1;
    animation: cube-rotate 5s infinite linear;
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face {
    background-color: rgba(0, 255, 136, 0.3);
    border-color: rgba(0, 255, 136, 0.5);
    box-shadow: 0 0 5px rgba(0, 255, 136, 0.3);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face:nth-child(1) {
    transform: translateZ(10px);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face:nth-child(2) {
    transform: rotateY(180deg) translateZ(10px);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face:nth-child(3) {
    transform: rotateY(90deg) translateZ(10px);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face:nth-child(4) {
    transform: rotateY(-90deg) translateZ(10px);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face:nth-child(5) {
    transform: rotateX(90deg) translateZ(10px);
  }

  .holo-checkbox-input[data-state="checked"] ~ .checkbox-container .cube-face:nth-child(6) {
    transform: rotateX(-90deg) translateZ(10px);
  }

  @keyframes cube-rotate {
    0% {
      transform: rotateX(0) rotateY(0) rotateZ(0);
    }
    100% {
      transform: rotateX(360deg) rotateY(360deg) rotateZ(360deg);
    }
  }
`;

export { HoloSwitch }; 