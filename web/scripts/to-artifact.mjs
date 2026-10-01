// dist/index.html（完全な HTML）を、Artifact 用の断片 dist/artifact.html に変換する。
// Artifact は公開時に <!doctype><html><head><body> で包まれるため、中身だけを並べる。
import { readFileSync, writeFileSync } from "node:fs";

const html = readFileSync("dist/index.html", "utf8");
const pick = (re) => [...html.matchAll(re)].map((m) => m[0]);

const title = pick(/<title>[\s\S]*?<\/title>/g);
const links = pick(/<link [^>]*fonts\.(googleapis|gstatic)[^>]*>/g);
const styles = pick(/<style[^>]*>[\s\S]*?<\/style>/g);
const scripts = pick(/<script[^>]*>[\s\S]*?<\/script>/g);
const body = html.match(/<body[^>]*>([\s\S]*?)<\/body>/)[1].replace(/<script[\s\S]*?<\/script>/g, "").trim();

const out = [...title, ...links, ...styles, body, ...scripts].join("\n");
writeFileSync("dist/artifact.html", out);
console.log(`dist/artifact.html (${(out.length / 1024).toFixed(0)} KB)`);
