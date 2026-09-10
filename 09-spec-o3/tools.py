"""从原始光谱重绘局部波段，作为下一轮的图片观察。"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def spectral_visualization_tool(wavelength, flux, redshift, wavelength_range, label, output_path):
    wavelength = np.asarray(wavelength) / (1 + redshift)
    flux = np.asarray(flux)
    low, high = wavelength_range
    selected = (wavelength >= low) & (wavelength <= high)
    # 空窗口是工具动作的一种结果，返回文字让模型继续判断。
    if selected.sum() < 2:
        return {
            "content": [{"type": "text", "text": f"No spectrum data in wavelength range ({low:g}, {high:g}) Å."}],
            "images": [], "ok": False,
        }
    wave, values = wavelength[selected], flux[selected]
    width = high - low
    figsize = (6, 4) if width < 50 else (7, 4.5) if width < 200 else (8, 5) if width < 1000 else (9, 5.5)
    fig, ax = plt.subplots(figsize=figsize, dpi=80)
    ax.plot(wave, values, color="blue", linewidth=1, alpha=0.8)
    ax.set_xlabel("Wavelength (Å)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Flux", fontsize=12, fontweight="bold")
    ax.set_title("Spectrum", fontsize=14, fontweight="bold", pad=20)
    ax.grid(True, alpha=0.3)
    ax.minorticks_on()
    ax.text(
        0.98, 0.98,
        f"Points: {len(wave):,}\nλ: {wave.min():.1f}–{wave.max():.1f} Å\nFlux: {values.min():.2f}–{values.max():.2f}",
        transform=ax.transAxes, va="top", ha="right", fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
    )
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=80, bbox_inches="tight")
    plt.close(fig)
    text = f"Generated spectral visualization for wavelength range ({low:g}, {high:g}) Å"
    if label:
        text += f" ({label})"
    return {
        "content": [{"type": "image", "image": str(output_path)}, {"type": "text", "text": text}],
        "images": [str(output_path)], "ok": True,
    }
