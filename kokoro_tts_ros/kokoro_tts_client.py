
#!/usr/bin/env python3
# -*- coding: utf-8 -*- #

import rclpy
from rclpy.action import ActionClient
from sobits_interfaces.action import TextToSpeech  # sobits_msgs/action/TextToSpeech.action

def tts_action(node, text):
    """
    Sends text to the server using an ActionClient and retrieves the result.
    """
    # Create an ActionClient
    action_client = ActionClient(node, TextToSpeech, '/speech_word')

    # Wait for the server to be ready
    node.get_logger().info('Waiting for the action server...')
    action_client.wait_for_server()

    # Create a goal message
    goal_msg = TextToSpeech.Goal()
    goal_msg.text = text

    # Send the goal and wait for the result
    node.get_logger().info(f'Sending goal: "{text}"')
    future = action_client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(node, future)

    # Check if the goal was accepted
    goal_handle = future.result()
    if not goal_handle.accepted:
        node.get_logger().error('Goal was rejected.')
        return

    # Wait for the result
    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future)
    result = result_future.result().result

    # Display the result
    if result.success:
        node.get_logger().info('Text-to-speech succeeded!')
    else:
        node.get_logger().error('Text-to-speech failed.')

def main():
    rclpy.init()
    node = rclpy.create_node('text_to_speech_client')

    try:
        while True:
            input_text = input('Enter text for speech synthesis ("EXIT" to quit): ')
            if input_text.strip() == 'EXIT':
                print('Exiting the program.')
                break
            if not input_text.strip():
                print('Input is empty. Please enter text.')
                continue

            tts_action(node, input_text)

    except KeyboardInterrupt:
        print('\nProgram interrupted by user.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
