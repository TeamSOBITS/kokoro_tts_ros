from launch import LaunchDescription 
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch_ros.parameter_descriptions import ParameterValue 

def generate_launch_description():
    return LaunchDescription([ 
        DeclareLaunchArgument(
            'lang_code',
            default_value='a',
            description='Language code'

            # 🇺🇸 'a' => アメリカ英語, 🇬🇧 'b' => イギリス英語
            # 🇯🇵 'j' => 日本語
            # 🇪🇸 'e' => スペイン語
            # 🇫🇷 'f' => フランス語
            # 🇮🇳 'h' => ヒンディー語
            # 🇮🇹 'i' => イタリア語
            # 🇧🇷 'p' => ブラジルのポルトガル語
            # 🇨🇳 'z' => 中国語(普通話): pip3 install misaki[zh]
        ),
        DeclareLaunchArgument(
            'voice',
            default_value='af_heart',
            description='Speaker model'

            # 🇺🇸 アメリカ英語：af_heart
            # 🇬🇧 イギリス英語：bf_isabella
            # 🇯🇵 日本語      ：jf_alpha
            # 🇪🇸 スペイン語  ：ef_dora
            # 🇫🇷 フランス語  ：ff_siwis
            # 🇮🇳 ヒンディー語：hf_alpha	
            # 🇮🇹 イタリア語  ：if_sara
            # 🇧🇷 ブラジルのポルトガル語：pf_dora
            # 🇨🇳 中国語(普通話)：zf_xiaobei
        ),
        DeclareLaunchArgument(
            'speech_speed',
            default_value='1.0',
            description='Speech speed'
        ),
        DeclareLaunchArgument(
            'split_regex',
            default_value= r'[\n,.!?、。！？]+',
            description='Regular expression to split text'
        ),

        Node(
            package='kokoro_tts_ros',
            executable='kokoro_tts_server',
            name='kokoro_tts_action_server',
            parameters=[
                {'lang_code': LaunchConfiguration('lang_code')},
                {'voice': LaunchConfiguration('voice')},
                {'speech_speed': LaunchConfiguration('speech_speed')},
                {'split_regex': ParameterValue(LaunchConfiguration('split_regex'), value_type=str)}, # ParameterValue で文字列として明示的に指定
            ],
            output='screen'
        ),
    ])