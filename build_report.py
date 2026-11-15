"""
Builds the technical report PDF from the simulation results.

1. Run   python src/ecg_filter_simulation.py   first (creates results/).
2. Edit the STUDENT DETAILS block below.
3. Run   python report/build_report.py
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle,
                                Preformatted)

# ============================ STUDENT DETAILS ==============================
STUDENT_NAME = "Ayush Singh"
ROLL_NO = "202410101150252"
COURSE = "Signals & Systems"
INSTITUTION = "Shri Ram Swaroop Memorial University"
GITHUB_URL = "https://github.com/Ayush4444-creator/ecg-filter-simulation"
# ===========================================================================

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
OUT = os.path.join(HERE, "Signals_Systems_ECG_Filter_Report.pdf")

with open(os.path.join(RES, "metrics.json")) as fh:
    M = json.load(fh)

# ---- fonts (DejaVu gives Greek letters; fall back to Helvetica) ----------
FONT, FONT_B, FONT_I = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
UNICODE_OK = False
for d in ["/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts", "/Library/Fonts"]:
    reg, bold, ita = (os.path.join(d, f) for f in
                      ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"])
    if all(os.path.exists(p) for p in (reg, bold, ita)):
        pdfmetrics.registerFont(TTFont("DV", reg))
        pdfmetrics.registerFont(TTFont("DV-B", bold))
        pdfmetrics.registerFont(TTFont("DV-I", ita))
        FONT, FONT_B, FONT_I, UNICODE_OK = "DV", "DV-B", "DV-I", True
        break

ASCII_MAP = {"ω": "w", "π": "pi", "≈": "~", "·": "*", "−": "-", "×": "x",
             "τ": "tau", "Ω": "Ohm", "≤": "<=", "≥": ">=", "→": "->", "Δ": "d"}


def T(s):
    if UNICODE_OK:
        return s
    for k, v in ASCII_MAP.items():
        s = s.replace(k, v)
    return s


# ---- styles ----------------------------------------------------------------
ss = getSampleStyleSheet()
BODY = ParagraphStyle("Body", parent=ss["Normal"], fontName=FONT, fontSize=10,
                      leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6)
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName=FONT_B, fontSize=14,
                    spaceBefore=14, spaceAfter=6, keepWithNext=1, textColor=colors.HexColor("#1f3a5f"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName=FONT_B, fontSize=11,
                    spaceBefore=8, spaceAfter=4, keepWithNext=1, textColor=colors.HexColor("#1f3a5f"))
CAP = ParagraphStyle("Cap", parent=BODY, fontName=FONT_I, fontSize=8.5, leading=11,
                     alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=10)
EQ = ParagraphStyle("Eq", parent=BODY, fontName=FONT_I, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8)
TITLE = ParagraphStyle("Title", parent=ss["Title"], fontName=FONT_B, fontSize=22, leading=27,
                       textColor=colors.HexColor("#1f3a5f"))
SUB = ParagraphStyle("Sub", parent=BODY, alignment=TA_CENTER, fontSize=11.5, leading=16)
CODE = ParagraphStyle("Code", fontName="Courier", fontSize=7.8, leading=9.8,
                      backColor=colors.HexColor("#f4f4f4"), borderPadding=5)


def P(text, style=BODY):
    return Paragraph(T(text), style)


def fig(name, caption, width=15.5):
    path = os.path.join(RES, name)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    img = Image(path, width=width * cm, height=width * cm * h / w)
    return KeepTogether([img, P(caption, CAP)])


def table(data, widths, header=True):
    data = [[Paragraph(T(str(c)), ParagraphStyle("c", parent=BODY, alignment=0, fontSize=9,
                                                   leading=12, spaceAfter=0,
                                                   fontName=FONT_B if (header and i == 0) else FONT))
             for c in row] for i, row in enumerate(data)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f2")))
    t.setStyle(TableStyle(st))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, T(f"{COURSE} - Innovative Assessment | {STUDENT_NAME}"))
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


# ---- numbers used in the text ------------------------------------------------
snr_in = M["snr_input_dB"]
snr_out = M["snr_output_zero_phase_dB"]
gain = M["gain_dB"]
cfg = M["configurations"]
orders = {r["order"]: r for r in M["order_sweep"]}

story = []

# =============================== Title block ==================================
story += [Spacer(1, 3 * cm),
          P("Removal of Baseline Wander and Power-Line Interference from an ECG Signal "
            "using Butterworth and Notch Filters", TITLE),
          Spacer(1, 0.6 * cm),
          P("A Python Simulation of LTI Filtering", SUB),
          Spacer(1, 1.2 * cm),
          P(f"<b>{COURSE}</b> - Innovative Assessment", SUB),
          P(f"{STUDENT_NAME} | {ROLL_NO}", SUB),
          P(INSTITUTION, SUB),
          Spacer(1, 0.8 * cm),
          P(f"Source code: {GITHUB_URL}", SUB),
          Spacer(1, 1.6 * cm)]

story += [P("Abstract", H1),
          P(f"This report simulates the cleaning of a noisy electrocardiogram (ECG) using "
            f"linear time-invariant (LTI) digital filters. A synthetic ECG sampled at "
            f"{M['fs_Hz']:.0f} Hz is corrupted by baseline wander (0.3 Hz), 50 Hz mains "
            f"interference and white Gaussian noise. A Butterworth band-pass filter "
            f"(0.5-40 Hz) cascaded with a 50 Hz IIR notch filter is designed and analysed in the "
            f"time, frequency and z-domains. The simulation demonstrates sampling, the Fourier "
            f"transform, impulse response and convolution, frequency response, pole-zero "
            f"stability and group delay. The final filter raises the signal-to-noise ratio from "
            f"{snr_in:.1f} dB to {snr_out:.1f} dB (an improvement of {snr_out - snr_in:.1f} dB), "
            f"all poles lie inside the unit circle, and the convolution sum reproduces the filter "
            f"output to within {M['convolution_max_error']:.0e}.")]
story.append(PageBreak())

# =============================== 1 Introduction ==================================
story += [P("1. Introduction", H1),
          P("Biomedical signals are small in amplitude and easily contaminated. An ECG has a "
            "useful bandwidth of roughly 0.5-40 Hz, but real recordings also contain slow "
            "baseline drift caused by breathing and electrode movement, narrow-band interference "
            "at the mains frequency (50 Hz in India), and broadband electrode or muscle noise. "
            "Because the unwanted components occupy different frequency ranges from the wanted "
            "signal, they can be separated by frequency-selective LTI systems, that is, filters."),
          P("<b>Objective.</b> Simulate an ECG, add realistic noise, design a filter in Python, "
            "and verify its behaviour using the main tools of Signals and Systems."),
          P("<b>Syllabus topics covered:</b> sampling; LTI systems; impulse response and "
            "convolution; Fourier transform and spectra; frequency response and Bode plots; "
            "poles, zeros and stability; phase and group delay.")]

# =============================== 2 Theory ==================================
story += [P("2. Theory", H1),
          P("2.1 Sampling", H2),
          P("A continuous-time signal x(t) is sampled at f<sub>s</sub> = 1/T<sub>s</sub> to give "
            "x[n] = x(nT<sub>s</sub>). To avoid aliasing, f<sub>s</sub> must exceed twice the highest "
            "frequency present (Nyquist criterion). Here f<sub>s</sub> = 500 Hz, so the Nyquist "
            "frequency is 250 Hz, well above the 50 Hz interference and the 40 Hz band edge."),
          P("2.2 LTI systems, impulse response and convolution", H2),
          P("A discrete LTI system is completely described by its impulse response h[n]. The "
            "output for any input is the convolution sum:"),
          P("y[n] = x[n] * h[n] = Σ<sub>k</sub> h[k] · x[n − k]", EQ),
          P("An IIR filter realises the same system through a difference equation "
            "y[n] = Σ b<sub>k</sub> x[n−k] − Σ a<sub>k</sub> y[n−k], which is far cheaper than "
            "convolving with a long h[n]. Section 4.4 verifies that both give identical results."),
          P("2.3 Frequency response and the Fourier transform", H2),
          P("The frequency response H(e<super>jω</super>) is the discrete-time Fourier transform of "
            "h[n]. Its magnitude gives the gain at each frequency and its phase gives the "
            "delay. For a sampled signal, the FFT estimates the spectrum X(e<super>jω</super>); a Hann "
            "window is applied to reduce spectral leakage."),
          P("2.4 Butterworth filter", H2),
          P("A Butterworth low-pass filter of order N has a maximally flat passband:"),
          P("|H(jΩ)|<super>2</super> = 1 / (1 + (Ω/Ω<sub>c</sub>)<super>2N</super>)", EQ),
          P("The gain is −3 dB at the cutoff Ω<sub>c</sub>, and the roll-off steepens by "
            "20N dB per decade as N increases. The digital filter is obtained with the bilinear "
            "transform. A band-pass response combines a high-pass edge (0.5 Hz) and a low-pass "
            "edge (40 Hz); in SciPy, butter(N, [f1, f2], 'bandpass') returns a filter "
            "with 2N poles in total."),
          P("2.5 Notch filter", H2),
          P("A second-order IIR notch places a pair of zeros on the unit circle at the "
            "interference frequency and a pair of poles just inside it:"),
          P("H(z) = (1 − 2cos ω<sub>0</sub> z<super>−1</super> + z<super>−2</super>) / "
            "(1 − 2r cos ω<sub>0</sub> z<super>−1</super> + r<super>2</super> z<super>−2</super>),   "
            "ω<sub>0</sub> = 2π f<sub>0</sub>/f<sub>s</sub>", EQ),
          P("The zeros give a null exactly at f<sub>0</sub> = 50 Hz, while the nearby poles keep the "
            "rest of the spectrum almost untouched. The quality factor Q = f<sub>0</sub>/bandwidth "
            "controls the notch width (Q = 30 here)."),
          P("2.6 Stability and group delay", H2),
          P("A causal discrete-time LTI system is BIBO stable if and only if all poles lie strictly "
            "inside the unit circle |z| = 1. Group delay τ<sub>g</sub>(ω) = −dφ/dω measures how long "
            "each frequency component is delayed. A causal IIR filter has non-zero group delay, "
            "whereas forward-backward (zero-phase) filtering cancels the phase at the cost of "
            "needing the whole record in advance.")]

# =============================== 3 Methodology ==================================
story += [P("3. Methodology", H1),
          P("The simulation is written in Python using NumPy, SciPy and Matplotlib. The steps are:"),
          P("1. <b>Signal model.</b> Each heartbeat is the sum of five Gaussian pulses (P, Q, R, S "
            "and T waves). Beats occur at 72 bpm with small random timing variation."),
          P("2. <b>Noise model.</b> Baseline wander = 0.50 sin(2π·0.30t) + 0.15 sin(2π·0.15t + 1); "
            "mains interference = 0.25 sin(2π·50t); white Gaussian noise with σ = 0.05 mV."),
          P("3. <b>Filter design.</b> Butterworth band-pass 0.5-40 Hz, order 4 per band edge, "
            "implemented as second-order sections (SOS) for numerical stability, cascaded with a "
            "50 Hz IIR notch (Q = 30)."),
          P("4. <b>Analysis.</b> Spectra by FFT, frequency response by <font face='Courier'>sosfreqz</font>, "
            "pole-zero plot by <font face='Courier'>sos2zpk</font>, impulse response and convolution "
            "check, causal filtering by <font face='Courier'>sosfilt</font> and zero-phase filtering by "
            "<font face='Courier'>sosfiltfilt</font>."),
          P("5. <b>Evaluation.</b> SNR = 10 log<sub>10</sub>(Σc² / Σ(y − c)²) where c is the clean ECG "
            "and y the test signal. The first and last second are excluded to ignore start-up "
            "transients."),
          Spacer(1, 4),
          table([["Parameter", "Value"],
                 ["Sampling frequency", f"{M['fs_Hz']:.0f} Hz"],
                 ["Duration", f"{M['duration_s']:.0f} s ({int(M['fs_Hz'] * M['duration_s'])} samples)"],
                 ["Heart rate", f"{M['heart_rate_bpm']} bpm"],
                 ["Band-pass edges / order", "0.5 Hz and 40 Hz / 4 per edge"],
                 ["Notch", "50 Hz, Q = 30"],
                 ["Noise", "0.3 Hz + 0.15 Hz drift, 50 Hz hum (0.25 mV), white σ = 0.05 mV"]],
                [5.5, 10.5])]

# =============================== 4 Results ==================================
story += [P("4. Results", H1),
          P("4.1 Signal and noise", H2),
          P("Figure 1 shows the clean ECG, each noise component and the corrupted signal. The "
            "PQRST morphology is almost invisible in the noisy trace, and the input SNR is "
            f"only {snr_in:.1f} dB."),
          fig("fig1_signal_and_noise.png", "Figure 1: Clean ECG, noise components and the noisy signal.", 15),
          P("4.2 Spectrum of the noisy signal", H2),
          P("The spectrum in Figure 2 makes the noise easy to locate: baseline wander sits below "
            "0.5 Hz and the mains hum appears as a sharp line at 50 Hz, both outside the main "
            "ECG energy at 1-30 Hz. This frequency separation is what makes filtering possible."),
          fig("fig2_spectrum_noisy.png", "Figure 2: Amplitude spectrum of noisy and clean ECG.", 14.5),
          P("4.3 Frequency response and pole-zero plot", H2),
          P("Figure 3 compares band-pass filters of order 2, 4, 6 and 8 and the final design. "
            f"The final filter has a gain of {gain['1Hz']:.2f} dB at 1 Hz and {gain['10Hz']:.2f} dB at "
            f"10 Hz (flat passband), {gain['0.3Hz']:.1f} dB at 0.3 Hz (baseline wander suppressed), "
            f"{gain['40Hz']:.1f} dB at 40 Hz (the cutoff) and {gain['100Hz']:.1f} dB at 100 Hz. At 50 Hz "
            "the notch gives an essentially exact null (below −100 dB in exact arithmetic, "
            "limited only by floating-point precision)."),
          fig("fig3_frequency_response.png", "Figure 3: Bode plot - magnitude for several orders, phase of the final filter.", 14.5),
          P(f"The pole-zero plot (Figure 4) shows that all poles lie inside the unit circle. The "
            f"largest pole magnitude is {M['max_pole_magnitude']:.4f}, so the system is stable. "
            "The poles near z = 1 are responsible for the very low 0.5 Hz edge, and the notch zeros "
            "sit exactly on the unit circle at ±50 Hz."),
          fig("fig4_pole_zero.png", "Figure 4: Pole-zero plots in the z-plane (poles = x, zeros = o).", 15.5),
          P("4.4 Impulse response and convolution", H2),
          P("The impulse response h[n] was obtained by feeding a unit impulse through the filter. "
            "Convolving the noisy ECG with h[n] using <font face='Courier'>np.convolve</font> gives the same "
            f"output as the difference-equation implementation, with a maximum difference of "
            f"{M['convolution_max_error']:.1e}. This confirms that the filter is a true LTI "
            "system whose output is fully determined by h[n]."),
          fig("fig5_convolution_check.png", "Figure 5: Impulse response and the convolution check.", 15.5),
          P("4.5 Filtered output", H2),
          P("Figure 6 shows the result for the middle 4 seconds. After zero-phase filtering the "
            "P, QRS and T waves are clearly restored and the 50 Hz ripple and baseline drift are "
            "gone. The causal filter produces the same shape, but delayed: the mean group delay in "
            f"the 5-15 Hz range (where the QRS energy lies) is {M['mean_group_delay_5_15Hz_ms']:.1f} ms. "
            "Figure 7 confirms in the frequency domain that the 50 Hz line and the low-frequency "
            "drift have been removed."),
          fig("fig6_filtered_time.png", "Figure 6: Noisy input, zero-phase output and causal output compared with the clean reference.", 15),
          fig("fig7_spectrum_filtered.png", "Figure 7: Spectrum before and after filtering.", 14.5),
          P("4.6 Quantitative comparison", H2),
          KeepTogether([table([["Configuration", "SNR (dB)", "RMSE (mV)"],
                 ["Noisy input (no filter)", f"{snr_in:.2f}", f"{M['rmse_input_mV']:.4f}"]] +
                [[k, f"{v['snr_db']:.2f}", f"{v['rmse_mV']:.4f}"] for k, v in cfg.items()],
                [7.5, 4, 4]),
          Spacer(1, 6),
          P("Table 1: Performance of different filter configurations (zero-phase filtering).", CAP)]),
          P("The notch filter alone does not help much because the large baseline wander "
            "remains, and the band-pass alone leaves a small residual at 50 Hz. The cascade is "
            "best, as each stage removes a different disturbance."),
          KeepTogether([table([["Order (per edge)", "SNR (dB)", "RMSE (mV)"]] +
                [[str(n), f"{r['snr_db']:.2f}", f"{r['rmse_mV']:.4f}"] for n, r in orders.items()],
                [5.5, 5, 5]),
          Spacer(1, 6),
          P("Table 2: Effect of Butterworth order (all with the 50 Hz notch).", CAP)]),
          fig("fig8_order_vs_snr.png", "Figure 8: Output SNR for different filter orders.", 11)]

# =============================== 5 Discussion ==================================
best_order = max(orders, key=lambda k: orders[k]["snr_db"])
story += [P("5. Discussion", H1),
          P(f"<b>Overall performance.</b> The final filter improves the SNR by "
            f"{snr_out - snr_in:.1f} dB. The remaining error has two main sources. First, a 0.5 Hz "
            "high-pass edge removes the DC level of the reference ECG (its P and T waves give it "
            "a small positive mean), so the filtered baseline sits slightly lower than the clean "
            "reference. Second, white noise inside the 0.5-40 Hz passband cannot be removed by a "
            "frequency-selective filter."),
          P(f"<b>Effect of order.</b> Increasing the order sharpens the roll-off (Figure 3) but does "
            f"not increase the SNR monotonically (best at order {best_order} in this run). Higher orders "
            "cut more of the ECG's own low- and high-frequency content and ring more around the sharp QRS "
            "complex, which can offset the benefit of steeper attenuation. The differences above "
            "order 4 are small (a few tenths of a dB) and depend on the particular noise realisation, "
            "so order 4 is a good compromise between selectivity and waveform distortion."),
          P("<b>Causal versus zero-phase.</b> Zero-phase filtering gives the best waveform "
            "fidelity but requires the whole recording, so it suits offline analysis. A real-time "
            "monitor must use the causal filter and accept the group delay of about "
            f"{M['mean_group_delay_5_15Hz_ms']:.0f} ms, which is acceptable for display but "
            "relevant when timing against other signals."),
          P("<b>Limitations.</b> The ECG is synthetic and the noise is stationary; real signals "
            "have varying noise levels, and the mains frequency can drift slightly. Adaptive "
            "filters would handle such cases better. The SNR is also computed against a known "
            "clean reference, which is not available for real recordings.")]

# =============================== 6 Conclusion ==================================
story += [P("6. Conclusion", H1),
          P(f"A cascade of a Butterworth band-pass filter and a 50 Hz notch filter removes "
            f"baseline wander and mains interference from a noisy ECG, improving SNR from "
            f"{snr_in:.1f} dB to {snr_out:.1f} dB. The simulation demonstrates how the core ideas of "
            "Signals and Systems, namely sampling, convolution, frequency response, "
            "pole-zero stability and group delay, combine in a practical biomedical application. "
            "Possible extensions include testing real ECG records (e.g. the MIT-BIH database), "
            "comparing Chebyshev and elliptic designs, and implementing an adaptive notch.")]

# =============================== 7 References ==================================
story += [P("References", H1),
          P("[1] A. V. Oppenheim, A. S. Willsky and S. H. Nawab, <i>Signals and Systems</i>, 2nd ed., "
            "Prentice Hall, 1997."),
          P("[2] A. V. Oppenheim and R. W. Schafer, <i>Discrete-Time Signal Processing</i>, 3rd ed., "
            "Pearson, 2010."),
          P("[3] S. Butterworth, \"On the theory of filter amplifiers,\" <i>Experimental Wireless and "
            "the Wireless Engineer</i>, vol. 7, pp. 536-541, 1930."),
          P("[4] P. Virtanen et al., \"SciPy 1.0: fundamental algorithms for scientific computing "
            "in Python,\" <i>Nature Methods</i>, vol. 17, pp. 261-272, 2020."),
          P("[5] C. R. Harris et al., \"Array programming with NumPy,\" <i>Nature</i>, vol. 585, "
            "pp. 357-362, 2020."),
          P("[6] J. D. Hunter, \"Matplotlib: a 2D graphics environment,\" <i>Computing in Science "
            "&amp; Engineering</i>, vol. 9, no. 3, pp. 90-95, 2007."),
          P("[7] G. B. Moody and R. G. Mark, \"The impact of the MIT-BIH Arrhythmia Database,\" "
            "<i>IEEE Eng. in Medicine and Biology</i>, vol. 20, no. 3, pp. 45-50, 2001.")]

# =============================== Appendix ==================================
story += [PageBreak(), P("Appendix A: Core filter code", H1),
          P(f"The complete code is available at {GITHUB_URL}. The key design lines are:"),
          Preformatted(
              "from scipy import signal\n\n"
              "FS = 500.0\n"
              "sos_bp    = signal.butter(4, [0.5, 40.0], btype='bandpass', fs=FS, output='sos')\n"
              "b, a      = signal.iirnotch(50.0, 30.0, fs=FS)\n"
              "sos_notch = signal.tf2sos(b, a)\n"
              "sos_final = np.vstack([sos_bp, sos_notch])      # cascade\n\n"
              "y_zero   = signal.sosfiltfilt(sos_final, noisy)  # zero-phase (offline)\n"
              "y_causal = signal.sosfilt(sos_final, noisy)      # causal (real-time)\n\n"
              "# impulse response and convolution check\n"
              "impulse = np.zeros(len(noisy)); impulse[0] = 1\n"
              "h = signal.sosfilt(sos_final, impulse)\n"
              "y_conv = np.convolve(noisy, h)[:len(noisy)]", CODE)]

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=2 * cm, bottomMargin=2 * cm,
                        title="ECG Noise Removal using Butterworth Filters",
                        author=STUDENT_NAME)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("Report written to", OUT)
