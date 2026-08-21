"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

/**
 * Hook to trigger staggered GSAP entrance animations on child elements.
 */
export function useGsapStagger<T extends HTMLElement = HTMLDivElement>(
  selector: string = ".gsap-item",
  dependencies: any[] = []
) {
  const containerRef = useRef<T>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const ctx = gsap.context(() => {
      const items = containerRef.current?.querySelectorAll(selector);
      if (items && items.length > 0) {
        gsap.fromTo(
          items,
          {
            opacity: 0,
            y: 20,
            scale: 0.98,
          },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.6,
            stagger: 0.06,
            ease: "power3.out",
            clearProps: "transform",
          }
        );
      }
    }, containerRef);

    return () => ctx.revert();
  }, dependencies);

  return containerRef;
}

/**
 * Hook to animate numeric values smoothly with GSAP.
 */
export function useGsapCountUp(
  targetValue: number,
  duration: number = 1.2,
  decimals: number = 2
) {
  const elementRef = useRef<HTMLSpanElement>(null);
  const prevValueRef = useRef<number>(0);

  useEffect(() => {
    if (!elementRef.current) return;

    const obj = { val: prevValueRef.current };
    const tween = gsap.to(obj, {
      val: targetValue,
      duration,
      ease: "power2.out",
      onUpdate: () => {
        if (elementRef.current) {
          elementRef.current.textContent = obj.val.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
          });
        }
      },
    });

    prevValueRef.current = targetValue;

    return () => {
      tween.kill();
    };
  }, [targetValue, duration, decimals]);

  return elementRef;
}
