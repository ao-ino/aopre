// Web Audio で「ポン」（ドレミの音階）と「キラーン」を鳴らす。動画版と同じ音作り。
let ctx: AudioContext | null = null;
export const soundState = { enabled: true };

function ac(): AudioContext | null {
  if (!soundState.enabled) return null;
  try {
    ctx ??= new AudioContext();
    if (ctx.state === "suspended") void ctx.resume();
    return ctx;
  } catch {
    return null;
  }
}

const MAJOR = [0, 2, 4, 5, 7, 9, 11]; // ド レ ミ ファ ソ ラ シ
const hz = (m: number) => 440 * 2 ** ((m - 69) / 12);

function tone(c: AudioContext, f: number, start: number, decay: number, gain: number, slide = false) {
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = "sine";
  o.frequency.setValueAtTime(slide ? f * 0.6 : f, start);
  if (slide) o.frequency.exponentialRampToValueAtTime(f, start + 0.012);
  g.gain.setValueAtTime(0.0001, start);
  g.gain.exponentialRampToValueAtTime(gain, start + 0.004);
  g.gain.exponentialRampToValueAtTime(0.0001, start + decay);
  o.connect(g).connect(c.destination);
  o.start(start);
  o.stop(start + decay + 0.05);
}

/** step=0,1,2,… が ド,レ,ミ,… */
export function pop(step: number) {
  const c = ac();
  if (!c) return;
  const s = ((step % 15) + 15) % 15;
  const f = hz(72 + 12 * Math.floor(s / 7) + MAJOR[s % 7]);
  const t = c.currentTime;
  tone(c, f, t, 0.22, 0.3, true);
  tone(c, f * 2, t, 0.12, 0.08, true);
}

export function chime() {
  const c = ac();
  if (!c) return;
  const t = c.currentTime;
  [76, 79, 84, 88, 91].forEach((m, k) => {
    tone(c, hz(m), t + k * 0.055, 0.9, 0.16);
    tone(c, hz(m) * 3, t + k * 0.055, 0.3, 0.04);
  });
}
