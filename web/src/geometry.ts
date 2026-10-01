// 横線 nH 本（上から 0,1,..）と、右に傾いた縦線 nS 本（左から 0,1,..）の格子。SVG 座標（y は下向き）。

export const VIEW = { w: 600, h: 420 };

export type Pt = [number, number];

export interface Geo {
  nH: number;
  nS: number;
  pt: (i: number, j: number) => Pt;
  hLine: (i: number) => [Pt, Pt];
  sLine: (j: number) => [Pt, Pt];
  para: (i1: number, i2: number, j1: number, j2: number) => string;
}

export function geometry(nH: number, nS: number, slant = 0.35, ext = 16): Geo {
  const x0 = 60, x1 = 540, y0 = 40, y1 = 370;
  const yc = (y0 + y1) / 2;
  const shift = slant * (y1 - y0);
  const ys = (i: number) => y0 + ((y1 - y0) * i) / (nH - 1);
  const cs = (j: number) => x0 + shift / 2 + ((x1 - x0 - shift) * j) / (nS - 1);
  const pt = (i: number, j: number): Pt => {
    const y = ys(i);
    return [cs(j) + slant * (yc - y), y];
  };
  const len = Math.hypot(slant, 1);
  return {
    nH,
    nS,
    pt,
    hLine: (i) => {
      const [ax, ay] = pt(i, 0);
      const [bx, by] = pt(i, nS - 1);
      return [[ax - ext, ay], [bx + ext, by]];
    },
    sLine: (j) => {
      const [ax, ay] = pt(nH - 1, j);
      const [bx, by] = pt(0, j);
      const dx = (slant / len) * ext, dy = ext / len;
      return [[ax - dx, ay + dy], [bx + dx, by - dy]];
    },
    para: (i1, i2, j1, j2) =>
      [pt(i1, j1), pt(i1, j2), pt(i2, j2), pt(i2, j1)].map((p) => p.join(",")).join(" "),
  };
}

export const choose2 = (n: number) => (n * (n - 1)) / 2;
