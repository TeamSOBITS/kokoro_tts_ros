<a name="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

# Kokoro TTS for ROS

<!-- 目次 -->
<details>
  <summary>目次</summary>
  <ol>
    <li>
      <a href="#概要">概要</a>
    </li>
    <li>
      <a href="#環境構築">環境構築</a>
      <ul>
        <li><a href="#環境条件">環境条件</a></li>
        <li><a href="#インストール方法">インストール方法</a></li>          
      </ul>
    </li>
    <li><a href="#実行操作方法">実行・操作方法</a></li>
    <li><a href="#対応言語">対応言語</a></li>
    <li><a href="#話者">話者</a></li>
    <li><a href="#発話速度">発話速度</a></li>
    <li><a href="#区切る文字">区切る文字</a></li>
    <li><a href="#マイルストーン">マイルストーン</a></li>
    <!-- <li><a href="#contributing">Contributing</a></li> -->
    <!-- <li><a href="#license">License</a></li> -->
    <li><a href="#参考文献">参考文献</a></li>
  </ol>
</details>


<!-- レポジトリの概要 -->
## 概要
Kokoroは，8,200万のパラメータを持つオープンウェイトのTTS（Text-to-Speech：音声合成）モデルです．\
軽量なアーキテクチャにもかかわらず，大規模モデルに匹敵する品質を実現し，同時に処理速度とコスト効率を大幅に向上させています．\
本リポジトリは，KokoroをROS2環境でアクション通信に対応させたものです．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- 環境構築 -->
## 環境構築
ここで，本レポジトリのセットアップ方法について説明します．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### 環境条件

まず，以下の環境を整えてから，次のインストール段階に進んでください．
| System  | Version |
| --- | --- |
| Ubuntu | 22.04 (Jammy Jellyfish) |
| ROS    | Humble Hawksbill |
| Python | 3.10 |

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### インストール方法
1. ROS2の`src`フォルダに移動します．
    ```sh
    cd ~/colcon_ws/src/
    ```

2. 本レポジトリをcloneします．
    ```sh
    git clone https://github.com/TeamSOBITS/kokoro_tts_ros.git
    ```
3. レポジトリの中へ移動します．
    ```sh
    cd kokoro_tts_ros/
    ```
4. 依存パッケージをインストールします．時間がかかるので注意．
    ```sh
    bash install.sh
5. パッケージをコンパイルします．
    ```sh
    cd ~/colcon_ws/
    ```
    ```sh
    colcon build --symlink-install
    ```
    ```sh
    source ~/colcon_ws/install/setup.sh
    ```

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- 実行・操作方法 -->
## 実行・操作方法
1. アクションサーバーを起動します．**Ready to kokoro TTS**と表示されるまでgoalを送らずに待機してください．
   ```sh
   ros2 launch kokoro_tts_ros kokoro_tts_server.launch.py 
   ```
2. アクションクライアントを起動し，発話させたい文字を送信します．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## 対応言語
kokoro_ttsは以下の言語に対応しています．\
[kokoro_tts_server.launch.py](launch/kokoro_tts_server.launch.py)の**lang_code**を使用する言語に書き換えてください．

| 対応言語  | lang_code |
| ----- | ----- |
| アメリカ英語 | a |
| イギリス英語 | b |
| 日本語 | j |
| スペイン語 | e |
| フランス語 |f  |
| ヒンディー語 | h |
| イタリア語 | i |
| ブラジルのポルトガル語 | p |
| 中国語(普通話) | z |

* 中国語を使用する際は以下のコードを実行してください．
    ```sh
    pip3 install misaki[zh]==0.9.4
    ```
<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## 話者
kokoro_ttsは言語別で様々な話者に対応しています．\
[kokoro_tts_server.launch.py](launch/kokoro_tts_server.launch.py)の**voice**を使用する言語に書き換えてください．\
以下はその一例です．


- アメリカ英語
    - 女性
        - af_heart
        - af_bella
    - 男性
        - am_fenrir
        - am_puck
- 日本語
    - 女性
        - jf_alpha
    - 男性
        - jm_kumo

アメリカ英語や日本語，他の言語では，より多くの話者を指定できます．\
使用したい場合は[こちら](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)を参考にしてください．

> 日本語を外国人が話しているように発話させることもできます．その場合は以下のように設定してください．
> - 言語(lang_code)：日本語
> - 話者(voice)：英語の話者
> - 発話するテキスト：日本語

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## 発話速度
発話する速度を変更する場合は，[kokoro_tts_server.launch.py](launch/kokoro_tts_server.launch.py)の**speech_speed**を書き換えてください．(デフォルト値：1.0)

例：1.2倍にしたい場合
```sh
DeclareLaunchArgument(
    'speech_speed',
    default_value='1.2',    #ここを書き換える
    description='Speech speed'
),
```
<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## 区切る文字
特定の文字で区切らせて発話させる場合は，[kokoro_tts_server.launch.py](launch/kokoro_tts_server.launch.py)の**split_regex**を書き換えてください．(デフォルト値：**r'[\n,.!?、。！？]+'**)

例：*で区切らせたい場合
```sh
DeclareLaunchArgument(
    'split_regex',
    default_value= r'[\n,.!?、。！？*]+',    #ここを修正する
    description='Regular expression to split text'
),
```

<!-- マイルストーン -->
## マイルストーン
現時点のbugや新規機能の依頼を確認するために[Issueページ][issues-url] をご覧ください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- 参考文献 -->
## 参考文献
[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/TeamSOBITS/kokoro_tts_ros.svg?style=for-the-badge
[contributors-url]: https://github.com/TeamSOBITS/kokoro_tts_ros/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/TeamSOBITS/kokoro_tts_ros.svg?style=for-the-badge
[forks-url]: https://github.com/TeamSOBITS/kokoro_tts_ros/network/members
[stars-shield]: https://img.shields.io/github/stars/TeamSOBITS/kokoro_tts_ros.svg?style=for-the-badge
[stars-url]: https://github.com/TeamSOBITS/kokoro_tts_ros/stargazers
[issues-shield]: https://img.shields.io/github/issues/TeamSOBITS/kokoro_tts_ros.svg?style=for-the-badge
[issues-url]: https://github.com/TeamSOBITS/kokoro_tts_ros/issues
[license-shield]: https://img.shields.io/github/license/TeamSOBITS/kokoro_tts_ros.svg?style=for-the-badge
[license-url]: LICENSE
