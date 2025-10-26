import cv2
from pyzbar.pyzbar import decode
import time
import tkinter as tk

def scan_qr_code(app_root):
    """
    Opens the camera, scans for a QR code, decodes the content (Fragrance ID),
    and returns the ID as an integer.

    :param app_root: The main Tkinter root window to keep camera view on top.
    :return: Fragrance ID (int) or None if scanning fails or is cancelled.
    """
    # 0 is usually the default camera (built-in or first USB)
    cap = cv2.VideoCapture(0) 
    
    if not cap.isOpened():
        # Handle case where camera is not available
        tk.messagebox.showerror("Camera Error", "Could not open camera. Check if a camera is connected or in use.")
        return None

    # Create a simple window for the live camera feed
    window_name = "QR Code Scanner - Focus on Code"
    cv2.namedWindow(window_name)

    fragrance_id = None
    
    # Use 'app_root' to ensure the scanner window stays above the main application
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    # Set a timeout for scanning (e.g., 10 seconds)
    start_time = time.time()
    SCAN_TIMEOUT = 10
    
    # Loop to capture video frames and check for QR codes
    while (time.time() - start_time) < SCAN_TIMEOUT:
        ret, frame = cap.read()
        if not ret:
            break

        # Decode any QR codes found in the frame
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            try:
                # The data is the embedded text (Fragrance ID)
                data = obj.data.decode('utf-8')
                fragrance_id = int(data) 
                
                # Draw a green rectangle around the successfully decoded code
                points = obj.polygon
                if len(points) == 4:
                    pts = [(points[i].x, points[i].y) for i in range(4)]
                    for j in range(4):
                        cv2.line(frame, pts[j], pts[(j + 1) % 4], (0, 255, 0), 3)

                # Display confirmation message on the frame
                cv2.putText(frame, "SCANNED! ID: " + str(fragrance_id), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Hold the confirmation frame for a moment
                cv2.imshow(window_name, frame)
                cv2.waitKey(1500) 
                
                # Exit the loop upon successful scan
                break 

            except ValueError:
                # Handle non-integer data in QR code (i.e., not a valid ID)
                cv2.putText(frame, "INVALID ID FORMAT", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            except Exception:
                # Other decoding errors
                continue
                
        # If successfully scanned, break the main loop
        if fragrance_id is not None:
            break

        # Display the live feed
        cv2.imshow(window_name, frame)

        # Wait for key press (1ms), check for 'q' to quit manually
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Return the ID found (or None)
    return fragrance_id
