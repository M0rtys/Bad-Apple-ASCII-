#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全屏 Bad Apple ASCII 字符画播放器。

支持 MP4 等 OpenCV 可读取的视频。音频通过 FFmpeg 提取为临时 WAV，
再由 pygame 播放。视频帧以音频时钟为基准同步。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

try:
    import pygame
except ImportError:
    raise SystemExit(
        "缺少 pygame 模块。请运行：python -m pip install -r requirements.txt"
    )

ASCII_CHARS = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def extract_audio(video_path: Path, wav_path: Path) -> bool:
    """用 imageio-ffmpeg 自带的 FFmpeg 提取音轨；无音轨时返回 False。"""
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg, "-y", "-i", str(video_path),
            "-vn", "-ac", "2", "-ar", "44100",
            "-c:a", "pcm_s16le", str(wav_path),
        ]
        result = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 44
    except Exception:
        return False


def frame_to_ascii(frame: np.ndarray, cols: int, rows: int,
                   contrast: float, brightness: int, invert: bool) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (cols, rows), interpolation=cv2.INTER_AREA)
    adjusted = np.clip(
        (gray.astype(np.float32) - 128.0) * contrast + 128.0 + brightness,
        0, 255
    ).astype(np.uint8)
    if invert:
        adjusted = 255 - adjusted
    indices = adjusted.astype(np.int32) * (len(ASCII_CHARS) - 1) // 255
    return np.asarray(list(ASCII_CHARS), dtype="<U1")[indices]


def parse_args():
    parser = argparse.ArgumentParser(
        description="在全屏窗口中实时播放 ASCII 字符画视频。"
    )
    parser.add_argument("video", type=Path, help="视频文件路径，例如 bad_apple.mp4")
    parser.add_argument("--font-size", type=int, default=12, help="字符字号，默认 12")
    parser.add_argument("--contrast", type=float, default=1.25, help="对比度，默认 1.25")
    parser.add_argument("--brightness", type=int, default=0, help="亮度偏移，建议 -80 到 80")
    parser.add_argument("--fps", type=float, default=0, help="目标帧率；0 表示使用源视频帧率")
    parser.add_argument("--invert", action="store_true", help="反转黑白")
    parser.add_argument("--no-loop", action="store_true", help="播放结束后退出，不循环")
    parser.add_argument("--mute", action="store_true", help="不播放音频")
    parser.add_argument("--windowed", action="store_true", help="窗口模式，便于调试")
    return parser.parse_args()


def main():
    args = parse_args()
    video_path = args.video.expanduser().resolve()

    if not video_path.is_file():
        raise SystemExit(f"找不到视频文件：{video_path}")
    if not 6 <= args.font_size <= 40:
        raise SystemExit("--font-size 必须在 6 到 40 之间")
    if args.contrast < 0 or args.fps < 0:
        raise SystemExit("--contrast 和 --fps 不能为负数")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit("无法打开视频。请确认文件格式及视频文件是否损坏。")

    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if src_fps <= 0 or src_fps > 240:
        src_fps = 30.0
    target_fps = args.fps or src_fps
    duration = total_frames / src_fps if total_frames > 0 else 0

    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.init()

    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

    info = pygame.display.Info()
    screen_size = (info.current_w, info.current_h)
    flags = 0 if args.windowed else pygame.FULLSCREEN
    if args.windowed:
        screen_size = (min(1280, info.current_w), min(720, info.current_h))
    screen = pygame.display.set_mode(screen_size, flags)
    pygame.display.set_caption("Bad Apple ASCII Player")

    font = pygame.font.SysFont("consolas", args.font_size, bold=True)
    cell_w = max(1, font.size("M")[0])
    cell_h = max(1, font.get_linesize())
    cols = max(1, screen_size[0] // cell_w)
    rows = max(1, screen_size[1] // cell_h)

    # ASCII 字符的单元格比例与原始视频比例不同；按屏幕网格填充。
    # 这是字符画显示，不是原始视频像素级画质。
    print(f"视频：{src_w}x{src_h} @ {src_fps:.3f} FPS")
    print(f"屏幕：{screen_size[0]}x{screen_size[1]}；字符网格：{cols}x{rows}")
    print("ESC/Q 退出 | 空格暂停/继续 | R 从头播放")

    temp_dir = tempfile.TemporaryDirectory(prefix="badapple_ascii_")
    wav_path = Path(temp_dir.name) / "audio.wav"
    audio_loaded = False

    if not args.mute and pygame.mixer.get_init():
        if extract_audio(video_path, wav_path):
            try:
                pygame.mixer.music.load(str(wav_path))
                audio_loaded = True
            except pygame.error as exc:
                print(f"音频加载失败，将静音播放：{exc}")
        else:
            print("未能提取音轨或视频没有音轨，将静音播放。")

    looping = not args.no_loop
    if audio_loaded:
        pygame.mixer.music.play(loops=-1 if looping else 0)

    clock = pygame.time.Clock()
    frame_period = 1.0 / target_fps
    frame_index = 0
    loop_offset = 0.0
    paused = False
    running = True
    start_clock = time.perf_counter()
    last_frame = None
    render_color = (235, 235, 235)

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                        if audio_loaded:
                            if paused:
                                pygame.mixer.music.pause()
                            else:
                                pygame.mixer.music.unpause()
                    elif event.key == pygame.K_r:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        frame_index = 0
                        loop_offset = 0.0
                        start_clock = time.perf_counter()
                        if audio_loaded:
                            pygame.mixer.music.play(loops=-1 if looping else 0)

            if not running:
                break
            if paused:
                clock.tick(30)
                continue

            # 以音频播放位置作为主时钟；无音频时用单调时钟。
            if audio_loaded:
                audio_ms = pygame.mixer.music.get_pos()
                elapsed = max(0.0, audio_ms / 1000.0)
                if audio_ms < 0:
                    elapsed = time.perf_counter() - start_clock
            else:
                elapsed = time.perf_counter() - start_clock

            if duration > 0 and elapsed >= duration:
                if looping:
                    loop_offset += duration
                    # pygame music 循环播放时 get_pos 通常会重新计时。
                    if audio_loaded:
                        elapsed = pygame.mixer.music.get_pos() / 1000.0
                    else:
                        start_clock = time.perf_counter()
                        elapsed = 0.0
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_index = 0
                else:
                    break

            desired_frame = int(elapsed * src_fps)
            if total_frames > 0:
                desired_frame = min(desired_frame, total_frames - 1)

            # 若渲染落后，直接定位到应显示帧，避免延迟不断累积。
            if desired_frame > frame_index + 1:
                cap.set(cv2.CAP_PROP_POS_FRAMES, desired_frame)
                frame_index = desired_frame

            ret, frame = cap.read()
            if not ret:
                if looping:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_index = 0
                    continue
                break
            frame_index += 1

            ascii_grid = frame_to_ascii(
                frame, cols, rows, args.contrast, args.brightness, args.invert
            )

            screen.fill((0, 0, 0))
            # 逐行渲染；较小字号/较低字符网格通常更流畅。
            for y, row in enumerate(ascii_grid):
                line = "".join(row.tolist())
                surface = font.render(line, False, render_color)
                screen.blit(surface, (0, y * cell_h))
            pygame.display.flip()

            # 限制空转，不用它替代音频时钟。
            clock.tick(min(max(target_fps, 1), 120))

    except KeyboardInterrupt:
        pass
    finally:
        if audio_loaded:
            pygame.mixer.music.stop()
        cap.release()
        pygame.quit()
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
