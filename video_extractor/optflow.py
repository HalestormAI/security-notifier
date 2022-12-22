import argparse
from pathlib import Path

import time
import cv2 as cv
import numpy as np

from  state import State
from camera_text import CAMERA_TEXT_POSITIONS, rescale_text_pos, generate_text_mask, extract_camera_text

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--max-corners", type=int, default=100)
    parser.add_argument("--max-frames-before-reinit", type=int, default=900)
    parser.add_argument("--rescale", type=float, default=0.5)
    parser.add_argument("--frame-skip", type=int, default=2)
    parser.add_argument("--min-line-length", type=int, default=100)
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--tesseract-opts", type=str,
                        default=r'--oem 3 --psm 7')
    parser.add_argument("--max-frames", type=int, default=None)
    return parser.parse_args()


def main(args: argparse.Namespace):
    if args.output_dir is not None:
        Path(args.output_dir).mkdir(exist_ok=True, parents=True)

    cap = cv.VideoCapture(args.input_file)

    feature_params = dict(maxCorners=args.max_corners,
                          qualityLevel=0.3,
                          minDistance=7,
                          blockSize=7)

    lk_params = dict(winSize=(15, 15),
                     maxLevel=2,
                     criteria=(cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03))

    color = np.random.randint(0, 255, (args.max_corners, 3))

    ret, orig_frame = cap.read()
    orig_grey = cv.cvtColor(orig_frame, cv.COLOR_BGR2GRAY)
    prev_grey = cv.resize(orig_grey, dsize=None,
                          fx=args.rescale, fy=args.rescale)

    feature_mask = generate_text_mask(prev_grey, args.rescale)

    no_motion = np.zeros(prev_grey.shape + (3, ), dtype=orig_frame.dtype)
    print(prev_grey.shape + (3, ))
    cv.putText(no_motion, "NO MOTION", (100, 100),
               cv.FONT_HERSHEY_DUPLEX, 3.0, (0, 255, 0), 3)

    for rect in CAMERA_TEXT_POSITIONS:
        (x1, y1), (x2, y2) = rect
        roi = orig_grey[y1:y2, x1:x2].copy()
        print(extract_camera_text(roi, args.tesseract_opts))

    p0 = cv.goodFeaturesToTrack(prev_grey, mask=feature_mask, **feature_params)

    mask = np.zeros(prev_grey.shape + (3, ), dtype=orig_frame.dtype)

    state = State()
    state.reset()
    while (1):
        write_frame = False
        ret, raw_frame = cap.read()
        
        raw_grey = cv.cvtColor(raw_frame, cv.COLOR_BGR2GRAY) 

        frame = cv.resize(raw_frame, dsize=None,
                          fx=args.rescale, fy=args.rescale)
        if not ret:
            print('No frames grabbed!')
            break

        grey = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        state.update_fps()

        if state.frame_counter > 0 and state.frame_counter % args.max_frames_before_reinit == 0:
            state.print()
            p0 = cv.goodFeaturesToTrack(
                grey, mask=feature_mask, **feature_params)
            mask = np.zeros_like(grey)
            state.reset()

            # This is expensive, we'll do it once per second max
        if state.frame_counter % cap.get(cv.CAP_PROP_FPS) == 0:
            t_st = time.time()
            state.update_frame_time(raw_grey, args.tesseract_opts, debug=args.display)
            print(f"Getting frame time took {time.time() - t_st:.2f}s")

        if state.frame_counter % args.frame_skip == 0:

            p1, st, err = cv.calcOpticalFlowPyrLK(
                prev_grey, grey, p0, None, **lk_params)

            if p1 is not None:
                good_new = p1[st == 1]
                good_old = p0[st == 1]

            for i, (new, old) in enumerate(zip(good_new, good_old)):
                a, b = new.ravel()
                c, d = old.ravel()
                mask = cv.line(mask, (int(a), int(b)),
                               (int(c), int(d)), color[i].tolist(), 2)
                frame = cv.circle(frame, (int(a), int(b)),
                                  5, color[i].tolist(), -1)

                state.line_lengths[i] += np.sqrt((c-a)**2 + (d-b)**2)
                if state.line_lengths[i] > args.min_line_length and state.flagged_detections[i][0] is None:
                    print(
                        f"Frame {state.frame_counter:05d} [{state.current_frame_time}] Object motion detected for feature {i}!!")
                    state.flagged_detections[i][0] = state.frame_counter
                    write_frame = True
                if i in state.flagged_detections:
                    state.flagged_detections[i][1] = state.frame_counter

            if write_frame and args.output_dir is not None:
                cv.imwrite(str(Path(args.output_dir) /
                           f'frame_{state.frame_counter:06d}.png'), raw_frame)
                write_frame = False

            if args.display:
                if len(state.flagged_detections) > 0:
                    img = cv.add(frame, mask)
                    output = img
                else:
                    output = no_motion.copy()

                fps_pos = rescale_text_pos(
                    CAMERA_TEXT_POSITIONS[0], args.rescale)
                output = cv.putText(output, f"FPS: {state.fps:.2f}", (
                    fps_pos[0][0], fps_pos[0][1]), cv.FONT_HERSHEY_DUPLEX, 0.4, (255, 0, 0), 1)

                cv.imshow('frame', output)
                k = cv.waitKey(1) & 0xff
                if k == 27:
                    break

            prev_grey = grey.copy()
            p0 = good_new.reshape(-1, 1, 2)

        state.increment()
        if args.max_frames and state.frame_counter > args.max_frames:
            break
    cv.destroyAllWindows()

if __name__ == "__main__":
    args = parse_args()
    main(args)