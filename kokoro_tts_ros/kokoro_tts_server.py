import rclpy
from rclpy.node import Node
import pygame

from sobits_interfaces.action import TextToSpeech 
from rclpy.action import ActionServer, GoalResponse, CancelResponse 

from kokoro import KPipeline # テキストから音声を生成する「kokoro」ライブラリのパイプライン
import numpy as np 
import soundfile as sf # 音声ファイルを扱うためのライブラリ
import torch # PyTorchライブラリ（GPU利用の有無を判断するために使用）
import time # 時間関連の操作
import io # インメモリのバイトストリームを扱うため

class KokoroTTSActionServer(Node):
    def __init__(self, device=None):
        super().__init__('kokoro_tts_action_server')
        
        # ROSパラメータの宣言
        self.declare_parameter('lang_code', 'a') # 言語コード 
        self.declare_parameter('voice', 'af_heart') # 使用する音声モデル
        self.declare_parameter('speech_speed', 1.0) # 音声の再生速度
        self.declare_parameter('split_regex', r'[\n,.!?、。！？]+') # テキストを分割するための正規表現

        # 宣言したパラメータの値を取得
        self.lang_code = self.get_parameter('lang_code').get_parameter_value().string_value
        self.voice = self.get_parameter('voice').get_parameter_value().string_value
        self.speech_speed = self.get_parameter('speech_speed').get_parameter_value().double_value
        self.split_regex = self.get_parameter('split_regex').get_parameter_value().string_value

        # デバイスの決定: GPUが利用可能ならCUDA、そうでなければCPUを使用
        self.device = device if device else "cuda:0" if torch.cuda.is_available() else "cpu"
        self.get_logger().debug(f"Using device: {self.device}") # デバッグログでデバイス情報を出力

        # KPipelineの初期化
        try:
            self.pipeline = KPipeline(lang_code=self.lang_code, device=self.device)
        except Exception as e:
            self.get_logger().error(f"Failed to initialize KPipeline: {e}") # 初期化失敗時のエラーログ
            raise # 初期化に失敗したら例外を再送出し、ノード起動を停止

        self.sample_rate = 24000 # 音声のサンプルレート

        self._mixer_initialized = False # Pygameミキサーが初期化されたかどうかのフラグ
        # Pygameミキサーの初期化
        try:
            # frequency: サンプルレート, size: サンプルあたりのビット数 (-16は符号付き16ビット), channels: チャンネル数 (1はモノラル), buffer: バッファサイズ
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self.get_logger().info("Pygame mixer initialized.") # 初期化成功ログ
            self._mixer_initialized = True
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Pygame mixer: {e}") # 初期化失敗ログ

        # アクションサーバーの作成
        self._action_server = ActionServer(
            self, # ノードインスタンス
            TextToSpeech, # 使用するアクションインターフェース
            'speech_word', # アクション名
            execute_callback=self.execute_callback, # ゴール実行時に呼び出されるコールバック
            goal_callback=self.goal_callback,       # ゴールリクエスト受信時に呼び出されるコールバック
            cancel_callback=self.cancel_callback)   # キャンセルリクエスト受信時に呼び出されるコールバック

        self.get_logger().info(f"Ready to kokoro TTS (Lang: {self.lang_code}, Voice: {self.voice})") # ノードの準備完了ログ

    # ノードが破棄される際のクリーンアップ処理
    def destroy_node(self):
        self.get_logger().info('Shutting down kokoro TTS action server...')
        if pygame.mixer.get_init(): # Pygameミキサーが初期化されているか確認
            try:
                pygame.mixer.music.stop() # 念のため再生中の音楽を停止
                pygame.mixer.quit() # Pygameミキサーを終了
                self.get_logger().info('Pygame mixer quit.')
            except Exception as e:
                 self.get_logger().error(f"Error quitting Pygame mixer: {e}")
        super().destroy_node() # 親クラスのdestroy_nodeを呼び出し
    
    # ゴールリクエスト受信時のコールバック
    def goal_callback(self, goal_request):
        self.get_logger().debug(f"Received goal request with text: '{goal_request.text}'")
        # Pygameミキサーが初期化されていない場合、ゴールを拒否
        if not self._mixer_initialized:
            self.get_logger().error("Pygame mixer not initialized. Rejecting goal.")
            return GoalResponse.REJECT
        # KPipelineが初期化されていない場合、ゴールを拒否
        if self.pipeline is None:
            self.get_logger().error("KPipeline not initialized. Rejecting goal.")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT # ゴールを受け入れ

    # キャンセルリクエスト受信時のコールバック
    def cancel_callback(self, goal_handle):
        self.get_logger().debug('Received cancel request.')
        return CancelResponse.ACCEPT # キャンセルリクエストを受け入れ

    # ゴール実行時のコールバック
    def execute_callback(self, goal_handle):
        feedback = TextToSpeech.Feedback() # フィードバックメッセージのインスタンス
        response = TextToSpeech.Result() # 結果メッセージのインスタンス

        text = goal_handle.request.text # ゴールリクエストからテキストを取得

        # 入力テキストのバリデーション (文字列であること、空でないこと)
        if not isinstance(text, str) or not text.strip():
            self.get_logger().error(f"Input text is empty, blank, or not a string. Received: '{text}'")
            response.success = False
            goal_handle.abort() # ゴールを中断
            return response
        
        self.get_logger().info(f"Processing text: [{text}] (Language: {self.lang_code}, Voice: {self.voice}, Speed: {self.speech_speed})")

        # Pygameミキサーが初期化されていない場合、エラーとして終了
        if not pygame.mixer.get_init():
            self.get_logger().error("Pygame mixer is not initialized. Cannot play audio.")
            response.success = False
            goal_handle.abort()
            return response

        response.success = False # デフォルトは失敗

        play_time = 0.0 # 推定再生時間
        audio_buffer = None # 音声データが格納されるバッファ

        try:
            # 音声バッファの生成
            play_time, audio_buffer = self._generate_audio_buffer(text)

            # 音声バッファの生成失敗または再生時間が無効な場合
            if audio_buffer is None or play_time <= 0:
                self.get_logger().error("Audio buffer generation failed or invalid play time.")
                response.success = False
                goal_handle.abort()
                return response
            
            pygame.mixer.music.load(audio_buffer) # 音声バッファをミキサーにロード
            pygame.mixer.music.play() # 音声再生開始
            
            start_playback_loop_time = time.time() # 再生開始時刻を記録
            feedback.remaining_time = play_time # 初期残り時間を設定

            # 音声再生中のループ
            while pygame.mixer.music.get_busy(): # ミキサーがビジー（再生中）の間ループ
                if goal_handle.is_cancel_requested: # キャンセルリクエストがあるか確認
                    self.get_logger().info('Goal canceled during playback.')
                    pygame.mixer.music.stop() # 音声再生を停止
                    goal_handle.canceled() # ゴールをキャンセル状態に設定
                    response.success = False # キャンセルは成功ではないとみなす
                    return response # ここで処理を終了

                current_time_in_loop = time.time()
                elapsed_in_loop = current_time_in_loop - start_playback_loop_time # 再生経過時間
                response.total_time = elapsed_in_loop # 現時点での再生経過時間を結果に設定
                feedback.remaining_time = play_time - elapsed_in_loop # 残り時間を計算

                if feedback.remaining_time < 0:
                    feedback.remaining_time = 0.0 # 残り時間が負にならないように調整
                
                goal_handle.publish_feedback(feedback) # フィードバックを公開

                # ループの頻度を調整するための短いスリープ
                # これによりCPU使用率を抑える
                time.sleep(0.05) # 50ミリ秒ごとにフィードバックを更新 (例)

            # ループが終了した後の処理（再生が終了したか、予期せず停止した場合）
            final_elapsed_time = time.time() - start_playback_loop_time # 実際の再生にかかった時間
            response.total_time = final_elapsed_time # 最終的な再生時間を結果に設定
            
            # 再生時間と実経過時間の誤差を考慮し、成功と判断
            if abs(play_time - final_elapsed_time) < 0.5 : # 0.5秒程度の誤差は許容
                 self.get_logger().info(f"Playback completed. Estimated: {play_time:.2f}s, Actual: {final_elapsed_time:.2f}s")
                 response.success = True
                 goal_handle.succeed() # ゴールを成功状態に設定
            elif final_elapsed_time >= play_time: # 推定時間以上再生されていればOKとする場合
                 self.get_logger().info(f"Playback ostensibly completed. Estimated: {play_time:.2f}s, Actual: {final_elapsed_time:.2f}s")
                 response.success = True
                 goal_handle.succeed() # ゴールを成功状態に設定
            else:
                 # 予期せぬ理由で早く停止した場合
                 self.get_logger().warn(f"Playback ended prematurely or unexpectedly. Estimated: {play_time:.2f}s, Actual: {final_elapsed_time:.2f}s")
                 response.success = False
                 goal_handle.abort() # ゴールを中断

            # 最後のフィードバック (残り時間0)
            feedback.remaining_time = 0.0
            goal_handle.publish_feedback(feedback)

        # Pygameエラーのハンドリング
        except pygame.error as e:
            self.get_logger().error(f"Pygame error during playback: {e}")
            response.success = False
            goal_handle.abort()
        # KPipeline関連など、実行時のエラーのハンドリング
        except RuntimeError as e:
            self.get_logger().error(f"Runtime error during TTS processing: {e}")
            response.success = False
            goal_handle.abort()
        # その他の予期せぬエラーのハンドリング
        except Exception as e:
            self.get_logger().error(f"An unexpected error occurred in execute_callback: {e}", exc_info=True)
            response.success = False
            goal_handle.abort()
        
        return response

    # 音声バッファを生成するプライベートメソッド
    def _generate_audio_buffer(self, text):
        if self.pipeline is None: # KPipelineが初期化されていない場合のガード
            self.get_logger().error("KPipeline is not initialized. Cannot generate audio.")
            return 0.0, None

        combined_audio_chunks = [] # 生成された音声チャンクを格納するリスト
        total_samples = 0 # 総サンプル数

        try:
            # KPipelineを使用してテキストから音声を生成
            for i, result in enumerate(self.pipeline(text, voice=self.voice, speed=self.speech_speed, split_pattern=self.split_regex)):
                self.get_logger().debug(f"Processing audio chunk {i}...")
                audio_chunk = result.audio # 生成された音声データ

                # 音声データがPyTorchテンソルであればNumPy配列に変換
                if isinstance(audio_chunk, torch.Tensor):
                    audio_chunk = audio_chunk.cpu().numpy()
                # 音声データがリストまたはタプルであれば各要素を処理
                elif isinstance(audio_chunk, (list, tuple)):
                    processed_elements = []
                    for x in audio_chunk:
                        if isinstance(x, torch.Tensor):
                            processed_elements.append(x.cpu().numpy().squeeze())
                        else:
                            # NumPy配列でない場合、かつsqueeze可能な場合はsqueeze
                            try:
                                processed_elements.append(np.squeeze(x))
                            except:
                                self.get_logger().warn(f"Could not squeeze element: {type(x)}")
                                processed_elements.append(x) # そのまま追加
                    # 処理された要素をNumPy配列にスタック
                    try:
                        audio_chunk = np.stack(processed_elements, axis=0)
                    except ValueError as e:
                        self.get_logger().error(f"Error stacking audio chunks: {e}. Elements: {[type(el) for el in processed_elements]}")
                        return 0.0, None

                # 音声チャンクの次元を調整
                if audio_chunk.ndim == 1:
                    final_chunk = audio_chunk
                elif audio_chunk.ndim == 2:
                    # 2次元の場合、行数が列数より少なければ転置 (例: (1, N) -> (N, 1))
                    final_chunk = audio_chunk.T if audio_chunk.shape[0] < audio_chunk.shape[1] else audio_chunk
                else:
                    self.get_logger().error(f"Unsupported audio chunk shape: {audio_chunk.shape}. Expected 1D or 2D.")
                    return 0.0, None

                combined_audio_chunks.append(final_chunk) # 処理済みチャンクを追加
                total_samples += final_chunk.shape[0] # 総サンプル数を加算
            
        except Exception as e:
            self.get_logger().error(f"Error during KPipeline processing: {e}", exc_info=True)
            return 0.0, None

        # 音声チャンクが何も生成されなかった場合
        if not combined_audio_chunks:
            self.get_logger().warn("No audio chunks generated for the given text.")
            return 0.0, None

        try:
            # すべての音声チャンクを結合
            combined_audio = np.concatenate(combined_audio_chunks, axis=0)
        except ValueError as e:
             self.get_logger().error(f"Error concatenating audio chunks: {e}. Shapes: {[ch.shape for ch in combined_audio_chunks]}", exc_info=True)
             return 0.0, None

        # 推定再生時間の計算
        play_time = float(total_samples) / self.sample_rate
        self.get_logger().debug(f"Total estimated play time: {play_time:.2f} seconds for {total_samples} samples.")

        # 再生時間が無効な場合
        if play_time <= 0:
            self.get_logger().warn(f"Calculated play_time is zero or negative ({play_time:.2f}s).")
            return 0.0, None

        try:
            buffer = io.BytesIO() # インメモリのバイトストリームを作成
            # 音声データをWAV形式でバッファに書き込む
            # subtype='PCM_16' は16ビットPCM形式を指定
            sf.write(buffer, combined_audio, self.sample_rate, format='WAV', subtype='PCM_16')
            buffer.seek(0) # バッファの読み込み位置を先頭に戻す
            return play_time, buffer
        except Exception as e:
            self.get_logger().error(f"Error writing audio to buffer: {e}", exc_info=True)
            return 0.0, None

def main(args=None):
    rclpy.init(args=args)
    try:
        action_server = KokoroTTSActionServer() # アクションサーバーのインスタンスを作成
        rclpy.spin(action_server) # アクションサーバーをスピンさせ、コールバックを処理
    # 特定の実行時エラーのハンドリング (例: KPipelineやPygame Mixerの初期化失敗)
    except RuntimeError as e:
        if 'Failed to initialize' in str(e):
            Node('dummy_node_for_logging').get_logger().fatal(f"KokoroTTSActionServer could not be started: {e}")
        else:
            Node('dummy_node_for_logging').get_logger().fatal(f"Unhandled RuntimeError during KokoroTTSActionServer setup: {e}")
    except KeyboardInterrupt:
        pass # Ctrl+Cによる終了を捕捉
    except Exception as e:
        Node('dummy_node_for_logging').get_logger().fatal(f"An unexpected error occurred in main: {e}", exc_info=True)
    finally:
        # ROS 2がまだ実行中の場合、適切にシャットダウン
        if rclpy.ok():
             if 'action_server' in locals() and hasattr(action_server, 'is_initialized') and action_server.is_initialized:
                 action_server.destroy_node() # ノードを破棄
             rclpy.shutdown() # ROS 2をシャットダウン

if __name__ == "__main__":
    main()