import cv2
import numpy as np
import mediapipe as mp

# Initialize Mediapipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Function to overlay transparent images (clothing)
def overlay_transparent(background, overlay, x, y):
    overlay_h, overlay_w = overlay.shape[:2]

    # Ensure overlay does not exceed frame size
    if x + overlay_w > background.shape[1] or y + overlay_h > background.shape[0]:
        return background

    overlay_rgb = overlay[:, :, :3]  # Extract RGB channels
    alpha_mask = overlay[:, :, 3] / 255.0  # Normalize alpha (0 to 1)

    roi = background[y:y+overlay_h, x:x+overlay_w]

    # Blend overlay with background using the alpha channel
    for c in range(3):  
        roi[:, :, c] = (1 - alpha_mask) * roi[:, :, c] + alpha_mask * overlay_rgb[:, :, c]

    background[y:y+overlay_h, x:x+overlay_w] = roi
    return background

def virtual_try_on():
    cap = cv2.VideoCapture(0)  # Open webcam
    
    # Load t-shirt and pants images (replace with correct paths)
    tshirt_path = r"C:\Users\venka\OneDrive\Desktop\tshirtrn.png"
    pants_path = r"C:\Users\venka\OneDrive\Desktop\pants.png"
    
    tshirt = cv2.imread(tshirt_path, cv2.IMREAD_UNCHANGED)  # Load transparent t-shirt image
    pants = cv2.imread(pants_path, cv2.IMREAD_UNCHANGED)  # Load transparent pants image

    if tshirt is None or pants is None:
        print(f"Error: Could not load clothing images. Check the file paths.")
        return

    while True:
        ret, frame = cap.read()

        # If frame is not successfully read, continue without exiting
        if not ret:
            print("Error: Unable to read from webcam. Continuing...")
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # T-shirt: Using shoulder landmarks (LEFT_SHOULDER, RIGHT_SHOULDER)
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            img_h, img_w, _ = frame.shape
            x1, y1 = int(left_shoulder.x * img_w), int(left_shoulder.y * img_h)
            x2, y2 = int(right_shoulder.x * img_w), int(right_shoulder.y * img_h)

            tshirt_width = max(int(abs(x2 - x1) * 1.4), 1)  
            tshirt_height = max(int(tshirt.shape[0] * (tshirt_width / tshirt.shape[1])), 1)

            tshirt_resized = cv2.resize(tshirt, (tshirt_width, tshirt_height))

            x_center = (x1 + x2) // 2
            x_pos = x_center - (tshirt_width // 2)

            y_pos = min(y1, y2) - tshirt_height // 8

            frame = overlay_transparent(frame, tshirt_resized, x_pos, y_pos)

            # Pants: Using hip landmarks (LEFT_HIP, RIGHT_HIP)
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

            x1, y1 = int(left_hip.x * img_w), int(left_hip.y * img_h)
            x2, y2 = int(right_hip.x * img_w), int(right_hip.y * img_h)

            pants_width = max(int(abs(x2 - x1) * 1.8), 1)  
            pants_height = max(int(pants.shape[0] * (pants_width / pants.shape[1])), 1)

            pants_resized = cv2.resize(pants, (pants_width, pants_height))

            x_center = (x1 + x2) // 2
            x_pos = x_center - (pants_width // 2)

            y_pos = min(y1, y2)  # Position pants just below the hips

            frame = overlay_transparent(frame, pants_resized, x_pos, y_pos)

        # If no person detected, just show the webcam feed (without overlay)
        else:
            print("No person detected, continuing...")  

        cv2.imshow("Virtual Try-On", frame)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):  
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the virtual try-on application for both t-shirt and pants
virtual_try_on()