"""
ECG Noise Removal using Butterworth Filters
============================================
Signals & Systems - Innovative Assessment

This script simulates a synthetic ECG signal corrupted by three common
noise sources and removes them with a cascade of LTI filters:

    1. Baseline wander      (~0.3 Hz, from breathing / movement)
    2. Power-line hum       (50 Hz mains interference)
    3. Broadband noise      (white Gaussian, electrode / muscle noise)

Filters used
    - Butterworth band-pass (0.5 - 40 Hz)
    - IIR notch at 50 Hz
    - Cascade of both (the final design)

Syllabus topics demonstrated
    - Continuous / discrete-time signals and sampling
    - LTI systems, impulse response, convolution
    - Fourier transform (FFT) and spectrum analysis
    - Frequency response (magnitude and phase), Bode plot
    - Poles and zeros, stability (z-plane)
    - Group delay, causal vs zero-phase filtering

Run:
    python src/ecg_filter_simulation.py
Outputs (figures + metrics.json) are written to the ../results folder.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# --------------------------------------------------------------------------
# 1. Parameters
# --------------------------------------------------------------------------
FS = 500.0            # sampling frequency (Hz)
DURATION = 10.0       # signal length (s)
HEART_RATE = 72       # beats per minute
SEED = 42             # reproducible noise

F_LOW, F_HIGH = 0.5, 40.0   # band-pass edges (Hz)
F_NOTCH, Q_NOTCH = 50.0, 30.0
ORDER = 4                   # Butterworth order (per band edge)

TRIM = int(1.0 * FS)        # ignore 1 s at each end (filter transients)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
C_CLEAN, C_NOISY, C_FILT, C_ALT = "#1b7f3b", "#b0b0b0", "#c0392b", "#1f5fa8"


# --------------------------------------------------------------------------
# 2. Signal generation
# --------------------------------------------------------------------------
def synthetic_ecg(fs, duration, heart_rate, rng):
    """Sum-of-Gaussians ECG model (P, Q, R, S, T waves per beat)."""
    t = np.arange(0, duration, 1 / fs)
    ecg = np.zeros_like(t)
    # (amplitude mV, centre offset from R peak s, width s)
    waves = [(0.12, -0.20, 0.025),   # P
             (-0.15, -0.04, 0.010),  # Q
             (1.00, 0.00, 0.012),    # R
             (-0.25, 0.04, 0.010),   # S
             (0.30, 0.25, 0.045)]    # T
    period = 60.0 / heart_rate
    r_peaks = np.arange(0.5, duration, period)
    r_peaks = r_peaks + rng.normal(0, 0.01, r_peaks.size)  # slight variability
    for rp in r_peaks:
        for amp, off, width in waves:
            ecg += amp * np.exp(-0.5 * ((t - rp - off) / width) ** 2)
    return t, ecg


def add_noise(t, clean, rng):
    baseline = 0.50 * np.sin(2 * np.pi * 0.30 * t) + 0.15 * np.sin(2 * np.pi * 0.15 * t + 1)
    mains = 0.25 * np.sin(2 * np.pi * 50.0 * t)
    white = rng.normal(0, 0.05, t.size)
    return clean + baseline + mains + white, baseline, mains, white


# --------------------------------------------------------------------------
# 3. Filter design and helpers
# --------------------------------------------------------------------------
def design_bandpass(order=ORDER, low=F_LOW, high=F_HIGH, fs=FS):
    return signal.butter(order, [low, high], btype="bandpass", fs=fs, output="sos")


def design_notch(f0=F_NOTCH, q=Q_NOTCH, fs=FS):
    b, a = signal.iirnotch(f0, q, fs=fs)
    return signal.tf2sos(b, a)


def cascade(*sos_list):
    return np.vstack(sos_list)


def snr_db(clean, test):
    """SNR of 'test' relative to 'clean' reference, edges trimmed."""
    c, x = clean[TRIM:-TRIM], test[TRIM:-TRIM]
    return 10 * np.log10(np.sum(c ** 2) / np.sum((x - c) ** 2))


def rmse(clean, test):
    c, x = clean[TRIM:-TRIM], test[TRIM:-TRIM]
    return float(np.sqrt(np.mean((x - c) ** 2)))


def spectrum(x, fs):
    """One-sided amplitude spectrum using a Hann window."""
    n = x.size
    w = np.hanning(n)
    X = np.fft.rfft(x * w)
    f = np.fft.rfftfreq(n, 1 / fs)
    return f, 2 * np.abs(X) / np.sum(w)


def savefig(name):
    path = os.path.join(RESULTS_DIR, name)
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print("saved", name)


# --------------------------------------------------------------------------
# 4. Figures
# --------------------------------------------------------------------------
def fig_noisy_vs_clean(t, clean, noisy, baseline, mains, white):
    fig, ax = plt.subplots(4, 1, figsize=(9, 8), sharex=True)
    ax[0].plot(t, clean, color=C_CLEAN); ax[0].set_title("Clean synthetic ECG")
    ax[1].plot(t, baseline, color=C_ALT); ax[1].set_title("Baseline wander (0.3 Hz + 0.15 Hz)")
    ax[2].plot(t, mains + white, color=C_ALT, lw=0.6); ax[2].set_title("50 Hz mains hum + white noise")
    ax[3].plot(t, noisy, color="#555"); ax[3].set_title("Noisy ECG (clean + all noise sources)")
    for a in ax: a.set_ylabel("mV")
    ax[3].set_xlabel("Time (s)")
    plt.tight_layout(); savefig("fig1_signal_and_noise.png")


def fig_spectrum_noisy(noisy, clean):
    f, Xn = spectrum(noisy, FS)
    _, Xc = spectrum(clean, FS)
    plt.figure(figsize=(9, 4))
    plt.semilogy(f, Xn, color=C_NOISY, label="Noisy ECG")
    plt.semilogy(f, Xc, color=C_CLEAN, lw=1.2, label="Clean ECG")
    plt.axvline(50, color=C_FILT, ls="--", lw=0.8); plt.text(51, 1.5, "50 Hz hum", color=C_FILT)
    plt.annotate("baseline wander", xy=(0.3, 0.1), xytext=(3, 0.6), color=C_ALT,
                 arrowprops=dict(arrowstyle="->", color=C_ALT))
    plt.xlim(0, 100); plt.ylim(1e-5, 3)
    plt.xlabel("Frequency (Hz)"); plt.ylabel("Amplitude (mV)")
    plt.title("Spectrum of the noisy ECG (FFT, Hann window)")
    plt.legend(); plt.tight_layout(); savefig("fig2_spectrum_noisy.png")


def fig_frequency_response(sos_final):
    w = np.logspace(-2, np.log10(FS / 2 - 1), 4000)
    fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for n, col in zip([2, 4, 6, 8], ["#8e44ad", C_FILT, C_ALT, "#e67e22"]):
        _, h = signal.sosfreqz(design_bandpass(order=n), worN=w, fs=FS)
        ax[0].semilogx(w, 20 * np.log10(np.abs(h) + 1e-12), color=col, label=f"order {n}")
    _, hf = signal.sosfreqz(sos_final, worN=w, fs=FS)
    ax[0].semilogx(w, 20 * np.log10(np.abs(hf) + 1e-12), color="k", ls="--", lw=1.2,
                   label="order 4 + 50 Hz notch (final)")
    ax[0].axhline(-3, color="gray", lw=0.7, ls=":")
    ax[0].set_ylim(-80, 5); ax[0].set_ylabel("Magnitude (dB)")
    ax[0].set_title("Frequency response of Butterworth band-pass 0.5-40 Hz (Bode plot)")
    ax[0].legend(loc="lower center", fontsize=8)
    ax[1].semilogx(w, np.unwrap(np.angle(hf)) * 180 / np.pi, color="k")
    ax[1].set_ylabel("Phase (deg) - final filter"); ax[1].set_xlabel("Frequency (Hz)")
    plt.tight_layout(); savefig("fig3_frequency_response.png")


def fig_pole_zero(sos_bp, sos_notch):
    z1, p1, _ = signal.sos2zpk(sos_bp)
    z2, p2, _ = signal.sos2zpk(sos_notch)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.8))
    th = np.linspace(0, 2 * np.pi, 400)
    for a, (z, p, ttl) in zip(ax, [(z1, p1, "Band-pass 0.5-40 Hz (order 4 per edge)"),
                                    (z2, p2, "50 Hz notch")]):
        a.plot(np.cos(th), np.sin(th), "k", lw=0.8)
        a.plot(z.real, z.imag, "o", mfc="none", color=C_ALT, ms=9, label="zeros")
        a.plot(p.real, p.imag, "x", color=C_FILT, ms=9, mew=2, label="poles")
        a.axhline(0, color="gray", lw=0.5); a.axvline(0, color="gray", lw=0.5)
        a.set_aspect("equal"); a.set_title(ttl); a.set_xlabel("Real"); a.set_ylabel("Imag")
        a.legend(loc="upper left", fontsize=8)
    plt.tight_layout(); savefig("fig4_pole_zero.png")
    return float(np.max(np.abs(np.concatenate([p1, p2]))))


def fig_convolution(sos_final, noisy):
    n = noisy.size
    impulse = np.zeros(n); impulse[0] = 1
    h = signal.sosfilt(sos_final, impulse)                 # impulse response h[n]
    y_conv = np.convolve(noisy, h)[:n]                     # y = x * h
    y_sos = signal.sosfilt(sos_final, noisy)               # direct IIR recursion
    err = float(np.max(np.abs(y_conv - y_sos)))
    tt = np.arange(n) / FS
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].plot(tt[:500], h[:500], color=C_ALT); ax[0].set_title("Impulse response h[n] of final filter")
    ax[0].set_xlabel("Time (s)"); ax[0].set_ylabel("h[n]")
    ax[1].plot(tt, y_sos, color=C_FILT, lw=1.4, label="sosfilt (difference equation)")
    ax[1].plot(tt, y_conv, color="k", lw=0.7, ls="--", label="np.convolve(x, h)")
    ax[1].set_xlim(2, 6); ax[1].set_xlabel("Time (s)"); ax[1].legend(fontsize=8)
    ax[1].set_title(f"y = x * h   (max difference {err:.1e})")
    plt.tight_layout(); savefig("fig5_convolution_check.png")
    return err


def fig_filtered(t, clean, noisy, y_zero, y_causal):
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    lim = (2, 6)
    ax[0].plot(t, noisy, color=C_NOISY); ax[0].set_title("Noisy ECG (input)")
    ax[1].plot(t, clean, color=C_CLEAN, lw=1.2, label="clean reference")
    ax[1].plot(t, y_zero, color=C_FILT, lw=1.0, label="zero-phase (filtfilt)")
    ax[1].set_title("Filtered output - zero-phase"); ax[1].legend(fontsize=8, loc="upper right")
    ax[2].plot(t, clean, color=C_CLEAN, lw=1.2, label="clean reference")
    ax[2].plot(t, y_causal, color=C_ALT, lw=1.0, label="causal (sosfilt)")
    ax[2].set_title("Filtered output - causal (note the delay)"); ax[2].legend(fontsize=8, loc="upper right")
    ax[2].set_xlabel("Time (s)")
    for a in ax: a.set_xlim(*lim); a.set_ylabel("mV")
    plt.tight_layout(); savefig("fig6_filtered_time.png")


def fig_spectrum_filtered(noisy, y_zero):
    f, Xn = spectrum(noisy[TRIM:-TRIM], FS)
    _, Xy = spectrum(y_zero[TRIM:-TRIM], FS)
    plt.figure(figsize=(9, 4))
    plt.semilogy(f, Xn, color=C_NOISY, label="Before filtering")
    plt.semilogy(f, Xy, color=C_FILT, label="After filtering")
    plt.xlim(0, 100); plt.ylim(1e-6, 3)
    plt.xlabel("Frequency (Hz)"); plt.ylabel("Amplitude (mV)")
    plt.title("Spectrum before and after filtering")
    plt.legend(); plt.tight_layout(); savefig("fig7_spectrum_filtered.png")


def fig_order_comparison(results):
    orders = [r["order"] for r in results]
    plt.figure(figsize=(7, 4))
    plt.bar([str(o) for o in orders], [r["snr_db"] for r in results], color=C_ALT)
    plt.axhline(results[0]["snr_input"], color="gray", ls="--", label="noisy input SNR")
    for i, r in enumerate(results):
        plt.text(i, r["snr_db"] + 0.3, f"{r['snr_db']:.1f}", ha="center")
    plt.xlabel("Butterworth order (per band edge), with 50 Hz notch")
    plt.ylabel("Output SNR (dB)"); plt.legend()
    plt.title("Effect of filter order on output SNR")
    plt.tight_layout(); savefig("fig8_order_vs_snr.png")


# --------------------------------------------------------------------------
# 5. Main
# --------------------------------------------------------------------------
def main():
    rng = np.random.default_rng(SEED)
    t, clean = synthetic_ecg(FS, DURATION, HEART_RATE, rng)
    noisy, baseline, mains, white = add_noise(t, clean, rng)

    sos_bp = design_bandpass()
    sos_notch = design_notch()
    sos_final = cascade(sos_bp, sos_notch)

    # Zero-phase (offline) and causal (real-time) outputs
    y_zero = signal.sosfiltfilt(sos_final, noisy)
    y_causal = signal.sosfilt(sos_final, noisy)

    # Group delay of causal filter in the ECG band (5-15 Hz around QRS)
    w, gd = signal.group_delay(signal.sos2tf(sos_final), w=np.linspace(5, 15, 50), fs=FS)
    mean_delay_ms = float(np.mean(gd) / FS * 1000)

    # Compare configurations
    configs = {
        "Band-pass only": signal.sosfiltfilt(sos_bp, noisy),
        "Notch only": signal.sosfiltfilt(sos_notch, noisy),
        "Band-pass + notch (final)": y_zero,
    }
    config_results = {k: {"snr_db": float(snr_db(clean, v)), "rmse_mV": rmse(clean, v)}
                      for k, v in configs.items()}

    # Order sweep (with notch)
    order_results = []
    for n in [2, 4, 6, 8]:
        s = cascade(design_bandpass(order=n), sos_notch)
        y = signal.sosfiltfilt(s, noisy)
        order_results.append({"order": n, "snr_input": float(snr_db(clean, noisy)),
                              "snr_db": float(snr_db(clean, y)), "rmse_mV": rmse(clean, y)})

    # Figures
    fig_noisy_vs_clean(t, clean, noisy, baseline, mains, white)
    fig_spectrum_noisy(noisy, clean)
    fig_frequency_response(sos_final)
    max_pole = fig_pole_zero(sos_bp, sos_notch)
    conv_err = fig_convolution(sos_final, noisy)
    fig_filtered(t, clean, noisy, y_zero, y_causal)
    fig_spectrum_filtered(noisy, y_zero)
    fig_order_comparison(order_results)

    # Attenuation at key frequencies
    def gain_db(f):
        _, h = signal.sosfreqz(sos_final, worN=[f], fs=FS)
        return float(20 * np.log10(np.abs(h[0]) + 1e-12))

    metrics = {
        "fs_Hz": FS, "duration_s": DURATION, "heart_rate_bpm": HEART_RATE,
        "snr_input_dB": float(snr_db(clean, noisy)),
        "snr_output_zero_phase_dB": float(snr_db(clean, y_zero)),
        "rmse_input_mV": rmse(clean, noisy),
        "rmse_output_mV": rmse(clean, y_zero),
        "max_pole_magnitude": max_pole,
        "stable": bool(max_pole < 1),
        "convolution_max_error": conv_err,
        "mean_group_delay_5_15Hz_ms": mean_delay_ms,
        "gain_dB": {"0.3Hz": gain_db(0.3), "1Hz": gain_db(1.0), "10Hz": gain_db(10.0),
                    "40Hz": gain_db(40.0), "50Hz": gain_db(50.0), "100Hz": gain_db(100.0)},
        "configurations": config_results,
        "order_sweep": order_results,
    }
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)

    print("\n=== Results ===")
    print(f"Input SNR            : {metrics['snr_input_dB']:.2f} dB")
    print(f"Output SNR (final)   : {metrics['snr_output_zero_phase_dB']:.2f} dB")
    print(f"Max pole magnitude   : {max_pole:.4f}  (stable: {metrics['stable']})")
    print(f"Convolution check    : max |error| = {conv_err:.2e}")
    print(f"Group delay (5-15 Hz): {mean_delay_ms:.1f} ms")
    for k, v in config_results.items():
        print(f"{k:28s}: SNR {v['snr_db']:.2f} dB, RMSE {v['rmse_mV']:.4f} mV")


if __name__ == "__main__":
    main()
