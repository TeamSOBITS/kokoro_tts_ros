#!/bin/bash
echo "╔══╣ Install: kokoro_tts_ros (STARTING) ╠══╗"

set -e  # 途中で失敗したら即終了

# apt の自動確認スキップ
export DEBIAN_FRONTEND=noninteractive

sudo apt update -y

sudo apt install -y ros-humble-vision-msgs espeak-ng

# Python パッケージのインストールと整備
pip3 install -q soundfile pygame

# kokoro および misaki TTS ライブラリ
pip3 install -q kokoro==0.9.4
pip3 install -q 'misaki[en,ja]==0.9.4'

pip3 uninstall -y fugashi unidic unidic-lite
pip3 install -q fugashi unidic-lite

# ROS パッケージのクローン
cd ~/colcon_ws/src/
if [ ! -d "sobits_msgs" ]; then
    git clone -b humble-devel https://github.com/TeamSOBITS/sobits_msgs.git
else
    echo "sobits_msgs リポジトリはすでに存在します。スキップします。"
fi

echo "╚══╣ Install: kokoro_tts_ros (FINISHED) ╠══╝"
