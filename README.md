# ECG Noise Removal using Butterworth and Notch Filters

**Signals & Systems - Innovative Assessment**
Python simulation of LTI filtering: removing baseline wander and 50 Hz mains
interference from a noisy synthetic ECG.

## What this project does

1. Generates a synthetic ECG (P, Q, R, S, T waves, 72 bpm, fs = 500 Hz).
2. Corrupts it with baseline wander (0.3 Hz), 50 Hz mains hum and white noise.
3. Designs a **Butterworth band-pass (0.5-40 Hz)** and a **50 Hz IIR notch**, then cascades them.
4. Analyses the system in the time, frequency and z-domains.
5. Writes all figures and a `metrics.json` file to `results/`.

### Syllabus topics demonstrated

| Topic | Where |
|---|---|
| Sampling and Nyquist | signal generation, fs = 500 Hz |
| LTI systems, impulse response, convolution | `fig5_convolution_check.png` |
| Fourier transform / spectrum | `fig2`, `fig7` |
| Frequency response, Bode plot | `fig3_frequency_response.png` |
| Poles, zeros, stability | `fig4_pole_zero.png` |
| Group delay, causal vs zero-phase | `fig6_filtered_time.png` |

## Results (seed = 42)

| Metric | Value |
|---|---|
| Input SNR | -6.63 dB |
| Output SNR (band-pass + notch) | 7.94 dB |
| SNR improvement | 14.6 dB |
| Max pole magnitude | 0.9976 (stable) |
| Convolution vs difference equation | max error 9.8e-13 |
| Mean group delay, 5-15 Hz | 13.5 ms |

## Folder structure

```
ecg-filter-simulation/
├── src/
│   └── ecg_filter_simulation.py   # main simulation
├── report/
│   ├── build_report.py            # builds the PDF report
│   └── Signals_Systems_ECG_Filter_Report.pdf
├── results/                       # figures + metrics.json
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python src/ecg_filter_simulation.py     # creates results/*.png and metrics.json
python report/build_report.py           # rebuilds the PDF report
```

Before rebuilding the report, edit the student details at the top of
`report/build_report.py` (name, roll number, institution, GitHub link).

## Technologies

Python 3, NumPy, SciPy (`signal`), Matplotlib, ReportLab.

## References

- Oppenheim, Willsky, Nawab - *Signals and Systems*
- Oppenheim, Schafer - *Discrete-Time Signal Processing*
- SciPy `scipy.signal` documentation
