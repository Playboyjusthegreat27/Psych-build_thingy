#!/usr/bin/env python3
import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: port_freestyle.py PSYCH_SOURCE FREESTYLE_HTML")

psych = Path(sys.argv[1]).resolve()
freestyle = Path(sys.argv[2]).resolve()

# Freestyle story order and the closest matching original FNF stages.
weeks = [
    {
        "id": "freestyle1", "name": "Freestyle Week 1", "story": "Freestyle: Week 1",
        "stage": "stage", "opponent": "dad", "gf": "gf",
        "songs": ["doobop", "refreshed", "spooky-fight"],
    },
    {
        "id": "freestyle2", "name": "Freestyle Week 2", "story": "Freestyle: Week 2",
        "stage": "halloween", "opponent": "spooky", "gf": "gf",
        "songs": ["creepz", "north", "night-lights"],
    },
    {
        "id": "freestyle3", "name": "Freestyle Week 3", "story": "Freestyle: Week 3",
        "stage": "philly", "opponent": "pico", "gf": "gf",
        "songs": ["gunfight", "funky-nice", "turf-war"],
    },
    {
        "id": "freestyle4", "name": "Freestyle Week 4", "story": "Freestyle: Week 4",
        "stage": "limo", "opponent": "mom-car", "gf": "gf-car",
        "songs": ["ecstacy", "cruise-control", "joyride"],
    },
    {
        "id": "freestyle5", "name": "Freestyle Week 5", "story": "Freestyle: Week 5",
        "stage": "mall", "opponent": "parents-christmas", "gf": "gf-christmas",
        "songs": ["slurry", "flurry", "snowblind"],
    },
    {
        "id": "freestyle6", "name": "Freestyle Week 6", "story": "Freestyle: Week 6",
        "stage": "school", "opponent": "senpai", "gf": "gf-pixel",
        "songs": ["social-suicide", "recess", "splinters"],
    },
]

colors = {
    "dad": [146, 113, 253], "spooky": [165, 0, 77], "pico": [255, 150, 0],
    "mom": [215, 0, 0], "mom-car": [215, 0, 0],
    "parents-christmas": [180, 0, 0], "senpai": [255, 170, 210],
    "senpai-angry": [255, 100, 160], "spirit": [255, 255, 255],
}

data_dir = psych / "assets" / "shared" / "data"
songs_dir = psych / "assets" / "songs"
weeks_dir = psych / "assets" / "shared" / "weeks"
data_dir.mkdir(parents=True, exist_ok=True)
songs_dir.mkdir(parents=True, exist_ok=True)
weeks_dir.mkdir(parents=True, exist_ok=True)

all_slugs = []
for week in weeks:
    week_songs = []
    for slug in week["songs"]:
        source_chart_dir = freestyle / "assets" / "data" / slug
        target_chart_dir = data_dir / slug
        if not source_chart_dir.is_dir():
            raise SystemExit(f"Missing chart folder: {source_chart_dir}")
        target_chart_dir.mkdir(parents=True, exist_ok=True)

        normal_chart = source_chart_dir / f"{slug}.json"
        if not normal_chart.is_file():
            raise SystemExit(f"Missing normal chart: {normal_chart}")

        opponent = week["opponent"]
        for chart_file in sorted(source_chart_dir.glob("*.json")):
            chart = json.loads(chart_file.read_text(encoding="utf-8"))
            song = chart.get("song", chart)
            song.setdefault("player1", "bf")
            song.setdefault("player2", opponent)
            song.setdefault("gfVersion", week["gf"])
            song.setdefault("stage", week["stage"])
            song.setdefault("needsVoices", True)
            song.setdefault("validScore", True)
            song["stage"] = week["stage"]
            # Keep the chart's own opponent where it specifies one.
            opponent = song.get("player2", opponent)
            chart["song"] = song
            (target_chart_dir / chart_file.name).write_text(
                json.dumps(chart, separators=(",", ":")) + "\n", encoding="utf-8"
            )

        source_audio_dir = freestyle / "assets" / "songs" / slug
        target_audio_dir = songs_dir / slug
        target_audio_dir.mkdir(parents=True, exist_ok=True)
        for stem in ("Inst", "Voices"):
            source_audio = source_audio_dir / f"{stem}.ogg"
            if not source_audio.is_file():
                if stem == "Voices":
                    continue
                raise SystemExit(f"Missing instrumental: {source_audio}")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(source_audio), "-vn", "-codec:a",
                 "libmp3lame", "-q:a", "2", str(target_audio_dir / f"{stem}.mp3")],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

        normal = json.loads(normal_chart.read_text(encoding="utf-8")).get("song", {})
        song_opponent = normal.get("player2", week["opponent"])
        week_songs.append([
            slug.replace("-", " ").title(),
            song_opponent,
            colors.get(song_opponent, colors.get(week["opponent"], [146, 113, 253]))
        ])
        all_slugs.append(slug)

    week_json = {
        "songs": week_songs,
        "weekCharacters": [week["opponent"], "bf", week["gf"]],
        "weekBackground": week["stage"],
        "storyName": week["story"],
        "weekBefore": "week7" if week["id"] == "freestyle1" else weeks[weeks.index(week) - 1]["id"],
        "weekName": week["name"],
        "startUnlocked": True,
        "hideStoryMode": False,
        "hideFreeplay": False,
    }
    (weeks_dir / f'{week["id"]}.json').write_text(
        json.dumps(week_json, indent=2) + "\n", encoding="utf-8"
    )

week_list = weeks_dir / "weekList.txt"
existing = week_list.read_text(encoding="utf-8").splitlines() if week_list.exists() else []
for week in weeks:
    if week["id"] not in existing:
        existing.append(week["id"])
week_list.write_text("\n".join(existing) + "\n", encoding="utf-8")

print(f"Ported {len(set(all_slugs))} songs across {len(weeks)} story weeks.")
