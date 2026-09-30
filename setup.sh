#!/usr/bin/env bash
# Manim 実行環境のセットアップ（Debian/Ubuntu 系）
set -euo pipefail
cd "$(dirname "$0")"

SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

# システム依存: Cairo/Pango（描画）, ffmpeg（動画）, LaTeX（数式）, 日本語フォント
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq \
  build-essential python3-dev python3-venv pkg-config \
  libcairo2-dev libpango1.0-dev ffmpeg \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended \
  texlive-lang-japanese cm-super dvisvgm \
  fonts-ipaexfont

# Python 仮想環境
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/pip install -q -U pip setuptools wheel
.venv/bin/pip install -q -r requirements.txt

.venv/bin/manim --version
echo "セットアップ完了: source .venv/bin/activate"
