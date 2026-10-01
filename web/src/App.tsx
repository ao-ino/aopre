import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { useEffect, useState } from "react";
import { Choose } from "./Choose";
import { Experiment } from "./Experiment";
import { Scale } from "./Scale";
import { soundState } from "./sound";

const TABS = [
  { id: "count", label: "数えてみよう", hint: "小さい順に1つずつ", el: <Experiment /> },
  { id: "choose", label: "2本ずつ選ぶ", hint: "縦2本・横2本で1つ", el: <Choose /> },
  { id: "scale", label: "本数を変える", hint: "何本でも一発", el: <Scale /> },
];

function initialTab() {
  const h = location.hash.replace("#", "");
  return TABS.some((t) => t.id === h) ? h : "count";
}

export function App() {
  const [tab, setTab] = useState(initialTab);
  const [sound, setSound] = useState(true);
  useEffect(() => { soundState.enabled = sound; }, [sound]);

  const go = (id: string) => {
    setTab(id);
    try { history.replaceState(null, "", `#${id}`); } catch { /* 共有リンクで無効でも動作は続ける */ }
  };

  return (
    <MotionConfig reducedMotion="user">
      <main className="page">
        <header className="head">
          <div>
            <p className="eyebrow">問題 257 ・ 組合せ</p>
            <h1>平行四辺形はいくつ？</h1>
            <p className="problem">
              6本の平行線と、それらに交わる7本の平行線とによってできる平行四辺形は何個あるか。
            </p>
          </div>
          <button className="btn ghost sound" onClick={() => setSound((s) => !s)} aria-pressed={sound}>
            {sound ? "音あり" : "音なし"}
          </button>
        </header>

        <nav className="tabs" aria-label="ステップ">
          {TABS.map((t, k) => (
            <button key={t.id} className={`tab${tab === t.id ? " on" : ""}`} onClick={() => go(t.id)}
              aria-current={tab === t.id ? "page" : undefined}>
              <span className="tab-no">{k + 1}</span>
              <span className="tab-text">
                <span className="tab-label">{t.label}</span>
                <span className="tab-hint">{t.hint}</span>
              </span>
              {tab === t.id && <motion.span layoutId="tab-ink" className="tab-ink" transition={{ type: "spring", stiffness: 500, damping: 35 }} />}
            </button>
          ))}
        </nav>

        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.22 }}>
            {TABS.find((t) => t.id === tab)!.el}
          </motion.div>
        </AnimatePresence>
      </main>
    </MotionConfig>
  );
}
