import cv2
import numpy as np
import mediapipe as mp

# Initialize Mediapipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def overlay_transparent(background, overlay, x, y):
    """
    Overlay transparent PNG onto another image at position (x, y).
    """
    overlay_h, overlay_w = overlay.shape[:2]

    # Ensure overlay does not exceed frame size
    if x + overlay_w > background.shape[1] or y + overlay_h > background.shape[0]:
        return background

    overlay_rgb = overlay[:, :, :3]  # Extract RGB channels
    alpha_mask = overlay[:, :, 3] / 255.0  # Normalize alpha (0 to 1)

    roi = background[y:y+overlay_h, x:x+overlay_w]

    # Blend overlay with background using the alpha channel
    for c in range(3):  # Loop over color channels (BGR)
        roi[:, :, c] = (1 - alpha_mask) * roi[:, :, c] + alpha_mask * overlay_rgb[:, :, c]

    background[y:y+overlay_h, x:x+overlay_w] = roi
    return background

def virtual_try_on():
    cap = cv2.VideoCapture(0)  # Open webcam
    clothing = cv2.imread("clothing.png", cv2.IMREAD_UNCHANGED)  # Load transparent clothing image

    if clothing is None:
        print("Error: Could not load clothing image.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to RGB for Mediapipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Get Shoulder Points
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            # Convert normalized coordinates to pixels
            img_h, img_w, _ = frame.shape
            x1, y1 = int(left_shoulder.x * img_w), int(left_shoulder.y * img_h)
            x2, y2 = int(right_shoulder.x * img_w), int(right_shoulder.y * img_h)

            # Determine width of clothing based on shoulder distance
            clothing_width = abs(x2 - x1) + 50
            clothing_height = int(clothing.shape[0] * (clothing_width / clothing.shape[1]))

            # Resize clothing to fit
            clothing_resized = cv2.resize(clothing, (clothing_width, clothing_height))

            # Position the clothing at the shoulders
            x_pos = x1 - 25
            y_pos = y1

            # Overlay clothing
            frame = overlay_transparent(frame, clothing_resized, x_pos, y_pos)

        cv2.imshow("Virtual Try-On", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the virtual try-on application
virtual_try_on()
