import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { AnimatedNumber } from "./AnimatedNumber";
import { choose2, geometry, VIEW } from "./geometry";
import { chime, pop } from "./sound";

const N_H = 6, N_S = 7;                 // 問題257: 横6本・縦7本
const g = geometry(N_H, N_S);
const ALL = choose2(N_S) * choose2(N_H); // 315

/** 選んだ線を追加。同じ向きで 2 本を超えたら古い方を外す。 */
function toggle(list: number[], k: number) {
  if (list.includes(k)) return list.filter((x) => x !== k);
  return [...list, k].slice(-2);
}

const sorted = (a: number[]) => [...a].sort((x, y) => x - y);

export function Choose() {
  const [hs, setHs] = useState<number[]>([1, 4]);   // 最初から 1 つ見えている状態で開く
  const [ss, setSs] = useState<number[]>([1, 4]);
  const [found, setFound] = useState<Set<string>>(() => new Set(["1-4|1-4"]));

  const complete = hs.length === 2 && ss.length === 2;
  const key = complete ? `${sorted(hs).join("-")}|${sorted(ss).join("-")}` : null;

  const commit = (nh: number[], ns: number[]) => {
    setHs(nh);
    setSs(ns);
    if (nh.length === 2 && ns.length === 2) {
      const k = `${sorted(nh).join("-")}|${sorted(ns).join("-")}`;
      if (!found.has(k)) {
        setFound(new Set(found).add(k));
        chime();
      } else pop(7);
    } else pop(nh.length + ns.length - 1);
  };

  const random = () => {
    const pick = (n: number) => {
      const a = Math.floor(Math.random() * n);
      let b = Math.floor(Math.random() * (n - 1));
      if (b >= a) b++;
      return [a, b];
    };
    commit(pick(N_H), pick(N_S));
  };

  const [i1, i2] = sorted(hs);
  const [j1, j2] = sorted(ss);

  const lineProps = (sel: boolean, label: string, onPick: () => void) => ({
    className: `hit${sel ? " sel" : ""}`,
    onClick: onPick,
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onPick(); }
    },
    tabIndex: 0,
    role: "button",
    "aria-pressed": sel,
    "aria-label": label,
  });

  return (
    <div className="stage">
      <figure className="board">
        <svg viewBox={`0 0 ${VIEW.w} ${VIEW.h}`} role="group" aria-label="横6本・縦7本。線を押して選ぶ">
          <AnimatePresence>
            {key && (
              <motion.polygon
                key={key}
                className="para"
                points={g.para(i1, i2, j1, j2)}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                transition={{ type: "spring", stiffness: 420, damping: 16 }}
                style={{ transformBox: "fill-box", transformOrigin: "center" }}
              />
            )}
          </AnimatePresence>
          {Array.from({ length: N_H }, (_, i) => {
            const [a, b] = g.hLine(i);
            const sel = hs.includes(i);
            return (
              <g key={`h${i}`} {...lineProps(sel, `横の線 ${i + 1}`, () => commit(toggle(hs, i), ss))}>
                <line className="ln-hit" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} />
                <motion.line className="ln ln-h" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
                  animate={{ strokeWidth: sel ? 7 : 3 }} />
              </g>
            );
          })}
          {Array.from({ length: N_S }, (_, j) => {
            const [a, b] = g.sLine(j);
            const sel = ss.includes(j);
            return (
              <g key={`s${j}`} {...lineProps(sel, `縦の線 ${j + 1}`, () => commit(hs, toggle(ss, j)))}>
                <line className="ln-hit" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} />
                <motion.line className="ln ln-s" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
                  animate={{ strokeWidth: sel ? 7 : 3 }} />
              </g>
            );
          })}
        </svg>
        <figcaption>線を押して、<span className="tag-s">縦 2本</span>と<span className="tag-h">横 2本</span>を選んでください</figcaption>
      </figure>

      <section className="panel">
        <div className="picks">
          <Pick label="縦" cls="tag-s" n={ss.length} />
          <Pick label="横" cls="tag-h" n={hs.length} />
        </div>
        <p className="lead">
          {complete ? "平行四辺形がちょうど 1つ決まりました。" : "あと少し。2本ずつ選ぶと平行四辺形ができます。"}
        </p>

        <div className="found">
          <div className="found-row">
            <span>見つけた平行四辺形</span>
            <span><AnimatedNumber value={found.size} className="num big" /> / {ALL}</span>
          </div>
          <div className="bar" aria-hidden>
            <motion.div className="bar-fill" animate={{ width: `${(found.size / ALL) * 100}%` }}
              transition={{ type: "spring", stiffness: 120, damping: 20 }} />
          </div>
        </div>

        <div className="controls">
          <button className="btn primary" onClick={random}>ランダムに選ぶ</button>
          <button className="btn ghost" onClick={() => { setHs([]); setSs([]); setFound(new Set()); }}>リセット</button>
        </div>

        <div className="calc">
          <p><span className="tag-s">縦 7本</span>から 2本：<sub>7</sub>C<sub>2</sub> = <b>21</b> 通り</p>
          <p><span className="tag-h">横 6本</span>から 2本：<sub>6</sub>C<sub>2</sub> = <b>15</b> 通り</p>
          <p className="formula">21 × 15 = <b>315</b> 個</p>
        </div>
      </section>
    </div>
  );
}

function Pick({ label, cls, n }: { label: string; cls: string; n: number }) {
  return (
    <div className="pick">
      <span className={cls}>{label}</span>
      <span className="dots">
        {[0, 1].map((k) => (
          <motion.span key={k} className={`dot ${cls}`} animate={{ scale: k < n ? 1 : 0.55, opacity: k < n ? 1 : 0.3 }}
            transition={{ type: "spring", stiffness: 500, damping: 20 }} />
        ))}
      </span>
    </div>
  );
}
