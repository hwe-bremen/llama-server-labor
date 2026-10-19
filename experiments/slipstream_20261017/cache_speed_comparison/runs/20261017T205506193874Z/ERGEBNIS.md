# PGRN-Cache2GiB gegen12GiB

Nur2frische Prozesse, je3gleiche Anfragen. Erste arena-kalt, danach wärmer. OS-Dateicache unkontrolliert, kein Kaltstartbenchmark.

| Messgröße | A2GiB | B12GiB |
|---|---:|---:|
| load_s | 126.62615320901386 | 126.91716112499125 |
| cache_mib | 2046.030 (2046.030–2046.030) | 12287.160 (12287.160–12287.160) |
| prompt_s | 38.319 (38.075–41.595) | 12.942 (12.914–14.896) |
| prompt_tps | 14.562 (13.415–14.655) | 43.116 (37.459–43.210) |
| ttft_s | 38.327 (38.083–41.604) | 12.950 (12.922–14.904) |
| decode_tps | 3.953 (3.648–4.014) | 12.501 (11.801–12.677) |
| wall_s | 73.168 (70.218–73.987) | 23.162 (23.047–25.751) |
| misses_delta | 80508.000 (80506.000–80808.000) | 12500.000 (12455.000–16241.000) |
| peak_rss_gib | 6.4371185302734375 | 16.437698364257812 |
| swapout_delta | 0 | 0 |

Median (Min–Max), bei Anfragemetriken3Werte; erster/wärmer getrennt in summary.json.
Technisch auswertbar: True
Alle sechs Ausgaben identisch: True
Nur Cache-CLI-Argument verschieden: True
B/A-Raten: {'prompt_s': 0.33774394123919393, 'prompt_tps': 2.9608229131541672, 'ttft_s': 0.33788742716233217, 'decode_tps': 3.162581651633111, 'wall_s': 0.3165561546520893}
Datenträgerzähler sind geräteweit, nicht exklusiv Prozess/Datei. Keine Qualitäts- oder Langkontextaussage.
