import argparse
import os
import os.path as osp
import numpy as np
import cv2
import torch
import gc
import sys
import json
import time
import logging
from typing import Tuple, List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append("./sam2")

try:
    from sam2.build_sam import build_sam2_video_predictor
    SAM2_AVAILABLE = True
except ImportError:
    logger.warning("SAM2 not available. Running in simulation mode.")
    SAM2_AVAILABLE = False

color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

def load_txt(gt_path: str) -> Dict[int, Tuple[Tuple[int, int, int, int], int]]:
    """Load ground truth bounding boxes from text file with improved error handling."""
    try:
        with open(gt_path, 'r') as f:
            gt = f.readlines()
        
        prompts = {}
        for fid, line in enumerate(gt):
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue
                
            try:
                parts = line.split(',')
                if len(parts) >= 4:
                    x, y, w, h = map(float, parts[:4])
                    x, y, w, h = int(x), int(y), int(w), int(h)
                    # Validate bounding box
                    if w > 0 and h > 0:
                        prompts[fid] = ((x, y, x + w, y + h), 0)
                    else:
                        logger.warning(f"Invalid bounding box at line {fid}: w={w}, h={h}")
                else:
                    logger.warning(f"Invalid format at line {fid}: {line}")
            except ValueError as e:
                logger.warning(f"Error parsing line {fid}: {line} - {e}")
                continue
                
        logger.info(f"Loaded {len(prompts)} valid bounding boxes from {gt_path}")
        return prompts
        
    except FileNotFoundError:
        logger.error(f"Ground truth file not found: {gt_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading ground truth file: {e}")
        raise

def determine_model_cfg(model_path: str) -> str:
    """Determine model configuration based on checkpoint path."""
    config_map = {
        "large": "configs/samurai/sam2.1_hiera_l.yaml",
        "base_plus": "configs/samurai/sam2.1_hiera_b+.yaml", 
        "small": "configs/samurai/sam2.1_hiera_s.yaml",
        "tiny": "configs/samurai/sam2.1_hiera_t.yaml"
    }
    
    for key, config in config_map.items():
        if key in model_path:
            return config
    
    # Default to base_plus if no match found
    logger.warning(f"Could not determine model size from path {model_path}, using base_plus config")
    return config_map["base_plus"]

def prepare_frames_or_path(video_path: str) -> str:
    """Validate and prepare video input path."""
    if not osp.exists(video_path):
        raise FileNotFoundError(f"Video path does not exist: {video_path}")
    
    if video_path.endswith((".mp4", ".avi", ".mov", ".mkv")):
        return video_path
    elif osp.isdir(video_path):
        # Check if directory contains image files
        image_files = [f for f in os.listdir(video_path) 
                      if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]
        if not image_files:
            raise ValueError(f"No image files found in directory: {video_path}")
        logger.info(f"Found {len(image_files)} image files in directory")
        return video_path
    else:
        raise ValueError("Invalid video_path format. Should be video file or directory of images.")

def validate_inputs(args) -> bool:
    """Validate all input arguments."""
    try:
        # Check video path
        prepare_frames_or_path(args.video_path)
        
        # Check ground truth file
        if not osp.exists(args.txt_path):
            raise FileNotFoundError(f"Ground truth file not found: {args.txt_path}")
        
        # Check model checkpoint (if SAM2 is available)
        if SAM2_AVAILABLE and not osp.exists(args.model_path):
            logger.warning(f"Model checkpoint not found: {args.model_path}")
            return False
            
        # Validate output directory
        output_dir = osp.dirname(args.video_output_path)
        if output_dir and not osp.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        return False

def simulate_tracking(args) -> bool:
    """Simulate SAMURAI tracking when SAM2 is not available."""
    logger.info("Running in simulation mode (SAM2 not available)")
    
    # Load inputs
    prompts = load_txt(args.txt_path)
    if not prompts:
        logger.error("No valid prompts found in ground truth file")
        return False
    
    # Get video information
    if osp.isdir(args.video_path):
        image_files = sorted([f for f in os.listdir(args.video_path) 
                            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))])
        num_frames = len(image_files)
        
        # Read first frame to get dimensions
        first_frame_path = osp.join(args.video_path, image_files[0])
        first_frame = cv2.imread(first_frame_path)
        if first_frame is None:
            logger.error(f"Could not read first frame: {first_frame_path}")
            return False
        height, width = first_frame.shape[:2]
        
    else:
        cap = cv2.VideoCapture(args.video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {args.video_path}")
            return False
        
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
    
    logger.info(f"Video info: {width}x{height}, {num_frames} frames")
    
    # Simulate tracking results
    tracking_results = simulate_tracking_results(prompts, num_frames, width, height)
    
    # Save simulation results
    results_file = args.video_output_path.replace('.mp4', '_simulation_results.json')
    with open(results_file, 'w') as f:
        json.dump(tracking_results, f, indent=2)
    
    logger.info(f"Simulation results saved to: {results_file}")
    return True

def simulate_tracking_results(prompts: Dict, num_frames: int, width: int, height: int) -> Dict:
    """Generate simulated tracking results."""
    results = {
        "metadata": {
            "num_frames": num_frames,
            "video_dimensions": [width, height],
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "simulation": True
        },
        "frames": []
    }
    
    # Initialize object position from first prompt
    if 0 in prompts:
        bbox, _ = prompts[0]
        x1, y1, x2, y2 = bbox
        obj_x, obj_y = (x1 + x2) // 2, (y1 + y2) // 2
        obj_w, obj_h = x2 - x1, y2 - y1
    else:
        obj_x, obj_y, obj_w, obj_h = width // 2, height // 2, 50, 50
    
    # Simulate motion
    velocity_x, velocity_y = 2, 1
    
    for frame_idx in range(num_frames):
        # Update position with simple motion model
        obj_x += velocity_x + np.random.normal(MOTION_NOISE_MEAN, MOTION_NOISE_STD)
        obj_y += velocity_y + np.random.normal(MOTION_NOISE_MEAN, MOTION_NOISE_STD)
        
        # Bounce off walls
        if obj_x <= 0 or obj_x >= width - obj_w:
            velocity_x *= -1
        if obj_y <= 0 or obj_y >= height - obj_h:
            velocity_y *= -1
        
        # Keep within bounds
        obj_x = max(0, min(width - obj_w, obj_x))
        obj_y = max(0, min(height - obj_h, obj_y))
        
        # Calculate confidence (simulated)
        confidence = 0.9 + 0.1 * np.sin(frame_idx * 0.1)
        
        frame_result = {
            "frame_id": frame_idx,
            "objects": [{
                "id": 0,
                "bbox": [int(obj_x), int(obj_y), int(obj_w), int(obj_h)],
                "confidence": float(confidence),
                "tracking_quality": float(0.8 + 0.2 * np.cos(frame_idx * 0.05))
            }]
        }
        results["frames"].append(frame_result)
    
    return results

def main(args):
    """Main function with improved error handling and fallback options."""
    logger.info("Starting SAMURAI demo...")
    
    # Validate inputs
    if not validate_inputs(args):
        logger.error("Input validation failed. Exiting.")
        return 1
    
    # Try to run actual SAMURAI tracking if available
    if SAM2_AVAILABLE:
        try:
            return run_actual_tracking(args)
        except Exception as e:
            logger.error(f"SAMURAI tracking failed: {e}")
            logger.info("Falling back to simulation mode...")
            
    # Run simulation if SAM2 not available or actual tracking failed
    try:
        success = simulate_tracking(args)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return 1

def run_actual_tracking(args):
    """Run actual SAMURAI tracking (when SAM2 is available)."""
    logger.info("Running actual SAMURAI tracking...")
    
    model_cfg = determine_model_cfg(args.model_path)
    logger.info(f"Using model config: {model_cfg}")
    
    try:
        predictor = build_sam2_video_predictor(model_cfg, args.model_path, device="cuda:0")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    frames_or_path = prepare_frames_or_path(args.video_path)
    prompts = load_txt(args.txt_path)
    
    if not prompts:
        raise ValueError("No valid prompts found")
    
    frame_rate = 30
    tracking_results = {
        "metadata": {
            "model_config": model_cfg,
            "model_path": args.model_path,
            "video_path": args.video_path,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "simulation": False
        },
        "frames": []
    }
    
    if args.save_to_video:
        if osp.isdir(args.video_path):
            frames = sorted([osp.join(args.video_path, f) for f in os.listdir(args.video_path) 
                           if f.endswith((".jpg", ".jpeg", ".JPG", ".JPEG"))])
            loaded_frames = [cv2.imread(frame_path) for frame_path in frames]
            if not loaded_frames or loaded_frames[0] is None:
                raise ValueError("Could not load frames from directory")
            height, width = loaded_frames[0].shape[:2]
        else:
            cap = cv2.VideoCapture(args.video_path)
            frame_rate = cap.get(cv2.CAP_PROP_FPS)
            loaded_frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                loaded_frames.append(frame)
            cap.release()
            
            if not loaded_frames:
                raise ValueError("No frames were loaded from the video.")
            height, width = loaded_frames[0].shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(args.video_output_path, fourcc, frame_rate, (width, height))

    start_time = time.time()
    
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        state = predictor.init_state(frames_or_path, offload_video_to_cpu=True)
        bbox, track_label = prompts[0]
        _, _, masks = predictor.add_new_points_or_box(state, box=bbox, frame_idx=0, obj_id=0)

        for frame_idx, object_ids, masks in predictor.propagate_in_video(state):
            mask_to_vis = {}
            bbox_to_vis = {}

            for obj_id, mask in zip(object_ids, masks):
                mask = mask[0].cpu().numpy()
                mask = mask > 0.0
                non_zero_indices = np.argwhere(mask)
                if len(non_zero_indices) == 0:
                    bbox = [0, 0, 0, 0]
                else:
                    y_min, x_min = non_zero_indices.min(axis=0).tolist()
                    y_max, x_max = non_zero_indices.max(axis=0).tolist()
                    bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
                bbox_to_vis[obj_id] = bbox
                mask_to_vis[obj_id] = mask

            # Store tracking results
            frame_result = {
                "frame_id": frame_idx,
                "objects": []
            }
            
            for obj_id in bbox_to_vis:
                bbox = bbox_to_vis[obj_id]
                frame_result["objects"].append({
                    "id": obj_id,
                    "bbox": bbox,
                    "confidence": 1.0,  # SAM2 doesn't provide confidence scores
                    "mask_area": int(np.sum(mask_to_vis[obj_id]))
                })
            
            tracking_results["frames"].append(frame_result)

            if args.save_to_video:
                img = loaded_frames[frame_idx]
                for obj_id, mask in mask_to_vis.items():
                    mask_img = np.zeros((height, width, 3), np.uint8)
                    mask_img[mask] = color[(obj_id + 1) % len(color)]
                    img = cv2.addWeighted(img, 1, mask_img, 0.2, 0)

                for obj_id, bbox in bbox_to_vis.items():
                    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), 
                                color[obj_id % len(color)], 2)

                out.write(img)

        if args.save_to_video:
            out.release()

    processing_time = time.time() - start_time
    tracking_results["metadata"]["processing_time"] = processing_time
    tracking_results["metadata"]["fps"] = len(tracking_results["frames"]) / processing_time
    
    # Save tracking results
    results_file = args.video_output_path.replace('.mp4', '_tracking_results.json')
    with open(results_file, 'w') as f:
        json.dump(tracking_results, f, indent=2)
    
    logger.info(f"Processing completed in {processing_time:.2f}s")
    logger.info(f"Average FPS: {len(tracking_results['frames']) / processing_time:.1f}")
    logger.info(f"Results saved to: {results_file}")

    # Cleanup
    del predictor, state
    gc.collect()
    torch.clear_autocast_cache()
    torch.cuda.empty_cache()
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Improved SAMURAI Demo with fallback simulation")
    parser.add_argument("--video_path", required=True, help="Input video path or directory of frames.")
    parser.add_argument("--txt_path", required=True, help="Path to ground truth text file.")
    parser.add_argument("--model_path", default="sam2/checkpoints/sam2.1_hiera_base_plus.pt", 
                       help="Path to the model checkpoint.")
    parser.add_argument("--video_output_path", default="demo.mp4", help="Path to save the output video.")
    parser.add_argument("--save_to_video", default=True, type=bool, help="Save results to a video.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        exit_code = main(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)