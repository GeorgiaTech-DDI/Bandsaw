#!/usr/bin/env python3
"""
Test Script for Angled Slit Detection (Updated)

This script focuses on testing the enhanced slit detection with properly angled
bounding boxes, including finalized detection with correct angle.

Usage:
    python test_angled_slit.py [--video SOURCE] [--stabilization TIME]
"""

import cv2
import time
import argparse
import sys
import math
import numpy as np
from enhanced_slit_detection import SlitDetector
from video_capture import open_video_source, get_frame, release_video

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Angled Slit Detection Test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--video', type=str, default='0',
                        help='Video source (0 for webcam, or path to video file)')
    parser.add_argument('--stabilization', type=float, default=5.0,
                        help='Stabilization time for slit detection (seconds)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with visualization')
    parser.add_argument('--width', type=int, default=30,
                        help='Width of the slit bounding box in pixels')
    
    return parser.parse_args()

def main():
    """Main function"""
    print("Angled Slit Detection Test (Updated)")
    print("===================================")
    
    # Parse arguments
    args = parse_arguments()
    debug_mode = args.debug
    
    # Initialize video capture
    print(f"Opening video source: {args.video}")
    cap = open_video_source(args.video)
    if cap is None:
        print("Error: Could not open video source.")
        return 1
    
    # Initialize slit detector
    slit_detector = SlitDetector(stabilization_time=args.stabilization, debug=debug_mode)
    
    # Always active mode for testing
    slit_detector.start_detection()
    
    print("\nSlit detection started")
    print(f"Stabilization time: {args.stabilization} seconds")
    print("Press 'q' to quit, 'r' to reset detection, 's' to save screenshot, 'f' to force finalization")
    
    # For FPS calculation
    frame_count = 0
    start_time = time.time()
    fps = 0
    
    # Count for screenshot filenames
    screenshot_count = 0
    
    # Timer display for stabilization countdown
    detection_start_time = time.time()
    
    try:
        while True:
            # Get a frame
            ret, frame = get_frame(cap)
            if not ret or frame is None:
                print("Error: Failed to get frame.")
                time.sleep(0.1)
                continue
            
            # Process frame to detect slit
            slit_data, processed_frame = slit_detector.detect_slit(frame)
            
            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
            
            # Create info panel
            info_panel = np.zeros((160, processed_frame.shape[1], 3), dtype=np.uint8)
            
            # Add FPS information
            cv2.putText(info_panel, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add detection state
            if slit_detector.is_finalized:
                state_color = (0, 255, 0)  # Green for finalized
                state_text = "FINALIZED"
            else:
                # Calculate remaining time
                elapsed = time.time() - detection_start_time
                remaining = max(0, slit_detector.stabilization_time - elapsed)
                state_color = (0, 165, 255)  # Orange for detecting
                state_text = f"DETECTING (Stabilizing: {remaining:.1f}s remaining)"
            
            cv2.putText(info_panel, f"State: {state_text}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
            
            # Add slit information if detected
            if slit_data:
                # Check if we have standard or rotated bbox
                if len(slit_data) == 5:  # Rotated bbox
                    center_x, center_y, width, height, angle = slit_data
                    cv2.putText(info_panel, f"Slit Center: ({center_x:.1f}, {center_y:.1f})", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(info_panel, f"Dimensions: {width:.1f} x {height:.1f} pixels", (10, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(info_panel, f"Angle: {angle:.1f}°", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                else:  # Standard bbox
                    x, y, w, h = slit_data
                    cv2.putText(info_panel, f"Slit Position: ({x}, {y})", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(info_panel, f"Dimensions: {w} x {h} pixels", (10, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                cv2.putText(info_panel, "No slit detected", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Add a key command reminder on the frame
            reminder_text = "Q: Quit | R: Reset | S: Screenshot | F: Force Finalize"
            text_size = cv2.getTextSize(reminder_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            reminder_x = processed_frame.shape[1] - text_size[0] - 10
            cv2.putText(processed_frame, reminder_text, (reminder_x, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Combine frame and info panel
            display = np.vstack([processed_frame, info_panel])
            
            # Display the combined frame
            cv2.imshow("Angled Slit Detection Test", display)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                print("Resetting slit detection...")
                slit_detector.stop_detection()
                slit_detector.start_detection()
                detection_start_time = time.time()
            elif key == ord('s'):
                # Save a screenshot
                filename = f"slit_detection_{screenshot_count}.png"
                cv2.imwrite(filename, display)
                print(f"Screenshot saved as {filename}")
                screenshot_count += 1
            elif key == ord('f'):
                # Force finalization immediately
                if not slit_detector.is_finalized and slit_detector.is_active:
                    print("Forcing finalization of slit detection...")
                    slit_detector._finalize_detection()
            
            # Reduce CPU usage
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        slit_detector.stop_detection()
        release_video(cap)
        cv2.destroyAllWindows()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())