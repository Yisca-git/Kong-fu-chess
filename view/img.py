from __future__ import annotations

import pathlib

import cv2
import numpy as np

class Img:
    def __init__(self):
        self.img = None

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Img":
        """
        Load `path` into self.img and **optionally resize**.

        Parameters
        ----------
        path : str | Path
            Image file to load.
        size : (width, height) | None
            Target size in pixels.  If None, keep original.
        keep_aspect : bool
            • False  → resize exactly to `size`
            • True   → shrink so the *longer* side fits `size` while
                       preserving aspect ratio (no cropping).
        interpolation : OpenCV flag
            E.g.  `cv2.INTER_AREA` for shrink, `cv2.INTER_LINEAR` for enlarge.

        Returns
        -------
        Img
            `self`, so you can chain:  `sprite = Img().read("foo.png", (64,64))`
        """
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]

            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h

            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        return self

    def draw_on(self, other_img, x, y):
        if self.img is None or other_img.img is None:
            raise ValueError("Both images must be loaded before drawing.")

        if self.img.shape[2] != other_img.img.shape[2]:
            if self.img.shape[2] == 3 and other_img.img.shape[2] == 4:
                self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
            elif self.img.shape[2] == 4 and other_img.img.shape[2] == 3:
                self.img = cv2.cvtColor(self.img, cv2.COLOR_BGRA2BGR)

        h, w = self.img.shape[:2]
        H, W = other_img.img.shape[:2]

        # clip to canvas bounds
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, W), min(y + h, H)
        if x2 <= x1 or y2 <= y1:
            return  # fully outside canvas

        sx, sy = x1 - x, y1 - y  # offset into self.img
        sprite_crop = self.img[sy:sy + (y2 - y1), sx:sx + (x2 - x1)]
        roi = other_img.img[y1:y2, x1:x2]

        if self.img.shape[2] == 4:
            b, g, r, a = cv2.split(sprite_crop)
            mask = a / 255.0
            for c in range(3):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * sprite_crop[..., c]
        else:
            other_img.img[y1:y2, x1:x2] = sprite_crop

    def copy(self) -> "Img":
        """Returns a new Img with an independent copy of the pixel buffer."""
        result = Img()
        result.img = self.img.copy()
        return result

    def width(self) -> int:
        return self.img.shape[1]

    def height(self) -> int:
        return self.img.shape[0]

    def channels(self) -> int:
        return self.img.shape[2]

    def paste(self, src: "Img", x: int, y: int, w: int) -> None:
        """Copies src pixels directly into self at (x, y) — no alpha blending."""
        self.img[y:y + src.height(), x:x + w] = src.img

    def raw(self):
        """Returns the raw numpy array — only for cv2.imshow plumbing in GameWindow."""
        return self.img

    def draw_rect(self, x: int, y: int, w: int, h: int, color=(0, 255, 255, 255), thickness: int = 3) -> None:
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.rectangle(self.img, (x, y), (x + w, y + h), color, thickness)

    def draw_rect_filled(self, x: int, y: int, w: int, h: int, color=(0, 255, 255), alpha: float = 0.4) -> None:
        """Draws a semi-transparent filled rectangle by blending with the existing pixels."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        x2, y2  = min(x + w, self.img.shape[1]), min(y + h, self.img.shape[0])
        if x2 <= x or y2 <= y:
            return
        roi     = self.img[y:y2, x:x2]
        overlay = roi.copy()
        channels = self.img.shape[2]
        fill = color[:3] + (255,) if channels == 4 else color[:3]
        overlay[:] = fill
        self.img[y:y2, x:x2] = cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0)

    def new(self, width: int, height: int, channels: int = 3) -> "Img":
        """Creates a blank black canvas of the given size."""
        self.img = np.zeros((height, width, channels), dtype=np.uint8)
        return self

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def draw_circle(self, cx: int, cy: int, radius: int,
                    color=(0, 255, 255, 255), thickness: int = 2) -> None:
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.circle(self.img, (cx, cy), radius, color, thickness)

    def save(self, path: str | pathlib.Path) -> None:
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imwrite(str(path), self.img)

    def show(self):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow("Image", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
