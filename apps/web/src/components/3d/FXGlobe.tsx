"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, OrbitControls, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

function AnimatedSphere() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.15;
      meshRef.current.rotation.x = clock.getElapsedTime() * 0.05;
    }
  });

  return (
    <Sphere ref={meshRef} args={[1, 64, 64]} scale={2.2}>
      <MeshDistortMaterial
        color="#00F0FF"
        attach="material"
        distort={0.35}
        speed={1.8}
        roughness={0.2}
        metalness={0.8}
        wireframe={true}
      />
    </Sphere>
  );
}

export default function FXGlobe() {
  return (
    <div className="w-full h-full min-h-[220px] relative rounded-2xl overflow-hidden bg-gradient-to-b from-tradly-card to-tradly-bg border border-tradly-border flex items-center justify-center">
      <div className="absolute top-3 left-4 z-10">
        <span className="text-[10px] uppercase tracking-widest font-bold text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded border border-cyan-500/20">
          Global FX Liquidity Sphere
        </span>
      </div>
      <Canvas camera={{ position: [0, 0, 4.5], fov: 50 }}>
        <ambientLight intensity={0.8} />
        <directionalLight position={[10, 10, 5]} intensity={1.5} color="#00F0FF" />
        <pointLight position={[-10, -10, -5]} intensity={0.8} color="#00E676" />
        <AnimatedSphere />
        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
      </Canvas>
    </div>
  );
}
