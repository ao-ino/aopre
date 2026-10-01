import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import { AnimatedNumber } from "./AnimatedNumber";
import { choose2, geometry, VIEW } from "./geometry";
import { pop } from "./sound";

const PRESETS = [
  { label: "問題257（縦7・横6）", s: 7, h: 6 },
  { label: "縦20・横30", s: 20, h: 30 },
  { label: "縦3・横3", s: 3, h: 3 },
];

export function Scale() {
  const [nS, setNS] = useState(20);
  const [nH, setNH] = useState(30);
  const [demo, setDemo] = useState<[number, number, number, number] | null>(null);
  const g = useMemo(() => geometry(nH, nS), [nH, nS]);

  // 2本・2本を選ぶと必ず平行四辺形になる様子を、ときどき見せる
  useEffect(() => {
    const pick = (n: number) => {
      const a = Math.floor(Math.random() * n);
      let b = Math.floor(Math.random() * (n - 1));
      if (b >= a) b++;
      return a < b ? [a, b] : [b, a];
    };
    const run = () => setDemo([...pick(nH), ...pick(nS)] as [number, number, number, number]);
    run();
    const t = setInterval(run, 1600);
    return () => clearInterval(t);
  }, [nH, nS]);

  const a = choose2(nS), b = choose2(nH);
  const thin = nH + nS > 30;

  const set = (s: number, h: number) => { setNS(s); setNH(h); pop(Math.min(s, h) % 8); };

  return (
    <div className="stage">
      <figure className="board">
        <svg viewBox={`0 0 ${VIEW.w} ${VIEW.h}`} role="img" aria-label={`縦${nS}本・横${nH}本の平行線`}>
          <AnimatePresence>
            {demo && demo[1] < nH && demo[3] < nS && (
              <motion.polygon
                key={demo.join("-") + `${nH}x${nS}`}
                className="para"
                points={g.para(demo[0], demo[1], demo[2], demo[3])}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              />
            )}
          </AnimatePresence>
          {Array.from({ length: nH }, (_, i) => {
            const [p, q] = g.hLine(i);
            const sel = demo && (demo[0] === i || demo[1] === i);
            return (
              <motion.line key={`h${i}`} className={`ln ln-h${sel ? " lit" : ""}`}
                initial={{ opacity: 0, x1: p[0], y1: p[1], x2: q[0], y2: q[1] }}
                animate={{ x1: p[0], y1: p[1], x2: q[0], y2: q[1], opacity: 1, strokeWidth: sel ? 5 : thin ? 1.4 : 3 }}
                transition={{ type: "spring", stiffness: 160, damping: 22 }} />
            );
          })}
          {Array.from({ length: nS }, (_, j) => {
            const [p, q] = g.sLine(j);
            const sel = demo && (demo[2] === j || demo[3] === j);
            return (
              <motion.line key={`s${j}`} className={`ln ln-s${sel ? " lit" : ""}`}
                initial={{ opacity: 0, x1: p[0], y1: p[1], x2: q[0], y2: q[1] }}
                animate={{ x1: p[0], y1: p[1], x2: q[0], y2: q[1], opacity: 1, strokeWidth: sel ? 5 : thin ? 1.4 : 3 }}
                transition={{ type: "spring", stiffness: 160, damping: 22 }} />
            );
          })}
        </svg>
        <figcaption>何本になっても、<span className="tag-s">縦 2本</span>と<span className="tag-h">横 2本</span>で 1つ決まる</figcaption>
      </figure>

      <section className="panel">
        <label className="slider" htmlFor="ns">
          <span className="tag-s">縦の線</span>
          <input id="ns" type="range" min={2} max={30} value={nS} onChange={(e) => setNS(+e.target.value)} />
          <b className="num">{nS}本</b>
        </label>
        <label className="slider" htmlFor="nh">
          <span className="tag-h">横の線</span>
          <input id="nh" type="range" min={2} max={30} value={nH} onChange={(e) => setNH(+e.target.value)} />
          <b className="num">{nH}本</b>
        </label>
        <div className="controls">
          {PRESETS.map((p) => (
            <button key={p.label} className="btn" onClick={() => set(p.s, p.h)}>{p.label}</button>
          ))}
        </div>

        <div className="calc">
          <p><span className="tag-s">縦 {nS}本</span>から 2本：<sub>{nS}</sub>C<sub>2</sub> = {nS}×{nS - 1}÷2 = <b><AnimatedNumber value={a} /></b></p>
          <p><span className="tag-h">横 {nH}本</span>から 2本：<sub>{nH}</sub>C<sub>2</sub> = {nH}×{nH - 1}÷2 = <b><AnimatedNumber value={b} /></b></p>
          <p className="formula result">
            <AnimatedNumber value={a} /> × <AnimatedNumber value={b} /> = <b><AnimatedNumber value={a * b} className="num big" /></b> 個
          </p>
          <p className="note">1つずつ数えなくても、一発で求まります。</p>
        </div>
      </section>
    </div>
  );
}
