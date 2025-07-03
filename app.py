import cv2
import mediapipe as mp
import time
import pyttsx3  # 🔊 Voice engine

# Initialize voice engine
engine = pyttsx3.init()

# MediaPipe Hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Input tracking
input_sequence = ""
last_input_time = 0
cooldown = 1.5

# Operator mapping for left hand
operator_map = {
    1: '+',
    2: '-',
    3: '*',
    4: '/',
}

def count_fingers(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb (based on x)
    if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other 4 fingers (based on y)
    for i in range(1, 5):
        if hand_landmarks.landmark[tips[i]].y < hand_landmarks.landmark[tips[i] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return sum(fingers)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks and results.multi_handedness:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_type = results.multi_handedness[i].classification[0].label
            finger_count = count_fingers(hand_landmarks)

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if time.time() - last_input_time > cooldown:
                if hand_type == "Right" and 1 <= finger_count <= 5:
                    input_sequence += str(finger_count)
                    last_input_time = time.time()
                elif hand_type == "Left":
                    if finger_count in operator_map:
                        input_sequence += operator_map[finger_count]
                        last_input_time = time.time()
                    elif finger_count == 0:
                        input_sequence = ""
                        print("🔄 Input cleared!")
                        engine.say("Input cleared")
                        engine.runAndWait()
                        last_input_time = time.time()

    # Show input
    y = 40
    cv2.putText(frame, "Input:", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    y += 40
    for i in range(0, len(input_sequence), 30):
        line = input_sequence[i:i + 30]
        cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        y += 40

    cv2.imshow("Air Gesture Calculator", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('='):
        try:
            result = eval(input_sequence)
            print(f"Result: {result}")
            engine.say(f"The result is {result}")
            engine.runAndWait()
            input_sequence = str(result)
        except:
            print("❌ Error in expression")
            engine.say("Error in expression")
            engine.runAndWait()
            input_sequence = ""
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
