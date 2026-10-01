import { animate, motion, useMotionValue, useTransform } from "motion/react";
import { useEffect } from "react";

/** 値が変わるとバネのように数字が数え上がる。 */
export function AnimatedNumber({ value, className }: { value: number; className?: string }) {
  const mv = useMotionValue(value);
  const text = useTransform(mv, (v) => Math.round(v).toLocaleString("ja-JP"));
  useEffect(() => {
    const ctl = animate(mv, value, { type: "spring", stiffness: 120, damping: 20 });
    return () => ctl.stop();
  }, [mv, value]);
  return <motion.span className={className}>{text}</motion.span>;
}
