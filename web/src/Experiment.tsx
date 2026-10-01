import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { geometry, VIEW } from "./geometry";
import { chime, pop } from "./sound";

const N_H = 3, N_S = 4;           // 横3本・縦4本
const COLS = N_S - 1, ROWS = N_H - 1;
const g = geometry(N_H, N_S);

interface Item { w: number; h: number; r: number; c: number; n: number }

// 小さい順（面積 → 縦の長さ）に、左上から横優先で並べる
const SIZES = Array.from({ length: ROWS }, (_, h) => Array.from({ length: COLS }, (_, w) => [w + 1, h + 1]))
  .flat()
  .sort((a, b) => a[0] * a[1] - b[0] * b[1] || a[1] - b[1]);
const ITEMS: Item[] = SIZES.flatMap(([w, h]) => {
  const out: Item[] = [];
  for (let r = 0; r + h <= ROWS; r++)
    for (let c = 0; c + w <= COLS; c++) out.push({ w, h, r, c, n: out.length });
  return out;
});
const TOTAL = ITEMS.length;

function SizeIcon({ w, h }: { w: number; h: number }) {
  const s = 9, k = 0.35;
  const cells = [];
  for (let r = 0; r < h; r++)
    for (let c = 0; c < w; c++) {
      const p = (cc: number, rr: number) => `${cc * s + (h - rr) * s * k},${rr * s}`;
      cells.push(<polygon key={`${r}-${c}`} points={[p(c, r), p(c + 1, r), p(c + 1, r + 1), p(c, r + 1)].join(" ")} />);
    }
  return (
    <svg className="size-icon" width={3 * s + 2 * s * k + 2} height={2 * s + 2} viewBox={`-1 -1 ${3 * s + 2 * s * k + 2} ${2 * s + 2}`} aria-hidden>
      {cells}
    </svg>
  );
}

export function Experiment() {
  const [idx, setIdx] = useState(-1);
  const [auto, setAuto] = useState(false);
  const done = idx === TOTAL - 1;

  // interval からも最新の値を読めるよう ref に持つ（音は state 更新の外で鳴らす）
  const idxRef = useRef(idx);
  idxRef.current = idx;
  const step = () => {
    const next = idxRef.current + 1;
    if (next >= TOTAL) return;
    idxRef.current = next;
    setIdx(next);
    pop(ITEMS[next].n);
    if (next === TOTAL - 1) setTimeout(chime, 450);
  };

  useEffect(() => {
    if (!auto) return;
    if (done) { setAuto(false); return; }
    const t = setInterval(step, 1000);
    return () => clearInterval(t);
  }, [auto, done]);

  const counts = useMemo(() => {
    const m = new Map<string, number>();
    ITEMS.slice(0, idx + 1).forEach((it) => m.set(`${it.w}x${it.h}`, it.n + 1));
    return m;
  }, [idx]);

  const cur = idx >= 0 ? ITEMS[idx] : null;

  return (
    <div className="stage">
      <figure className="board">
        <svg viewBox={`0 0 ${VIEW.w} ${VIEW.h}`} role="img" aria-label="横3本・縦4本の平行線">
          <AnimatePresence>
            {cur && (
              <motion.polygon
                key={idx}
                className="para"
                points={g.para(cur.r, cur.r + cur.h, cur.c, cur.c + cur.w)}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, transition: { duration: 0.25 } }}
                transition={{ type: "spring", stiffness: 380, damping: 18 }}
                style={{ transformBox: "fill-box", transformOrigin: "center" }}
              />
            )}
          </AnimatePresence>
          {Array.from({ length: N_H }, (_, i) => {
            const [a, b] = g.hLine(i);
            return <line key={`h${i}`} className="ln ln-h" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} />;
          })}
          {Array.from({ length: N_S }, (_, j) => {
            const [a, b] = g.sLine(j);
            return <line key={`s${j}`} className="ln ln-s" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} />;
          })}
        </svg>
        <figcaption>
          <span className="tag-h">横 3本</span>・<span className="tag-s">縦 4本</span>で実験
        </figcaption>
      </figure>

      <section className="panel">
        <p className="lead">小さい順に、左上から 1つずつ数えます。</p>
        <div className="controls">
          <button className="btn primary" onClick={step} disabled={done}>次へ</button>
          <button className="btn" onClick={() => setAuto((a) => !a)} disabled={done}>{auto ? "止める" : "自動で数える"}</button>
          <button className="btn ghost" onClick={() => { setAuto(false); setIdx(-1); }}>最初から</button>
        </div>

        <ul className="tally">
          <AnimatePresence initial={false}>
            {SIZES.filter(([w, h]) => counts.has(`${w}x${h}`)).map(([w, h]) => {
              const n = counts.get(`${w}x${h}`)!;
              const active = cur && cur.w === w && cur.h === h;
              return (
                <motion.li
                  key={`${w}x${h}`}
                  layout
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={active ? "active" : ""}
                >
                  <SizeIcon w={w} h={h} />
                  <span className="size">{w}×{h} のもの</span>
                  <motion.b key={n} className="num" initial={{ scale: 1.6 }} animate={{ scale: 1 }}>{n}</motion.b>
                  <span>個</span>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
        <p className="total">合計 <b className="num">{idx + 1}</b> 個</p>

        <AnimatePresence>
          {done && <Pattern />}
        </AnimatePresence>
      </section>
    </div>
  );
}

function Pattern() {
  const hPos = Array.from({ length: COLS }, (_, w) => COLS - w);      // 3,2,1
  const vPos = Array.from({ length: ROWS }, (_, h) => ROWS - h);      // 2,1
  return (
    <motion.div
      className="pattern"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, staggerChildren: 0.15 }}
    >
      <h3>表に並べると…</h3>
      <table>
        <thead>
          <tr>
            <th />
            {hPos.map((p, w) => (
              <th key={w}><span className="pos-h">{p}</span><br /><small>横{w + 1}</small></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {vPos.map((q, h) => (
            <tr key={h}>
              <th><span className="pos-v">{q}</span> <small>縦{h + 1}</small></th>
              {hPos.map((p, w) => (
                <motion.td key={w} initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.7 + (h * COLS + w) * 0.12 }}>
                  {p * q}
                </motion.td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">
        どの数も <span className="pos-h">横に置ける場所</span> × <span className="pos-v">縦に置ける場所</span>
      </p>
      <p className="formula">
        合計 = (<span className="pos-h">3+2+1</span>) × (<span className="pos-v">2+1</span>) = <b>18</b>
      </p>
    </motion.div>
  );
}
