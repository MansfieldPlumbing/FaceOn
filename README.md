
---

# FaceOn Studio

![Windows 10](https://img.shields.io/badge/Windows-10-0078D6?style=for-the-badge&logo=windows)![Windows 11](https://img.shields.io/badge/Windows-11-0078D6?style=for-the-badge&logo=windows)![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python)![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus)![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

FaceOn Studio is not just another face-swapping app; it's a real-time virtual camera suite that lets you become anyone or anything you can imagine. Paint directly onto a source face to create a unique digital avatar, and broadcast the result live into any application that uses a webcam—from OBS and Zoom to Discord and Google Meet.

Welcome to the cutting edge of real-time avatar creation! FaceOn Studio is an **experimental and creative tool.** Think of it less as a simple filter and more as a **collaboration with an AI artist.** Your mileage may vary, but the creative possibilities that arise from guiding a powerful neural network are endless.

Powered by a high-performance deep learning core and the custom **[VirtuaCam](https://github.com/MansfieldPlumbing/VirtuaCam)** driver, FaceOn Studio offers a seamless and powerful way to transform your digital presence.

## A Creative Collaboration (Not a Perfect Filter)

The magic of FaceOn Studio comes from the `inswapper` deep learning model, which is trained on millions of real faces. It doesn't just paste your drawings on top of your face; it tries to make them look *photorealistic*. This creates a fascinating and creative push-and-pull between you and the AI:

*   You might draw a pair of cartoony, orange-rimmed glasses on Abraham Lincoln, and the AI will render them as realistic-looking glasses on your face in real-time.
*   You can subtly paint a new hairline, apply digital makeup, or add a scar, and the model will intelligently blend it into your features.

This makes the tool incredibly powerful for tweaking and perfecting avatars, but be prepared for a creative partnership. The AI will interpret your work, and sometimes the most interesting results come from these "happy accidents."

<p align="center">
  <img src="https://github.com/user-attachments/assets/bcfbad9b-c0b3-47a5-9964-82fa112efd8d" alt="FaceOn Studio Demo" width="800"/>
</p>

## Core Features

*   **Real-Time, GPU-Accelerated Swapping:** Leverages ONNX Runtime with a DirectML backend for high-performance, vendor-agnostic face swapping that runs smoothly on any modern GPU (NVIDIA, AMD, Intel).
*   **AI-Interpreted Painting:** Experience a unique creative process where you don't just overlay an image, you guide an AI. The model intelligently interprets your paintings to create a cohesive, blended result.
*   **Powerful Paint Tools:** Use an intuitive painting interface to modify your source face. Features include:
    *   Adjustable brush size, opacity, hardness, and step.
    *   A full-featured color picker and eyedropper tool.
    *   Symbol stamping for adding creative effects.
    *   Full undo/redo history for non-destructive editing.
*   **Virtual Camera Broadcasting:** Integration with the **[VirtuaCam](https://github.com/MansfieldPlumbing/VirtuaCam)** driver creates a new webcam on your system, allowing you to pipe your modified video feed directly into other applications.
*   **Create & Save Permanent Avatars:** When you've perfected a look, you can save the resulting face embedding as a `.safetensors` file. This creates a permanent, high-fidelity avatar that you can load instantly in the future.
*   **Fine-Grained Controls:** Pop out the External Preview window to access advanced sliders for perfecting the blend. Adjust the ROI, feathering, mask expansion, and even nudge the affine transform (position/scale) for a flawless result.

## How It Works

FaceOn Studio uses a sophisticated hybrid architecture to achieve its real-time performance and system-level integration:

1.  **The Python Core:** The main application is built in Python using **Tkinter** for the UI. It uses **OpenCV** to manage the webcam feed and **ONNX Runtime** to execute the deep learning models for face detection (`det_10g`), recognition (`w600k_r50`), and swapping (`inswapper_128`).
2.  **The C++ Virtual Camera:** The low-level **[VirtuaCam](https://github.com/MansfieldPlumbing/VirtuaCam)** driver is written in C++. It registers a new software-based camera source with Windows, making it available to all other applications.
3.  **The `directport` Bridge:** A high-speed communication bridge allows the Python application (the "producer") to send the processed video frames to a shared memory texture, which the C++ driver (the "consumer") reads from. This ensures minimal latency and high throughput.

## Getting Started on Windows

You have two simple options for getting started. Both include all necessary models and libraries.

**Prerequisites:**
*   Windows 10 or Windows 11
*   A modern GPU (NVIDIA, AMD, or Intel) with DirectX 12 support
*   A webcam

---

### Option 1: Easy Installation (Recommended)

This method uses a standard installer and creates shortcuts for you. It installs locally to your user account and does **not** require administrator privileges.

1.  Go to the [**Latest Release**](https://github.com/MansfieldPlumbing/FaceOn/releases/latest) page.
2.  Download the `FaceOn-Studio-Setup.exe` file.
3.  Run the installer and follow the on-screen instructions.
4.  Launch **FaceOn Studio** from the desktop or Start Menu shortcut.

---

### Option 2: Portable (ZIP)

This method is for users who prefer not to install software.

1.  Go to the [**Latest Release**](https://github.com/MansfieldPlumbing/FaceOn/releases/latest) page.
2.  Download the `FaceOn-Studio.zip` file.
3.  Extract the contents of the ZIP file to a folder on your computer.
4.  Run `FaceOn Studio.exe` from the extracted folder.

## Basic Usage

1.  Launch **FaceOn Studio**.
2.  Click the **📂 (Folder)** icon to load a source image containing a face. This will be the face you swap onto your webcam feed.
3.  Use the paint tools and color picker to customize the source image on the canvas.
4.  (Optional) Click the **💾 (Save)** icon to save your creation as a permanent `.safetensors` avatar in the `embeddings` folder.
5.  Launch your streaming or video-conferencing app (OBS, Zoom, Discord, etc.).
6.  In your other application's settings, change the selected camera to **"VirtuaCam"**.
7.  Your real-time, face-swapped video will now be broadcasting!

## For Developers (Linux & macOS)

While the pre-built executables are Windows-only due to the custom virtual camera driver, users on other platforms can build and run the core Python application from the source code. The virtual camera functionality will not be available.

You will need:
*   A C++ compiler and CMake to build the `directport` library.
*   Python 3.10+
*   The necessary Python packages (see `requirements.txt`).
*   A suitable virtual camera solution for your OS (e.g., v4l2loopback on Linux).

## Technology Stack

*   **Core Logic:** Python
*   **GUI:** Tkinter
*   **AI/ML:** ONNX Runtime with DirectML
*   **Virtual Camera:** C++, Windows Media Foundation, COM
*   **Image Processing:** OpenCV, Pillow
*   **Packaging:** PyInstaller, Inno Setup
