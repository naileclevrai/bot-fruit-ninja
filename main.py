import time
import cv2
import numpy as np
from ultralytics import YOLO
import dxcam
from pynput.mouse import Controller, Button
from math import hypot
from collections import deque

model = YOLO('runs/detect/train3/weights/best.pt')
camera = dxcam.create()
REGION = (0, 0, 1280, 720)

mouse = Controller()

BOMB_SAFE_RADIUS = 150
SLICE_STEPS = 10
SLICE_SLEEP_TIME = 0.0005
FPS_LIMIT = 60
FRAME_TIME = 1.0 / FPS_LIMIT

active_targets = {}
TARGET_TIMEOUT = 5

# Pour le calcul des FPS
fps_history = deque(maxlen=30)
last_frame_time = time.time()

# Pour le suivi des positions
previous_positions = {}
MAX_HISTORY = 5

def move_and_slice(start_x, start_y, end_x, end_y):
    dx = (end_x - start_x) / SLICE_STEPS
    dy = (end_y - start_y) / SLICE_STEPS

    mouse.position = (int(start_x), int(start_y))
    mouse.press(Button.left)

    for i in range(SLICE_STEPS):
        current_x = start_x + dx * i
        current_y = start_y + dy * i
        mouse.position = (int(current_x), int(current_y))
        time.sleep(SLICE_SLEEP_TIME)

    mouse.release(Button.left)

def move_and_slice_pattern(cx, cy, bomb_positions, pattern_type="vertical"):
    length = 80
    height = 250
    offset = 20

    for bx, by in bomb_positions:
        distance = hypot(cx - bx, cy - by)
        if distance < BOMB_SAFE_RADIUS:
            return

    if pattern_type == "vertical":
        paths = [
            (cx - length//2, cy - height//2, cx + length//2, cy + height//2),
            (cx - length//2 + offset, cy - height//2, cx + length//2 + offset, cy + height//2),
            (cx - length//2 - offset, cy - height//2, cx + length//2 - offset, cy + height//2),
        ]
    elif pattern_type == "diagonal":
        paths = [
            (cx - length//2, cy - height//2, cx + length//2, cy + height//2),
            (cx - length//2, cy + height//2, cx + length//2, cy - height//2),
            (cx - length//2 + offset, cy - height//2, cx + length//2 + offset, cy + height//2),
        ]
    elif pattern_type == "x":
        paths = [
            (cx - length//2, cy - height//2, cx + length//2, cy + height//2),
            (cx - length//2, cy + height//2, cx + length//2, cy - height//2),
            (cx - height//2, cy - length//2, cx + height//2, cy + length//2),
            (cx - height//2, cy + length//2, cx + height//2, cy - length//2),
        ]

    for path in paths:
        sx, sy, ex, ey = path
        move_and_slice(sx, sy, ex, ey)

def predict_next_position(cx, cy, history):
    if len(history) < 2:
        return cx, cy
    
    # Calculer la vitesse moyenne
    dx = sum(x2 - x1 for x1, y1, x2, y2 in zip(history[:-1], history[1:]))
    dy = sum(y2 - y1 for x1, y1, x2, y2 in zip(history[:-1], history[1:]))
    
    # Prédire la position suivante
    predicted_x = cx + dx / (len(history) - 1)
    predicted_y = cy + dy / (len(history) - 1)
    
    return predicted_x, predicted_y

def update_target_history(cx, cy):
    if (cx, cy) not in previous_positions:
        previous_positions[(cx, cy)] = []
    
    history = previous_positions[(cx, cy)]
    history.append((cx, cy))
    
    if len(history) > MAX_HISTORY:
        history.pop(0)
    
    return history

def find_safe_targets(boxes, bomb_positions):
    safe_targets = []

    for box in boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        x1, y1, x2, y2 = box.xyxy[0]
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        if label == "bombe":
            bomb_positions.append((cx, cy))
        else:
            too_close = False
            for bx, by in bomb_positions:
                distance = hypot(cx - bx, cy - by)
                if distance < BOMB_SAFE_RADIUS:
                    too_close = True
                    break
            if not too_close:
                history = update_target_history(cx, cy)
                pred_x, pred_y = predict_next_position(cx, cy, history)
                safe_targets.append((int(pred_x), int(pred_y)))

    return safe_targets

def draw_overlay(img, results, bomb_positions, safe_targets, fps):
    # Copie de l'image pour l'overlay
    overlay = img.copy()
    
    # Dessiner les zones de sécurité des bombes
    for bx, by in bomb_positions:
        cv2.circle(overlay, (int(bx), int(by)), BOMB_SAFE_RADIUS, (0, 0, 255), 1)
    
    # Dessiner les cibles sûres
    for cx, cy in safe_targets:
        cv2.circle(overlay, (int(cx), int(cy)), 20, (0, 255, 0), 2)
    
    # Afficher les FPS
    cv2.putText(overlay, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Fusionner l'overlay avec l'image originale
    alpha = 0.3
    return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

def choose_best_pattern(cx, cy, current_targets):
    # Si plusieurs cibles sont proches, utiliser le pattern X
    nearby_targets = sum(1 for tx, ty in current_targets 
                        if hypot(cx - tx, cy - ty) < 100)
    
    if nearby_targets > 2:
        return "x"
    elif nearby_targets > 1:
        return "diagonal"
    else:
        return "vertical"

print("→ Le bot est lancé, faites [Ctrl+C] pour l'arrêter !")

try:
    while True:
        current_time = time.time()
        
        # Limiter les FPS
        if current_time - last_frame_time < FRAME_TIME:
            time.sleep(0.001)
            continue
            
        last_frame_time = current_time
        
        img = camera.grab(region=REGION)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        results = model.predict(source=img_bgr, conf=0.5, verbose=False)

        bomb_positions = []
        current_targets = []

        for r in results:
            boxes = r.boxes
            if boxes is not None and len(boxes) > 0:
                safe_targets = find_safe_targets(boxes, bomb_positions)
                current_targets.extend(safe_targets)

        # Nettoyer l'historique des positions
        current_positions = set((cx, cy) for cx, cy in current_targets)
        previous_positions = {k: v for k, v in previous_positions.items() if k in current_positions}

        updated_targets = {}
        for cx, cy in current_targets:
            key = (cx, cy)
            updated_targets[key] = active_targets.get(key, TARGET_TIMEOUT)

        active_targets = updated_targets

        for (cx, cy), timeout in active_targets.items():
            pattern = choose_best_pattern(cx, cy, current_targets)
            move_and_slice_pattern(cx, cy, bomb_positions, pattern)
            active_targets[(cx, cy)] = timeout - 1

        active_targets = {k: v for k, v in active_targets.items() if v > 0}

        # Calculer les FPS
        fps_history.append(1.0 / (time.time() - current_time))
        current_fps = sum(fps_history) / len(fps_history)

        # Afficher l'overlay
        display_img = draw_overlay(img_bgr, results, bomb_positions, current_targets, current_fps)
        cv2.imshow("Fruit Ninja Bot", display_img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("Le bot est arrêté.")

cv2.destroyAllWindows()
